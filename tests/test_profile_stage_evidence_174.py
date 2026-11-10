"""Durable tests for Assistant stage evidence report, no service/IO on MAIN."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))


class StageEvidence174(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import profile_raw_archive
        cls.archive = profile_raw_archive

    def test_presence_not_success(self):
        records = [
            {'seq': 1, 'event': 'job.claimed', 'at_utc': '2026-11-10T00:00:00Z', 'duration_us': None},
            {'seq': 2, 'event': 'profile.web_investigation', 'at_utc': '2026-11-10T00:01:00Z', 'duration_us': 20},
            {'seq': 3, 'event': 'profile.verdict_counts', 'at_utc': '2026-11-10T00:01:01Z', 'duration_us': None},
        ]
        idx = self.archive._stage_evidence_index(records, 196, 'a' * 32)
        by = {s['stage']: s for s in idx['stages']}
        self.assertEqual(len(idx['stages']), 8)
        self.assertEqual(by['lab_receipt']['capture']['status'], 'observed')
        self.assertEqual(by['document_crosscheck']['capture']['status'], 'not_observed')
        self.assertEqual(by['reports_publication']['capture']['status'], 'outside_capture_boundary')
        self.assertEqual(by['document_reading']['raw_evidence_references'][0]['seq'], 2)
        for stage in idx['stages']:
            self.assertEqual(stage['interpretation']['status'], 'not_evaluated')
            self.assertNotIn('verdict', stage)

    def test_archive_contains_separate_stage_json_without_losing_raw(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            trace_id = 'b' * 32
            events = [
                {'schema':'ezs.profile-trace.v1', 'seq':i, 'at_utc':'2026-11-10T00:00:00Z',
                 'run_id':196, 'trace_id':trace_id,'event':event,'elapsed_us':i,'duration_us':None,
                 'data':data}
                for i,(event,data) in enumerate([
                    ('trace.begin',{'token':'must-never-leak'}),
                    ('job.claimed',{'job_id':225}),
                    ('lab.submit.response',{'ok':True,'revision':{'id':80}}),
                    ('trace.finish',{'status':'completed'}),
                ],1)
            ]
            file = folder / 'timeline.jsonl'
            file.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')
            class Trace: pass
            trace=Trace()
            trace.run_id=196
            trace.trace_id=trace_id
            trace.folder=folder
            trace.file=file
            _, files, manifest=self.archive.package(trace,{'revision':80})
            contents={k:v for k,v in files}
            index=json.loads(contents['stage-observations.json.part-0000'])
            self.assertEqual(index['run_id'], 196)
            self.assertEqual(index['stages'][6]['raw_evidence_references'][0]['seq'],3)
            self.assertEqual(index['stages'][7]['capture']['status'],'outside_capture_boundary')
            self.assertEqual(manifest['revision_id'],80)
            joined=b''.join(v for name,v in files if name.startswith('timeline-'))
            self.assertIn(b'job.claimed',joined)
            self.assertNotIn(b'must-never-leak',joined)
            self.assertIn(b'[REDACTED:SENSITIVE_FIELD]',joined)

    def test_gap_in_timeline_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            tid='c'*32
            f=folder/'timeline.jsonl'
            f.write_text(json.dumps({'seq':2,'run_id':3,'trace_id':tid})+'\n',encoding='utf-8')
            class T: pass
            t=T();t.run_id=3;t.trace_id=tid;t.folder=folder;t.file=f
            with self.assertRaisesRegex(ValueError,'archive_timeline_sequence_gap'):
                self.archive.package(t,None)

if __name__ == '__main__':
    unittest.main()

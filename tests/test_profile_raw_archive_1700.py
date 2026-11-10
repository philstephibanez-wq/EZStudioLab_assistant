from __future__ import annotations
import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from profile_raw_archive import package, publish, scrub

class ArchiveTests(unittest.TestCase):
    def trace(self, root, count=3):
        f=Path(root)
        trace=type('Trace', (), {})()
        trace.folder=f
        trace.file=f/'timeline.jsonl'
        trace.run_id=196
        trace.trace_id='a'*32
        with trace.file.open('w',encoding='utf-8') as h:
            for i in range(1,count+1):
                h.write(json.dumps({'run_id':196,'trace_id':trace.trace_id,'seq':i,
                                    'event':'test','data':{'value':i,'token':'SENSITIVE',
                                    'evidence_url':'https://example.org/path?auth=secret&x=2'}})+'\n')
        (f/'0001_test.json').write_text(json.dumps({'payload':'é'*160000,'secret':'SENSITIVE'}),encoding='utf-8')
        return trace

    def test_segmented_roundtrip_and_manifest_last(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp, 1000)
            prefix, files, manifest=package(trace, {'revision':77})
            self.assertGreater(len(files), 4)
            self.assertEqual(manifest['timeline_events'],1000)
            for record, (name, raw) in zip(manifest['artifacts'],files):
                self.assertEqual(record['path'],name)
                self.assertEqual(record['sha256'],hashlib.sha256(raw).hexdigest())
                self.assertNotIn(b'"SENSITIVE"',raw)
                self.assertNotIn(b'auth=secret',raw)
            store={}
            writes=[]
            def gh(endpoint,payload=None):
                if payload is None:
                    if endpoint not in store: raise RuntimeError('report_github_http_error:repository_or_path_not_found:exit=1')
                    return {'content':base64.b64encode(store[endpoint]).decode(),'sha':'fake'}
                value=base64.b64decode(payload['content'])
                store[endpoint]=value
                writes.append(endpoint)
                return {'content':payload['content']}
            self.assertEqual(publish(trace,{'revision':77},gh),'raw_published')
            self.assertTrue(writes[-1].endswith('manifest.json'))
            self.assertEqual(publish(trace,{'revision':77},gh),'raw_unchanged')
            self.assertEqual(len(writes),len(files)+1)

    def test_strict_identity_sequence_and_input(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp)
            body=trace.file.read_text(encoding='utf-8').replace('"seq": 2','"seq": 5')
            trace.file.write_text(body,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'sequence_gap'):
                package(trace, {})

    def test_secret_masking_and_evidence_preservation(self):
        x=scrub({'url':'https://musicbrainz.org/recording/abc?token=secret&id=123',
                 'authorization':'Bearer abc','fact':'electric guitar',
                 'path':'C:\\Users\\steph\\Documents\\secret'})
        self.assertEqual(x['fact'],'electric guitar')
        self.assertIn('id=123',x['url'])
        self.assertNotIn('token=secret',x['url'])
        self.assertEqual(x['authorization'],'[REDACTED:SENSITIVE_FIELD]')
        self.assertIn('REDACTED:PERSONAL_PATH',x['path'])

    def test_large_single_event_never_truncated(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp,1)
            record=json.loads(trace.file.read_text().strip())
            record['data']['model_response']='A'*180000
            trace.file.write_text(json.dumps(record)+'\n',encoding='utf-8')
            _,files,manifest=package(trace,{'revision':77})
            timeline=b''.join(content for name,content in files if name.startswith('timeline-'))
            self.assertEqual(json.loads(timeline)['data']['model_response'],'A'*180000)
            self.assertTrue(all(raw.decode('utf-8') is not None for _,raw in files))
            self.assertEqual(manifest['timeline_events'],1)

    def test_preset_evidence_and_source_sets_are_derived_only(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp,2)
            lines=trace.file.read_text().splitlines()
            first=json.loads(lines[0]);first['event']='assistant.preset.loaded'
            first['data']={'preset_id':'research-v2','preset_sha256':'b'*64}
            second=json.loads(lines[1]);second['event']='profile.web_investigation'
            second['data']={'items':[{'key':'instrument:0','documents':[
                {'url':'https://example.org/credits','status':'read','recording_identity_verified':False}]}]}
            trace.file.write_text('\n'.join(json.dumps(x) for x in (first,second))+'\n',encoding='utf-8')
            _,files,manifest=package(trace, {'revision':77})
            self.assertEqual(manifest['assistant_preset_provenance_status'],'attested_by_runtime_event')
            preset=b''.join(raw for name,raw in files if name.startswith('assistant-preset-evidence'))
            sources=b''.join(raw for name,raw in files if name.startswith('source-sets'))
            self.assertEqual(json.loads(preset)['observations'][0]['data']['preset_id'],'research-v2')
            self.assertEqual(json.loads(sources)['items']['instrument:0']['read'],['https://example.org/credits'])
            self.assertEqual(json.loads(sources)['items']['instrument:0']['identity_attested'],[])

    def test_snapshot_roundtrip_preserves_large_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp, 2)
            _,files,manifest=package(trace,{'revision':77})
            parts=[raw for name,raw in files if name.startswith('snapshots/0001_test.json.part-')]
            self.assertGreater(len(parts), 1)
            restored=json.loads(b''.join(parts).decode('utf-8'))
            self.assertEqual(restored['payload'], 'é'*160000)
            self.assertEqual(restored['secret'], '[REDACTED:SENSITIVE_FIELD]')
            self.assertEqual(manifest['snapshot_count'],1)
            self.assertEqual(manifest['artifact_count'],len(files))

    def test_missing_preset_provenance_is_not_invented(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp)
            _,files,manifest=package(trace,{'revision':77})
            preset=b''.join(raw for name,raw in files if name.startswith('assistant-preset-evidence'))
            data=json.loads(preset)
            self.assertEqual(manifest['assistant_preset_provenance_status'],'not_attested')
            self.assertEqual(data['status'],'not_attested')
            self.assertEqual(data['observations'],[])
            source=b''.join(raw for name,raw in files if name.startswith('source-sets'))
            self.assertEqual(json.loads(source)['items'],{})

    def test_conflicting_immutable_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            trace=self.trace(temp)
            seen={}
            def gh(endpoint,payload=None):
                if payload is None:
                    return {'content':base64.b64encode(b'changed').decode()}
                raise AssertionError('must not overwrite')
            with self.assertRaisesRegex(RuntimeError,'immutable_path_conflict'):
                publish(trace,{},gh)

if __name__=='__main__': unittest.main()

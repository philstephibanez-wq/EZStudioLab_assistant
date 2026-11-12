import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app'))
from profile_engine_diagnostic import call_engine, execution_scope, record_items, record_item

class Trace:
    run_id=155
    trace_id='a'*32

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.events = []
        self.snapshots = []
        self.p1 = patch('profile_engine_diagnostic.emit', side_effect=lambda name, data: self.events.append((name,data)))
        self.p2 = patch('profile_engine_diagnostic.snap', side_effect=lambda name, data: self.snapshots.append((name,data)))
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)

    def read(self):
        f=self.folder/'profile'/'run-000155'/('execution-'+'a'*12+'.json')
        return json.loads(f.read_text(encoding='utf-8'))

    def test_success_and_duration(self):
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            self.assertEqual(call_engine('musicbrainz',lambda: {'status':'ok','secret':'NOT_STORED'}),{'status':'ok','secret':'NOT_STORED'})
        v=self.read()
        self.assertEqual(v['steps'][0]['status'],'OK')
        self.assertEqual(v['engine_count'],1)
        self.assertIsInstance(v['steps'][0]['duration_ms'],float)
        self.assertNotIn('NOT_STORED',json.dumps(v))
        self.assertEqual(self.snapshots[0][0],'profile.engine.summary')

    def test_error_is_rethrown_and_sanitized(self):
        with self.assertRaisesRegex(PermissionError,'PRIVATE_VALUE'):
            with execution_scope(155,229,Trace(),receipt_root=self.folder):
                def failing():raise PermissionError('PRIVATE_VALUE')
                call_engine('github_archive',failing)
        v=self.read()
        self.assertEqual(v['status'],'FAILED')
        self.assertEqual(v['steps'][0]['exception_type'],'PermissionError')
        self.assertNotIn('PRIVATE_VALUE',json.dumps(v))

    def test_skipped_provider_not_configured(self):
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            call_engine('local_ai_review',lambda: {'status':'not_configured','reason':'local_ai_provider_not_configured'})
        self.assertEqual(self.read()['steps'][0]['status'],'SKIPPED')

    def test_execution_once(self):
        count=[]
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            call_engine('research',lambda: count.append(1))
        self.assertEqual(count,[1])

    def test_no_trace_no_extra_io(self):
        with execution_scope(155,229,None,receipt_root=self.folder):
            self.assertEqual(call_engine('research',lambda:3),3)
        self.assertFalse(list(self.folder.iterdir()))

    def test_reject_invalid_engine(self):
        with self.assertRaises(ValueError):call_engine('git token=PRIVATE',lambda:None)

    def test_no_global_context_leak(self):
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            call_engine('research',lambda:1)
        self.events.clear()
        call_engine('research',lambda:2)
        self.assertEqual(self.events,[])

    def test_assertion_level_counts_are_redacted(self):
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            record_items('assertion_web_investigator', [
                {'key':'tempo', 'status':'documents_read', 'documents':[{'text':'PRIVATE_PAGE'}], 'value':'PRIVATE_VALUE'},
                {'key':'duration','status':'no_results','documents':[]},
            ])
        data=self.read()
        self.assertEqual(data['item_count'],2)
        self.assertEqual(data['items'][0]['document_count'],1)
        self.assertEqual(data['items'][0]['duration_ms'],None)
        self.assertNotIn('PRIVATE_PAGE',json.dumps(data))
        self.assertNotIn('PRIVATE_VALUE',json.dumps(data))

    def test_measured_assertion_time(self):
        import time
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            started=time.perf_counter_ns()
            record_item('assertion_web_investigator',{'key':'tempo','status':'documents_read','documents':[]},started)
        data=self.read()
        self.assertEqual(data['items'][0]['duration_semantics'],'measured')
        self.assertIsInstance(data['items'][0]['duration_ms'],float)

    def test_degraded_engine_status(self):
        with execution_scope(155,229,Trace(),receipt_root=self.folder):
            call_engine('web_research',lambda:{'status':'partial','reason':'web_search_partially_unavailable'})
        self.assertEqual(self.read()['steps'][0]['status'],'DEGRADED')

    def test_io_error_does_not_change_scientific_result(self):
        import io
        from contextlib import redirect_stdout
        output = io.StringIO()
        with patch('profile_engine_diagnostic._local_summary',side_effect=PermissionError('PRIVATE_PATH')):
            with redirect_stdout(output):
                with execution_scope(155,229,Trace(),receipt_root=self.folder):
                    result=call_engine('research',lambda:42)
        self.assertEqual(result,42)
        self.assertIn('PROFILE_ENGINE_DIAG_ERROR=local_summary:PermissionError',output.getvalue())
        self.assertNotIn('PRIVATE_PATH',output.getvalue())

    def test_temp_file_on_same_volume(self):
        from unittest.mock import patch
        import profile_engine_diagnostic as m
        original=m.tempfile.mkstemp
        dirs=[]
        def observed(*args,**kwargs):
            dirs.append(Path(kwargs['dir']))
            return original(*args,**kwargs)
        with patch.object(m.tempfile,'mkstemp',side_effect=observed):
            with execution_scope(155,229,Trace(),receipt_root=self.folder):
                call_engine('research',lambda:True)
        self.assertEqual(dirs,[self.folder/'profile'/'run-000155'])

if __name__ == '__main__': unittest.main(verbosity=2)

"""R172: exact-job one-shot guard. No HTTP, GPU, SQLite or LAB writes."""
import ast
from contextlib import nullcontext
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
WORKER=ROOT/'runtime/profile_ai_requests_worker.py'


def isolated():
    """Load production once() AST without importing live project or opening sockets."""
    source=WORKER.read_text(encoding='utf-8')
    tree=ast.parse(source)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='once')
    code=compile(ast.Module(body=[fn],type_ignores=[]),str(WORKER),'exec')
    state={'PATH':'/internal/analysis/desktop/profile/ai-requests',
           'nullcontext':nullcontext,'enabled':lambda:False,
           'emit':lambda *a,**kw:None,'snap':lambda *a,**kw:None,
           'STARTUP_PROVENANCE':{},'json':__import__('json'),
           'traceback':__import__('traceback'),
           'ExpertiseCancelled':type('ExpertiseCancelled',(Exception,),{})}
    exec(code,state)
    return state

class ExactOneShot172(unittest.TestCase):
    def setUp(self):
        self.s=isolated();self.calls=[];self.rows=[]
        self.s['api']=self.api
        self.s['process']=self.process
        self.s['assert_running']=lambda rid,jid: self.calls.append(('state',rid,jid))
    def api(self,path,data=None):
        self.calls.append(('api',path,data))
        if path==self.s['PATH']:
            return {'requests':self.rows}
        if path.endswith('/claim'):
            return {'claimed':True}
        if path.endswith('/finish'):
            return {'ok':True,'request':{'status':data['status']}}
        if path.endswith('/cancelled'):
            return {'ok':True,'request':{'status':'cancelled'}}
        raise AssertionError(path)
    def process(self,rid,client,check_cancel=None):
        self.calls.append(('process',rid))
        check_cancel()
        return {'revision':9001}
    def test_exact_job_completes_single_claim_and_finish(self):
        self.rows=[{'job_id':225,'run_id':196}]
        self.assertEqual(self.s['once'](object(),225,196),1)
        claims=[x for x in self.calls if x[0]=='api' and x[1].endswith('/claim')]
        finishes=[x for x in self.calls if x[0]=='api' and x[1].endswith('/finish')]
        self.assertEqual(len(claims),1)
        self.assertEqual(len(finishes),1)
        self.assertTrue(finishes[0][1].endswith('/196/finish'))
        self.assertEqual(finishes[0][2]['job_id'],225)
        self.assertEqual(len([x for x in self.calls if x[0]=='process']),1)
    def assert_no_claim(self,reason):
        with self.assertRaisesRegex(RuntimeError,reason):self.s['once'](object(),225,196)
        self.assertFalse(any(x[0]=='api' and x[1].endswith(('/claim','/finish')) for x in self.calls))
    def test_empty_list_refused_without_claim(self):
        self.rows=[];self.assert_no_claim('exclusive_fifo_head_required')
    def test_multiple_queued_refused_without_claim(self):
        self.rows=[{'job_id':225,'run_id':196},{'job_id':226,'run_id':197}]
        self.assert_no_claim('exclusive_fifo_head_required')
    def test_different_job_refused_without_claim(self):
        self.rows=[{'job_id':226,'run_id':196}];self.assert_no_claim('fifo_identity_mismatch')
    def test_different_run_refused_without_claim(self):
        self.rows=[{'job_id':225,'run_id':197}];self.assert_no_claim('fifo_identity_mismatch')
    def test_boolean_identity_is_not_integer(self):
        self.rows=[{'job_id':True,'run_id':196}];self.assert_no_claim('fifo_identity_mismatch')
    def test_claim_refusal_does_not_finish(self):
        self.rows=[{'job_id':225,'run_id':196}]
        def refuse(path,data=None):
            self.calls.append(('api',path,data))
            if path==self.s['PATH']:return {'requests':self.rows}
            if path.endswith('/claim'):return {'claimed':False}
            raise AssertionError(path)
        self.s['api']=refuse
        with self.assertRaisesRegex(RuntimeError,'one_shot_claim_refused'):
            self.s['once'](object(),225,196)
        self.assertFalse(any(x[0]=='process' or (x[0]=='api' and x[1].endswith('/finish')) for x in self.calls))
    def test_cancelled_never_finishes_and_ack_exact_job(self):
        self.rows=[{'job_id':225,'run_id':196}]
        exc=self.s['ExpertiseCancelled']
        def cancelled(r,j):raise exc('cancelled')
        self.s['assert_running']=cancelled
        self.assertEqual(self.s['once'](object(),225,196),1)
        self.assertTrue(any(x[0]=='api' and x[1].endswith('/196/cancelled') and x[2]['job_id']==225 for x in self.calls))
        self.assertFalse(any(x[0]=='api' and x[1].endswith('/finish') for x in self.calls))
    def test_one_shot_cli_requires_exact_ids(self):
        source=WORKER.read_text(encoding='utf-8')
        self.assertIn('if args.once:',source)
        self.assertIn('parser.error(\'--once requires positive --job-id and --run-id\')',source)
        self.assertIn('target_job_id=args.job_id, target_run_id=args.run_id',source)

if __name__=='__main__':unittest.main()

import unittest
from runtime.canonical_job_worker import consume
CONTEXT={'schema':'ezstudio.assistant-final-job.v1','job_id':181,'run_id':143,'song_id':42,'status':'queued',
'recording':{'title':'Inch Allah - Salvatore Adamo','artist':'Salvatore Adamo','version':None,'track_id':'42'},
'assertions':[{'id':'tempo','characteristic':'tempo','value':112.347}]}
class Client:
 def __init__(self,claim=True):self.calls=[];self.claim=claim
 def request(self,path,data=None):
  self.calls.append((path,data))
  if path.endswith('/context'):return CONTEXT
  if path.endswith('/claim'):return {'claimed':self.claim}
  if path.endswith('/finish'):return {'ok':True,'request':{'status':data['status']}}
  raise AssertionError(path)
class WorkerTests(unittest.TestCase):
 def test_preflight_does_not_claim(self):
  c=Client();r=consume(181,c)
  self.assertEqual(r['status'],'preflight_only');self.assertEqual(len(c.calls),1)
 def test_run_id_is_used_for_claim_finish(self):
  c=Client();r=consume(181,c,True,lambda context:{'job_id':181,'run_id':143,'status':'discovery_failed'})
  self.assertEqual(r['status'],'error')
  self.assertTrue(c.calls[1][0].endswith('/143/claim'))
  self.assertTrue(c.calls[2][0].endswith('/143/finish'))
  self.assertEqual(c.calls[2][1]['status'],'error')
 def test_refusal_stops_without_finish(self):
  c=Client(False)
  with self.assertRaisesRegex(RuntimeError,'claim_refused'):consume(181,c,True)
  self.assertEqual(len(c.calls),2)
 def test_exception_attempts_error_finish(self):
  c=Client()
  def broken(context):raise OSError('redact')
  with self.assertRaisesRegex(RuntimeError,'marked_error'):consume(181,c,True,broken)
  self.assertEqual(c.calls[-1][1]['status'],'error')
if __name__=='__main__':unittest.main()

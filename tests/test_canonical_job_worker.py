import unittest
from runtime.canonical_job_worker import consume, record_intake, scan_queued
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
class CheckpointClient(Client):
 def __init__(self):
  super().__init__()
  self.event=None
 def request(self,path,data=None):
  if path.endswith('/checkpoints'):
   self.calls.append((path,data))
   if data is not None:
    self.event={'id':7,'job_id':181,'run_id':143,'event_key':data['event_key'],'detail':data['detail']}
    return {'ok':True,'event':self.event}
   return {'schema':'ezstudio.assistant-checkpoint-history.v1','job_id':181,'events':[self.event]}
  return super().request(path,data)
class QueueClient:
 def request(self,path,data=None):
  return {'schema':'ezstudio.profile-ai-history.v1','jobs':[
   {'job_id':182,'status':'queued'},{'job_id':181,'status':'queued'},
   {'job_id':180,'status':'completed'}]}
class WorkerTests(unittest.TestCase):
 def test_batch_scans_only_queued_jobs(self):
  seen=[]
  def process(job_id,client):
   seen.append(job_id)
   if job_id==182:raise ValueError('metadata_missing')
   return {'job_id':job_id,'status':'intake_checkpoint_persisted'}
  result=scan_queued(QueueClient(),intake=process)
  self.assertEqual(seen,[181,182])
  self.assertEqual(result['queued_seen'],2)
  self.assertEqual(result['results'][1]['status'],'intake_failed')

 def test_intake_persisted_and_read_back_without_claim(self):
  c=CheckpointClient()
  result=record_intake(181,c)
  self.assertEqual(result['status'],'intake_checkpoint_persisted')
  self.assertEqual(result['event_id'],7)
  self.assertEqual([x[0].rsplit('/',1)[-1] for x in c.calls],['context','checkpoints','checkpoints'])
  self.assertFalse(result['claimed'])
 def test_intake_readback_failure(self):
  c=CheckpointClient()
  def bad(path,data=None):
   result=CheckpointClient.request(c,path,data)
   if path.endswith('/checkpoints') and data is None:
    result['events']=[]
   return result
  c.request=bad
  with self.assertRaisesRegex(RuntimeError,'readback_mismatch'):
   record_intake(181,c)

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

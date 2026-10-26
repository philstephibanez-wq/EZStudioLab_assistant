import unittest
from runtime.canonical_queue_pass import run_queue
class Client:
 def request(self,path,data=None):
  return {'schema':'ezstudio.profile-ai-history.v1','jobs':[
   {'job_id':182,'status':'queued'},{'job_id':181,'status':'queued'},
   {'job_id':180,'status':'completed'},{'job_id':181,'status':'queued'}]}
class TestQueuePass(unittest.TestCase):
 def test_preview_never_calls_worker(self):
  def fail(*args,**kwargs):raise AssertionError('worker invoked')
  result=run_queue(Client(),worker=fail)
  self.assertEqual(result['queued_found'],2)
  self.assertEqual([r['job_id'] for r in result['results']],[181,182])
  self.assertTrue(all(r['status']=='queued_preview' for r in result['results']))
 def test_research_pass_without_claim(self):
  seen=[]
  def research(job_id,client):
   seen.append(job_id)
   return {'job_id':job_id,'status':'discovery_failed','claimed':False,'finished':False}
  result=run_queue(Client(),research=True,researcher=research)
  self.assertEqual(seen,[181,182])
  self.assertEqual(result['mode'],'research')
  self.assertTrue(all(r['claimed'] is False for r in result['results']))
 def test_execute_isolates_errors(self):
  visited=[]
  def worker(job_id,client,execute):
   visited.append(job_id)
   if job_id==181:raise RuntimeError('failure')
   return {'job_id':job_id,'status':'error','finished':True}
  result=run_queue(Client(),execute=True,worker=worker)
  self.assertEqual(visited,[181,182])
  self.assertEqual(result['results'][0]['status'],'worker_failed')
  self.assertEqual(result['results'][1]['status'],'error')
  self.assertEqual(result['documentary_success_count'],0)
if __name__=='__main__':unittest.main()

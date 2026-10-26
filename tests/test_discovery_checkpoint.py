import unittest
from runtime.canonical_job_worker import record_discovery, PATH
from tests.test_canonical_job_worker import CONTEXT
class Client:
 def __init__(self):self.saved=None;self.calls=[]
 def request(self,path,data=None):
  self.calls.append((path,data))
  if path.endswith('/context'):return CONTEXT
  if path.endswith('/checkpoints'):
   if data is not None:
    self.saved={'id':3,'run_id':143,'event_key':data['event_key'],'detail':data['detail']}
    return {'ok':True,'event':self.saved}
   return {'events':[self.saved]}
  raise AssertionError(path)
class TestDiscoveryCheckpoint(unittest.TestCase):
 def test_failure_is_audited_without_claim_finish(self):
  c=Client()
  r=record_discovery(181,c,research=lambda ctx:{'job_id':181,'run_id':143,'status':'discovery_failed','discovered_count':0,'read_count':0})
  self.assertEqual(r['status'],'discovery_failed')
  self.assertEqual(r['checkpoint_id'],3)
  self.assertEqual([x[0].rsplit('/',1)[-1] for x in c.calls],['context','checkpoints','checkpoints'])
  self.assertFalse(r['claimed'])
 def test_coverage_is_not_a_success_verdict(self):
  c=Client()
  r=record_discovery(181,c,research=lambda ctx:{'job_id':181,'run_id':143,'status':'candidate_coverage_only_no_musical_verdict','discovered_count':6,'read_count':4})
  self.assertEqual(r['status'],'verification_blocked')
  self.assertFalse(r['review_persisted'])
if __name__=='__main__':unittest.main()

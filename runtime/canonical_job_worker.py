"""One-shot LAB canonical AI worker. By default: safe read-only preflight.
--execute claims job; records explicit error unless verified external review is persisted.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from runtime.musical_contract import normalize
from runtime.open_web_sets import analyze

PATH='/internal/analysis/desktop/profile/ai-requests'

def load_token(lab_root):
    token=os.environ.get('EZSTUDIO_ANALYSIS_WORKER_TOKEN','').strip()
    if token:return token
    for line in (Path(lab_root)/'.env.local').read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('EZSTUDIO_ANALYSIS_WORKER_TOKEN='):
            token=line.split('=',1)[1].strip().strip('"').strip("'")
            if token:return token
    raise RuntimeError('LAB_token_unavailable')

class LabClient:
    def __init__(self,token,opener=urlopen):
        self.token,self.opener=token,opener
    def request(self,path,data=None):
        body=json.dumps(data).encode('utf-8') if data is not None else None
        request=Request('http://127.0.0.1:8701'+path,data=body,
            headers={'X-EZScore-Analysis-Token':self.token,'Content-Type':'application/json','Accept':'application/json'},
            method='POST' if data is not None else 'GET')
        with self.opener(request,timeout=12) as response:
            return json.loads(response.read(1000000))

def consume(job_id,client,execute=False,research=analyze):
    if not isinstance(job_id,int) or job_id<1:raise ValueError('invalid_job_id')
    context=client.request(PATH+'/'+str(job_id)+'/context')
    if (context.get('schema')!='ezstudio.assistant-final-job.v1'
        or context.get('job_id')!=job_id or context.get('status')!='queued'
        or not isinstance(context.get('run_id'),int) or context['run_id']<1
        or not isinstance(context.get('song_id'),int) or context['song_id']<1):
        raise RuntimeError('canonical_context_invalid')
    normalized=normalize({'recording':context['recording'],'assertions':context['assertions']})
    run_id=context['run_id']
    result={'job_id':job_id,'run_id':run_id,'song_id':context['song_id'],
            'assertion_count':len(normalized['assertions'])}
    if not execute:
        return {**result,'status':'preflight_only','claimed':False,'finished':False}
    if client.request(PATH+'/'+str(run_id)+'/claim',{}).get('claimed') is not True:
        raise RuntimeError('canonical_claim_refused')
    reason='assistant_documentary_verification_unavailable'
    try:
        discovery=research(context)
        if discovery.get('job_id')!=job_id or discovery.get('run_id')!=run_id:
            raise RuntimeError('research_identity_mismatch')
        if discovery.get('status')=='discovery_failed':
            reason='assistant_discovery_failed'
        finished=client.request(PATH+'/'+str(run_id)+'/finish',
                                {'status':'error','message':reason})
        if finished.get('ok') is not True or (finished.get('request') or {}).get('status')!='error':
            raise RuntimeError('finish_not_confirmed')
        return {**result,'status':'error','claimed':True,'finished':True,
                'reason':reason,'read_count':discovery.get('read_count',0),
                'discovered_count':discovery.get('discovered_count',0),
                'review_persisted':False,'verdicts':[]}
    except Exception:
        try:
            finished=client.request(PATH+'/'+str(run_id)+'/finish',
                                    {'status':'error','message':'assistant_worker_exception'})
            if finished.get('ok') is not True:
                raise RuntimeError('error_finish_unconfirmed')
        except Exception:
            raise RuntimeError('error_finish_unconfirmed_job_may_be_running') from None
        raise RuntimeError('assistant_worker_exception_job_marked_error') from None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--job-id',type=int,required=True)
    parser.add_argument('--lab-root',default=r'H:\EZStudio_lab')
    parser.add_argument('--execute',action='store_true',help='Moves canonical queued job to error on no verified review')
    args=parser.parse_args()
    result=consume(args.job_id,LabClient(load_token(args.lab_root)),execute=args.execute)
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['status']=='preflight_only' else 2

if __name__=='__main__':
    raise SystemExit(main())

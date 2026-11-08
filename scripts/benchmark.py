"""Reproducible local-model experiment. No paid APIs, tools, credentials or customer data."""
import argparse
import hashlib
import json
import sys
import time
import urllib.request
import urllib.parse
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dashboard.plugin_api import Recorder, Store, make_comparison

TEXTS = [
    ("I was charged twice for the same invoice.","billing"),
    ("Please explain the amount on my latest bill.","billing"),
    ("My payment has not appeared on the invoice.","billing"),
    ("I need a copy of last month's invoice.","billing"),
    ("My electricity meter display is blank.","meter"),
    ("The meter reading is not updating.","meter"),
    ("How do I submit my electricity meter reading?","meter"),
    ("My smart meter shows an error code.","meter"),
    ("I cannot log in to my account.","account"),
    ("Please reset the password for my account.","account"),
    ("I want to change the email address on my account.","account"),
    ("How can I update my account contact details?","account"),
]
ITEMS=[{"id":f"T{i+1:02}","text":t,"expected":e} for i,(t,e) in enumerate(TEXTS)]
SYSTEM=("Classify each support ticket as billing, meter, or account. Billing is invoices and payments; "
        "meter is the physical meter and readings; account is login, password and contact details. "
        "Return JSON only, with a tickets array of objects containing id and category. "
        "Return exactly one object per input ticket, preserving its id. /no_think")
SCHEMA={"type":"object","properties":{"tickets":{"type":"array","items":{"type":"object","properties":{
    "id":{"type":"string"},"category":{"type":"string","enum":["billing","meter","account"]}},
    "required":["id","category"],"additionalProperties":False}}},"required":["tickets"],"additionalProperties":False}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError("Redirects are not allowed in the local benchmark")


def classify(endpoint, model, items):
    schema={**SCHEMA, 'properties': {'tickets': {**SCHEMA['properties']['tickets'], 'minItems':len(items), 'maxItems':len(items)}}}
    body={"model":model,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":json.dumps([{k:v for k,v in item.items() if k!='expected'} for item in items])}],
          "temperature":0,"seed":42,"max_tokens":768,"cache_prompt":False,"chat_template_kwargs":{"enable_thinking":False},
          "response_format":{"type":"json_schema","json_schema":{"name":"tickets","strict":True,"schema":schema}}}
    req=urllib.request.Request(endpoint+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.build_opener(NoRedirect).open(req,timeout=90) as response:
        return json.load(response)


def check_answers(answers, expected=ITEMS):
    found={}
    malformed=False
    for item in answers:
        if not isinstance(item,dict) or item.get('id') in found:
            malformed=True;continue
        found[item.get('id')]=item.get('category')
    if malformed or set(found)!= {item['id'] for item in expected}:return 0
    return sum(found[item['id']]==item['expected'] for item in expected)


def run(args):
    parsed=urllib.parse.urlparse(args.endpoint)
    if parsed.scheme!='http' or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SystemExit('Use an unauthenticated loopback HTTP model endpoint; no cloud calls are allowed.')
    root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=True)
    recorder=Recorder(lambda:root,local_energy=lambda:True)
    session='watt-benchmark-'+str(uuid.uuid4())
    digest=hashlib.sha256(json.dumps({'items':ITEMS,'system':SYSTEM,'schema':SCHEMA},sort_keys=True).encode()).hexdigest()
    print('Warm-up (not counted)',flush=True)
    classify(args.endpoint,args.model,ITEMS[:1])
    classify(args.endpoint,args.model,ITEMS)
    samples=[]
    for repeat in range(args.repetitions):
        for variant in (['baseline','candidate'] if repeat%2==0 else ['candidate','baseline']):
            turn=str(uuid.uuid4()); identity={'session_id':session,'turn_id':turn,'model':args.model,'provider':'custom'}
            recorder.handle('pre_llm_call',identity)
            begin=time.monotonic();answers=[];errors=0
            batches=[[item] for item in ITEMS] if variant=='baseline' else [ITEMS]
            for batch in batches:
                payload={**identity,'api_request_id':str(uuid.uuid4())}
                recorder.handle('pre_api_request',payload)
                try:
                    response=classify(args.endpoint,args.model,batch)
                    recorder.handle('post_api_request',{**payload,'usage':response.get('usage')})
                    answers.extend(json.loads(response['choices'][0]['message']['content'])['tickets'])
                except Exception:
                    errors+=1
                    recorder.handle('api_request_error',payload)
            passed=check_answers(answers) if not errors else 0
            recorder.handle('on_session_end',{**identity,'completed':not errors,'failed':bool(errors)})
            receipt=Store(root).latest(session)
            sample={'variant':variant,'repeat':repeat+1,'passed':passed,'checked':len(ITEMS),'requests':len(batches),
                    'joules':receipt['energy']['joules'],'seconds':time.monotonic()-begin,'overlap':receipt['energy']['overlap'],
                    'receipt_id':receipt['id'],'answers':answers}
            samples.append(sample)
            print(json.dumps({k:v for k,v in sample.items() if k!='answers'}),flush=True)
    report=make_comparison(samples,model=args.model,workload_sha256=digest)
    report['created_at']=time.time()
    report['run_parameters']={'temperature':0,'seed':42,'cache_prompt':False,'max_tokens':768,'enable_thinking':False}
    path=root/'comparison.json';tmp=root/'comparison.pending.json'
    tmp.write_text(json.dumps(report,indent=2),encoding='utf-8');tmp.replace(path)
    print('Result:',report['verdict'],'Observed difference:',report['observed_reduction_percent'],flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--endpoint',default='http://127.0.0.1:18081/v1')
    p.add_argument('--model',default='watt-demo')
    p.add_argument('--output',required=True,help='Hermes Watt data directory for this test profile')
    p.add_argument('--repetitions',type=int,choices=range(3,11),default=3)
    run(p.parse_args())

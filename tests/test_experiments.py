import importlib.util
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dashboard import plugin_api as api


class Counter:
    def __init__(self): self.value = 0
    def snapshot(self):
        self.value += 1000
        return {'cpu_mj': self.value, 'gpu_mj': self.value}


def answer(endpoint, model, items, definition):
    return [{'id': item['id'], **item['expected']} for item in items], {'prompt_tokens': 10}


def body(ident='a'*32, **values):
    return api.ExperimentInput(request_id=ident, consent=True, **values)


SETTINGS = {'endpoint': api.DEFAULT_ENDPOINT, 'model': 'test-model'}


def test_same_engine_checks_two_workloads_and_records_every_attempt(tmp_path):
    for workload in api.WORKLOADS:
        report = api.run_experiment(tmp_path/workload, **SETTINGS, workload=workload, repetitions=3,
                                    request_fn=answer, sampler_factory=Counter)
        assert report['baseline']['passed'] == report['candidate']['passed'] == 36
        assert len(report['samples']) == 6
        receipts = api.Store(tmp_path/workload).receipts()
        assert sum(r['requests'] for r in receipts) == 39
        assert all(r['accounting_complete'] for r in receipts)
        assert report['workload'] == workload


def test_bad_answer_prevents_claim_even_with_readings(tmp_path):
    def wrong(endpoint, model, items, definition):
        return [{'id': item['id'], 'category': 'not-a-category'} for item in items], None
    report = api.run_experiment(tmp_path, **SETTINGS, request_fn=wrong, sampler_factory=Counter)
    assert report['verdict'] == 'inconclusive'
    assert report['observed_reduction_percent'] is None


def test_exact_extraction_checks_reject_boolean_and_extra_fields():
    item = {'id': 'D', 'expected': {'invoice': 'INV-A', 'amount_cents': 1}}
    assert api.checked_answers([{'id': 'D', 'invoice': 'INV-A', 'amount_cents': 1}], [item]) == 1
    assert api.checked_answers([{'id': 'D', 'invoice': 'INV-A', 'amount_cents': True}], [item]) == 0
    assert api.checked_answers([{'id': 'D', 'invoice': 'INV-A', 'amount_cents': 1, 'other': 1}], [item]) == 0


@pytest.mark.parametrize('endpoint', ['https://example.com/v1','http://localhost:18082/v1','http://127.0.0.1/v1','http://127.0.0.1:2/admin','http://user:pass@127.0.0.1:2/v1','http://127.0.0.1:2/v1?key=private','file:///tmp/test','http://127.0.0.2:2/v1'])
def test_no_remote_or_arbitrary_endpoint(endpoint):
    with pytest.raises(ValueError): api.local_endpoint(endpoint)


def test_real_http_request_contains_synthetic_inputs_not_expected_answers():
    observed = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            content = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            observed.append(content)
            response = {'choices':[{'message':{'content':json.dumps({'results':[{'id':'T01','category':'billing'}]})}}]}
            self.send_response(200); self.end_headers(); self.wfile.write(json.dumps(response).encode())
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        answers,_=api.request_answers(f'http://127.0.0.1:{server.server_port}/v1','test-model',api.WORKLOADS['tickets']['items'][:1],api.WORKLOADS['tickets'])
        assert answers == [{'id':'T01','category':'billing'}]
        assert 'expected' not in observed[0]['messages'][1]['content']
        assert observed[0]['cache_prompt'] is False
    finally: server.shutdown();server.server_close();thread.join()


def test_redirect_is_not_followed():
    paths=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            paths.append(self.path)
            self.send_response(307);self.send_header('Location','/elsewhere');self.end_headers()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with pytest.raises(api.LocalModelUnavailable):
            api.request_answers(f'http://127.0.0.1:{server.server_port}/v1','test',[],api.WORKLOADS['tickets'])
        assert paths==['/v1/chat/completions']
    finally:server.shutdown();server.server_close();thread.join()


def test_overlapping_observed_work_makes_comparison_inconclusive(tmp_path):
    api.Store(tmp_path).start('other','another-session','another-model')
    report=api.run_experiment(tmp_path,**SETTINGS,request_fn=answer,sampler_factory=Counter)
    assert report['verdict']=='inconclusive'
    assert all(s['overlap'] for s in report['samples'])
    assert api.summary(api.Store(tmp_path))['summary']['included_energy_windows'] == 0
    api.Store(tmp_path).finish('other', status='completed', joules=10, overlap=False)
    assert all(r['energy']['overlap'] for r in api.Store(tmp_path).receipts())


def test_job_claim_is_atomic_and_same_request_is_idempotent(tmp_path):
    launched=[]
    jobs=api.ExperimentJobs(launcher=launched.append)
    jobs.store(tmp_path)
    barrier=threading.Barrier(6)
    def submit(_):
        barrier.wait()
        return jobs.start(tmp_path,body(),SETTINGS)
    with ThreadPoolExecutor(max_workers=6) as pool: results=list(pool.map(submit,range(6)))
    assert len(launched)==1
    assert {r['id'] for r in results}=={'a'*32}
    with pytest.raises(api.HTTPException) as e:jobs.start(tmp_path,body('b'*32),SETTINGS)
    assert e.value.status_code==409
    with pytest.raises(api.HTTPException):jobs.start(tmp_path,body(workload='extraction'),SETTINGS)


def test_failure_preserves_last_result_and_hides_raw_error(tmp_path):
    previous='{"old":"valid report"}'
    (tmp_path/'comparison.json').write_text(previous)
    def fail(*args,**kwargs):raise RuntimeError('PRIVATE PROVIDER RESPONSE')
    jobs=api.ExperimentJobs(runner=fail,launcher=lambda fn:fn())
    state=jobs.start(tmp_path,body(),SETTINGS)
    assert state['status']=='failed'
    assert 'PRIVATE' not in json.dumps(state)
    assert (tmp_path/'comparison.json').read_text()==previous


def test_cancel_before_worker_runs_preserves_report(tmp_path):
    (tmp_path/'comparison.json').write_text('old')
    queued=[]
    def runner(root,*,cancelled,**kw):
        assert cancelled()
        raise api.ExperimentCancelled()
    jobs=api.ExperimentJobs(runner=runner,launcher=queued.append)
    jobs.start(tmp_path,body(),SETTINGS)
    assert jobs.cancel(tmp_path,'a'*32)['status']=='cancelling'
    queued[0]()
    assert jobs.state(tmp_path)['status']=='cancelled'
    assert (tmp_path/'comparison.json').read_text()=='old'


def test_worker_keeps_original_profile_after_request_returns(tmp_path):
    queued=[];seen=[]
    def runner(root,**kw):seen.append(root);return {'scope':'synthetic test'}
    jobs=api.ExperimentJobs(runner=runner,launcher=queued.append)
    jobs.start(tmp_path/'a',body(),SETTINGS)
    assert jobs.state(tmp_path/'b') is None
    with pytest.raises(api.HTTPException):jobs.cancel(tmp_path/'b','a'*32)
    queued[0]()
    assert seen==[(tmp_path/'a').resolve()]
    assert not (tmp_path/'b'/'comparison.json').exists()


def test_crashed_host_does_not_leave_infinite_running_state(tmp_path):
    jobs=api.ExperimentJobs(launcher=lambda fn:None)
    jobs.start(tmp_path,body(),SETTINGS)
    with jobs.store(tmp_path).connect() as db:db.execute('UPDATE experiments SET started=0')
    assert jobs.state(tmp_path)['status']=='interrupted'
    assert jobs.start(tmp_path,body('b'*32),SETTINGS)['status']=='running'


def test_api_rejects_extra_payload_cross_site_and_missing_consent(monkeypatch,tmp_path):
    monkeypatch.setattr(api,'storage_root',lambda:tmp_path)
    monkeypatch.setattr(api,'experiment_settings',lambda:dict(SETTINGS))
    monkeypatch.setattr(api,'experiment_jobs',api.ExperimentJobs(launcher=lambda fn:None))
    app=FastAPI();app.include_router(api.router)
    with TestClient(app) as client:
        payload=body().model_dump()
        assert client.post('/experiment',json={**payload,'endpoint':'http://example.com'}).status_code==422
        assert client.post('/experiment',json={**payload,'consent':False}).status_code==400
        assert client.post('/experiment',json=payload,headers={'Sec-Fetch-Site':'cross-site'}).status_code==403
        assert client.post('/experiment',json=payload).status_code==202
        assert client.post('/experiment',json=payload).status_code==202
        assert client.get('/experiment').json()['job']['id']==payload['request_id']
        assert client.post('/experiment/cancel',json={'request_id':payload['request_id']}).status_code==200


def test_dashboard_direct_file_loader_supports_new_routes():
    spec=importlib.util.spec_from_file_location('watt_standalone',Path(api.__file__))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert {'/overview','/comparison','/experiment','/experiment/cancel'} <= {r.path for r in module.router.routes}


def test_storage_gap_cannot_reuse_previous_receipt(monkeypatch, tmp_path):
    original = api.Store.latest
    seen = []
    def stale(self, session):
        result = original(self, session)
        if seen:
            return seen[0]
        seen.append(result)
        return result
    monkeypatch.setattr(api.Store, 'latest', stale)
    with pytest.raises(api.LocalModelUnavailable):
        api.run_experiment(tmp_path, **SETTINGS, request_fn=answer, sampler_factory=Counter)

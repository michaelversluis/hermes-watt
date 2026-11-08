import json
import math
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dashboard.plugin_api import AppleSampler, Recorder, Store, opaque, summary, render_receipt, safe_label, tokens
from dashboard import plugin_api


class Counter:
    def __init__(self): self.value=0
    def snapshot(self):
        self.value += 1800000
        return {"cpu_mj":self.value,"gpu_mj":self.value}


@pytest.fixture
def rec(tmp_path):
    return Recorder(lambda:tmp_path,local_energy=lambda:True,sampler_factory=Counter)


def event(rec,name,**kw):
    rec.handle(name,{"session_id":"session-one","turn_id":"turn-one","model":"Qwen/test",**kw})


def finish(rec): event(rec,"on_session_end",completed=True)


def test_units_and_label(rec,tmp_path):
    event(rec,"pre_llm_call");finish(rec)
    r=Store(tmp_path).receipts()[0]
    assert r["energy"]["joules"]==3600
    assert r["energy"]["wh"]==1
    assert r["energy"]["status"]=="estimated"
    assert r["inference_energy"]["status"]=="unknown"
    assert r["quality"]=="not assessed"


def test_repeated_events_do_not_double_count(rec,tmp_path):
    event(rec,"pre_llm_call")
    for _ in range(3):
        event(rec,"pre_api_request",api_request_id="request")
        event(rec,"post_api_request",api_request_id="request",usage={"prompt_tokens":8,"completion_tokens":3})
    finish(rec);finish(rec)
    r=Store(tmp_path).receipts()[0]
    assert r["requests"]==1
    assert r["attempts"][0]["input_tokens"]==8
    assert r["energy"]["joules"]==3600


def test_error_retry_and_auxiliary_are_distinct(rec,tmp_path):
    event(rec,"pre_llm_call")
    event(rec,"api_request_error",api_request_id="failed",error={"message":"SECRET"})
    event(rec,"post_api_request",api_request_id="retried")
    event(rec,"post_auxiliary_call",api_request_id="compression")
    finish(rec)
    r=Store(tmp_path).receipts()[0]
    assert (r["requests"],r["failed_requests"],r["auxiliary_requests"])==(3,1,1)
    assert "SECRET" not in json.dumps(r)


@pytest.mark.parametrize("payload,status",[({"interrupted":True},"interrupted"),({"failed":True},"incomplete"),({},"incomplete")])
def test_unfinished_turns_close(rec,tmp_path,payload,status):
    event(rec,"pre_llm_call");event(rec,"on_session_end",**payload)
    assert not rec.active
    assert Store(tmp_path).receipts()[0]["status"]==status


def test_finalize_closes_only_that_session(rec,tmp_path):
    event(rec,"pre_llm_call")
    event(rec,"pre_llm_call",session_id="other",turn_id="other")
    rec.handle("on_session_finalize",{"session_id":"session-one"})
    assert len(rec.active)==1
    assert Store(tmp_path).latest("session-one")["status"]=="interrupted"


def test_overlaps_excluded_from_totals(rec,tmp_path):
    event(rec,"pre_llm_call")
    event(rec,"pre_llm_call",turn_id="second")
    finish(rec);event(rec,"on_session_end",turn_id="second",completed=True)
    result=summary(Store(tmp_path))
    assert all(x["energy"]["overlap"] for x in result["receipts"])
    assert result["summary"]["estimated_local_wh"] is None
    assert result["summary"]["excluded_energy_windows"]==2


def test_opt_out_does_not_initialize_meter(tmp_path):
    def fail(): raise AssertionError("must not run")
    r=Recorder(lambda:tmp_path,sampler_factory=fail)
    event(r,"pre_llm_call");finish(r)
    result=Store(tmp_path).receipts()[0]
    assert result["energy"]["wh"] is None
    assert result["reason"]=="local_measurement_disabled"


def test_recording_disabled_writes_nothing(tmp_path):
    r=Recorder(lambda:tmp_path,enabled=lambda:False)
    event(r,"pre_llm_call");finish(r)
    assert not list(tmp_path.iterdir())


def test_measurement_failure_does_not_crash_or_fake_zero(tmp_path):
    def fail(): raise RuntimeError("sensitive driver detail")
    r=Recorder(lambda:tmp_path,local_energy=lambda:True,sampler_factory=fail)
    event(r,"pre_llm_call");finish(r)
    result=Store(tmp_path).receipts()[0]
    assert result["energy"]["wh"] is None
    assert result["reason"]=="local_measurement_unavailable"
    assert "sensitive" not in json.dumps(result)


def test_counter_reset_is_unknown(tmp_path):
    class Reset:
        def __init__(self):self.i=2
        def snapshot(self):
            self.i-=1
            return {"cpu_mj":self.i,"gpu_mj":self.i}
    r=Recorder(lambda:tmp_path,local_energy=lambda:True,sampler_factory=Reset)
    event(r,"pre_llm_call");finish(r)
    assert Store(tmp_path).receipts()[0]["energy"]["wh"] is None


def test_missing_start_never_claims_full_measurement(rec,tmp_path):
    event(rec,"post_api_request",api_request_id="r");finish(rec)
    r=Store(tmp_path).receipts()[0]
    assert r["energy"]["wh"] is None
    assert r["reason"]=="missing_start"


def test_payload_privacy_and_session_isolation(rec,tmp_path):
    secret="PRIVATE-PROMPT-CONTENT"
    event(rec,"pre_llm_call",session_id="customer@example.invalid",user_message=secret)
    event(rec,"post_api_request",session_id="customer@example.invalid",api_request_id="r",request={"key":secret},response=secret,base_url="https://user:secret@provider/")
    event(rec,"on_session_end",session_id="customer@example.invalid",completed=True)
    assert Store(tmp_path).latest("session-one") is None
    content=(tmp_path/"receipts.sqlite3").read_bytes()
    assert secret.encode() not in content
    assert b"customer@example.invalid" not in content
    assert b"https://" not in content


def test_separate_profiles_use_separate_stores(tmp_path):
    current=[tmp_path/'a']
    r=Recorder(lambda:current[0])
    event(r,"pre_llm_call");finish(r)
    current[0]=tmp_path/'b'
    assert Store(current[0]).receipts()==[]
    event(r,"pre_llm_call");finish(r)
    assert len(Store(tmp_path/'a').receipts())==len(Store(tmp_path/'b').receipts())==1


def test_concurrent_callbacks(rec,tmp_path):
    event(rec,"pre_llm_call")
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda i:event(rec,"post_api_request",api_request_id=str(i%20)),range(100)))
    finish(rec)
    assert rec.errors==0
    assert Store(tmp_path).receipts()[0]["requests"]==20


@pytest.mark.parametrize("value",[None,-1,True,float('inf'),float('nan'),'7'])
def test_unknown_usage_stays_unknown(value):
    assert tokens({"input_tokens":value},"input_tokens") is None


def test_read_only_api_and_empty_state(monkeypatch,tmp_path):
    monkeypatch.setattr(plugin_api,"storage_root",lambda:tmp_path)
    app=FastAPI();app.include_router(plugin_api.router,prefix='/api/plugins/hermes-watt')
    with TestClient(app) as client:
        assert client.get('/api/plugins/hermes-watt/overview').json()['summary']['estimated_local_wh'] is None
        assert client.get('/api/plugins/hermes-watt/comparison').json()=={"comparison":None}
        assert client.post('/api/plugins/hermes-watt/overview',json={}).status_code==405


def test_raw_model_url_redacted():
    assert safe_label('https://user:password@host')=='unknown'
    assert safe_label('Qwen/Qwen3-0.6B')=='Qwen/Qwen3-0.6B'

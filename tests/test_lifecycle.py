from dashboard.plugin_api import Recorder, Store


def test_reset_uses_old_identity(tmp_path):
    r=Recorder(lambda:tmp_path)
    r.handle('pre_llm_call',{'session_id':'old','turn_id':'turn'})
    r.handle('on_session_reset',{'session_id':'new','old_session_id':'old','new_session_id':'new'})
    assert not r.active
    assert Store(tmp_path).latest('old')['status']=='interrupted'
    assert Store(tmp_path).latest('new') is None


def test_missing_request_correlation_remains_visible(tmp_path):
    r=Recorder(lambda:tmp_path)
    r.handle('pre_llm_call',{'session_id':'s','turn_id':'t'})
    r.handle('post_api_request',{'session_id':'s','turn_id':'t'})
    r.handle('on_session_end',{'session_id':'s','turn_id':'t','completed':True})
    receipt=Store(tmp_path).latest('s')
    assert receipt['requests']==0
    assert receipt['accounting_complete'] is False
    assert 'lower bound' in receipt['tips'][0]


def test_ambiguous_identifiers_do_not_collide(tmp_path):
    r=Recorder(lambda:tmp_path)
    for s,t in [('a:b','c'),('a','b:c')]:
        r.handle('pre_llm_call',{'session_id':s,'turn_id':t})
        r.handle('on_session_end',{'session_id':s,'turn_id':t,'completed':True})
    assert len(Store(tmp_path).receipts())==2


def test_disabling_during_task_closes_without_collecting_energy(tmp_path):
    enabled=[True]
    r=Recorder(lambda:tmp_path, enabled=lambda:enabled[0])
    r.handle('pre_llm_call',{'session_id':'s','turn_id':'t'})
    enabled[0]=False
    r.handle('on_session_end',{'session_id':'s','turn_id':'t','completed':True})
    receipt=Store(tmp_path).latest('s')
    assert receipt['status']=='incomplete'
    assert receipt['energy']['wh'] is None
    assert not r.active

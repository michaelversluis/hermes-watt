import copy
import pytest
from dashboard.plugin_api import make_comparison
from scripts.benchmark import check_answers, ITEMS


def samples():
    return [dict(variant=v,joules=j,seconds=2,passed=12,checked=12,overlap=False)
            for v,energies in [('baseline',[100,110,105]),('candidate',[50,55,52])] for j in energies]


def test_only_quality_checked_separated_runs_make_claim():
    r=make_comparison(samples(),model='local',workload_sha256='test')
    assert r['verdict']=='lower_energy'
    assert r['observed_reduction_percent']==pytest.approx((1-52/105)*100)


@pytest.mark.parametrize('field,value',[('passed',11),('joules',None),('joules',float('nan')),('overlap',True)])
def test_bad_or_missing_evidence_never_claims_savings(field,value):
    s=samples();s[-1][field]=value
    assert make_comparison(s,model='local',workload_sha256='test')['verdict']=='inconclusive'


def test_overlapping_energy_ranges_inconclusive():
    s=samples();s[-1]['joules']=104
    assert make_comparison(s,model='local',workload_sha256='test')['verdict']=='inconclusive'


def test_insufficient_repetitions_inconclusive():
    assert make_comparison(samples()[:2],model='local',workload_sha256='test')['verdict']=='inconclusive'


def test_duplicate_missing_or_extra_answers_fail():
    good=[{'id':i['id'],'category':i['expected']} for i in ITEMS]
    assert check_answers(good)==len(ITEMS)
    assert check_answers(good+[good[0]])==0
    assert check_answers(good[:-1])==0
    assert check_answers(good+[{'id':'foreign','category':'billing'}])==0


def test_report_recomputes_verdict_from_samples(tmp_path):
    import json
    from dashboard.plugin_api import read_comparison
    report=make_comparison(samples(),model='local',workload_sha256='test')
    report['samples'][0]['passed']=0
    report['observed_reduction_percent']=99
    (tmp_path/'comparison.json').write_text(json.dumps(report))
    assert read_comparison(tmp_path)['verdict']=='inconclusive'
    assert read_comparison(tmp_path)['observed_reduction_percent'] is None


@pytest.mark.parametrize('data', [[], None, {'schema':'hermes-watt-comparison/v1'}, {'schema':'hermes-watt-comparison/v1','samples':[None]}])
def test_invalid_reports_fail_cleanly(tmp_path, data):
    import json
    from dashboard.plugin_api import read_comparison
    (tmp_path/'comparison.json').write_text(json.dumps(data))
    with pytest.raises(ValueError): read_comparison(tmp_path)

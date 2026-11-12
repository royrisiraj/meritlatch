from copy import deepcopy
import json

import pytest

from backend.app.assurance_corpus import CORPUS_ROOT, assemble, generate, load_corpus, policy_for
from backend.app.assurance_executor import pure, binding
from backend.app.assurance_models import Observed, Profile, Scenario
from backend.app.assurance_scoring import compare,summarize


def raw():
    return [json.loads((CORPUS_ROOT/name).read_text()) for name in ("scenarios_v1.json","labels_v1.json")]


def test_independent_fixed_labels_and_generation_do_not_query_policy(monkeypatch):
    import backend.app.policy as policy
    monkeypatch.setattr(policy,"authorize",lambda *a,**k:pytest.fail("Oracle must never execute SUT"))
    data,labels=raw()
    scenarios,oracle=assemble(data,labels)
    assert len(scenarios)==len(oracle)==38
    assert tuple((s.id,s.version) for s in scenarios)==tuple(sorted(oracle))
    assert [s.model_dump() for s in generate(data)]==[s.model_dump() for s in generate(deepcopy(data))]
    cross=next(s for s in scenarios if s.id=="A05")
    assert cross.actor.tenant_id=="synthetic-org-b" and cross.actor.assigned is False
    assert cross.context.tenant_id=="synthetic-org-a"


@pytest.mark.parametrize("kind",["duplicate_label","missing_label","orphan","duplicate_scenario","conflicting_inputs","untyped_field","too_many"])
def test_oracle_rejects_invalid_or_conflicting_labels(kind):
    data,labels=raw()
    if kind=="duplicate_label":labels["labels"].append({**labels["labels"][0],"expected":{"decision":"DENY"}})
    if kind=="missing_label":labels["labels"].pop()
    if kind=="orphan":labels["labels"].append({**labels["labels"][0],"scenario_id":"ORPHAN"})
    if kind=="duplicate_scenario":data["scenarios"].append(data["scenarios"][0])
    if kind=="untyped_field":data["scenarios"][0]["permission_override"]=3
    if kind=="too_many":data["scenarios"]*=3
    if kind=="conflicting_inputs":
        data["scenarios"].append({**data["scenarios"][0],"id":"COPY"})
        labels["labels"].append({**labels["labels"][0],"scenario_id":"COPY","expected":{"decision":"DENY"}})
    with pytest.raises(ValueError):assemble(data,labels)


def test_pending_or_unreviewed_human_candidates_cannot_become_oracle():
    scenarios,_,_=load_corpus()
    original=scenarios[0].model_dump()
    for fields in ({"review_state":"PENDING_REVIEW"},{"source":"HUMAN_LABELED","review_state":"HUMAN_REVIEWED","reviewer":None}):
        with pytest.raises(ValueError):Scenario.model_validate(original|fields)


def test_safe_pure_and_read_only_binding_snapshots_match_fixed_oracle():
    scenarios,labels,_=load_corpus()
    for s in scenarios:
        if s.target=="API":continue
        actual=pure(s,policy_for(Profile.SAFE)) if s.target=="POLICY" else binding(s,policy_for(Profile.SAFE))
        assert compare(s,labels[(s.id,s.version)],actual).passed,s.id


@pytest.mark.parametrize("which,decision,status,level,classification",[
    ("A02","ALLOW","EVIDENCE_COMPLETE",2,"FALSE_APPROVAL"),
    ("A01","DENY","EVIDENCE_MISSING",0,"FALSE_REJECTION"),
    ("P15","ALLOW","EVIDENCE_COMPLETE",2,"REVIEW_BYPASS"),
    ("P15","DENY","SAFETY_ALERT",1,"REVIEW_MISMATCH"),
    ("P15","NEEDS_REVIEW","REVIEW_REQUIRED",1,"INSPECTION_MISMATCH"),
    ("P01","ALLOW","EVIDENCE_COMPLETE",1,"PERMISSION_MISMATCH")])
def test_exact_outcome_dimensions_and_three_way_classification(which,decision,status,level,classification):
    scenarios,labels,_=load_corpus()
    scenario=next(s for s in scenarios if s.id==which)
    result=compare(scenario,labels[(which,1)],Observed(decision=decision,inspection_status=status,max_permission=level,
        http_status=200 if scenario.target=="API" else None))
    assert result.mismatch==classification and not result.passed


def test_metrics_have_independent_binary_denominators_review_and_zero_denominators():
    scenarios,labels,_=load_corpus()
    rows=[]
    for key,decision in (("A02","ALLOW"),("A01","DENY"),("P15","NEEDS_REVIEW"),("P01","NEEDS_REVIEW")):
        s=next(s for s in scenarios if s.id==key)
        rows.append(compare(s,labels[(key,1)],Observed(decision=decision)))
    summary=summarize(rows,4)
    assert summary["false_approvals"]==summary["false_rejections"]==1
    assert summary["false_approval_denominator"]==summary["false_rejection_denominator"]==1
    assert summary["false_approval_rate"]==summary["false_rejection_rate"]==1
    assert summary["review_expected"]==summary["review_abstentions"]==1
    empty=summarize([],38)
    assert empty["false_approval_rate"] is None and empty["false_rejection_rate"] is None
    assert empty["skipped"]==empty["regression_failures"]==38


def test_safe_and_weak_same_unsafe_policy_scenario_reproduce_actual_authorization_bug():
    scenarios,labels,_=load_corpus()
    scenario=next(s for s in scenarios if s.id=="P15")
    good=compare(scenario,labels[("P15",1)],pure(scenario,policy_for(Profile.SAFE)))
    bad=compare(scenario,labels[("P15",1)],pure(scenario,policy_for(Profile.WEAK)))
    assert good.passed and good.actual.decision=="NEEDS_REVIEW"
    assert bad.actual.decision=="ALLOW" and bad.mismatch=="REVIEW_BYPASS"

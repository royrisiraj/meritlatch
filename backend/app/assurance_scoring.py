"""Independent comparison and explicit three-way scoring, separate from execution."""

from .assurance_models import Observed, ScenarioResult


def compare(scenario, label, actual):
    actual = Observed.model_validate(actual)
    expected = label.expected
    mismatch = None
    if actual.error_code or actual.decision is None:
        mismatch = "UNEVALUABLE"
    elif expected.decision != actual.decision:
        mismatch = ("FALSE_APPROVAL" if expected.decision == "DENY" and actual.decision == "ALLOW" else
                    "FALSE_REJECTION" if expected.decision == "ALLOW" and actual.decision == "DENY" else
                    "REVIEW_BYPASS" if actual.decision == "ALLOW" else "REVIEW_MISMATCH")
    elif expected.http_status is not None and expected.http_status != actual.http_status:
        mismatch = "HTTP_STATUS_MISMATCH"
    elif expected.inspection_status is not None and expected.inspection_status != actual.inspection_status:
        mismatch = "INSPECTION_MISMATCH"
    elif expected.max_permission is not None and expected.max_permission != actual.max_permission:
        mismatch = "PERMISSION_MISMATCH"
    elif not set(expected.required_reasons) <= set(actual.reason_codes):
        mismatch = "REASON_MISMATCH"
    return ScenarioResult(scenario_id=scenario.id, scenario_version=scenario.version, target=scenario.target,
        mandatory=label.mandatory, expected=expected, actual=actual, passed=mismatch is None,
        mismatch=mismatch, risk=scenario.risk)


def summarize(results, expected_total):
    """Positive=should DENY. Review/abstention excluded from binary denominators."""
    tp = fn = tn = fp = review = abstain = unevaluable = 0
    for item in results:
        exp, got = item.expected.decision, item.actual.decision
        if item.actual.error_code or got is None:
            unevaluable += 1
        elif exp == "NEEDS_REVIEW":
            review += 1
        elif got == "NEEDS_REVIEW":
            abstain += 1
        elif exp == "DENY":
            if got == "DENY": tp += 1
            else: fn += 1
        elif exp == "ALLOW":
            if got == "ALLOW": tn += 1
            else: fp += 1
    missing = max(0, expected_total - len(results))
    passed = sum(item.passed for item in results)
    return dict(total_expected=expected_total, total_executed=len(results), passed=passed, failed=len(results)-passed,
        true_positive=tp, false_negative=fn, true_negative=tn, false_positive=fp,
        correctly_restricted_invalid=tp, false_approvals=fn, correctly_permitted_valid=tn, false_rejections=fp,
        false_approval_denominator=tp+fn, false_rejection_denominator=tn+fp,
        false_approval_rate=fn/(tp+fn) if tp+fn else None, false_rejection_rate=fp/(tn+fp) if tn+fp else None,
        review_expected=review, review_bypasses=sum(item.mismatch == "REVIEW_BYPASS" for item in results),
        review_abstentions=abstain, unevaluable=unevaluable+missing, skipped=missing,
        regression_failures=sum(item.mandatory and not item.passed for item in results)+missing,
        source="SYNTHETIC", positive_class="SHOULD_DENY", rates_scope="BINARY_ONLY_EXCLUDES_REVIEW_AND_ABSTENTIONS")

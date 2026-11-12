"""Resolve validated append-only analysis data for the case service."""

import json


def media_observation(tx, case, evidence):
    upload = tx.get("media_uploads", tenant_id=case["tenant_id"], case_id=case["id"], evidence_id=evidence["id"])
    if not upload:
        return None, None, None
    runs = tx.recent("analysis_runs", {"tenant_id": case["tenant_id"], "case_id": case["id"], "evidence_id": evidence["id"]}, "started_case_version", 1)
    analysis = tx.get("analysis_results", run_id=runs[0]["id"], tenant_id=case["tenant_id"], case_id=case["id"]) if runs else tx.get("media_analyses", tenant_id=case["tenant_id"], case_id=case["id"], evidence_id=evidence["id"])
    observation = json.loads(analysis["observation_json"]) if analysis and analysis["status"] == "SUCCESS" else None
    return upload, analysis, observation

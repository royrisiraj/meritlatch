"""Resolve validated append-only analysis data for the case service."""

import json


def media_observation(tx, case, evidence):
    upload = tx.get("media_uploads", tenant_id=case["tenant_id"], case_id=case["id"], evidence_id=evidence["id"])
    if not upload:
        return None, None, None
    analysis = tx.get("media_analyses", tenant_id=case["tenant_id"], case_id=case["id"], evidence_id=evidence["id"])
    observation = json.loads(analysis["observation_json"]) if analysis and analysis["status"] == "SUCCESS" else None
    return upload, analysis, observation

"""Generation and fixed-label assembly; never ask the SUT for expected outcomes."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from .assurance_models import Expected, Label, Profile, Scenario
from .config import load_policy

ROOT = Path(__file__).resolve().parents[2]
CORPUS_ROOT = ROOT / "fixtures/security"
MAX_SCENARIOS = 64
RUNNER_VERSION = "phase04.1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return sha256(canonical(value).encode()).hexdigest()


def source_revision():
    paths = sorted((ROOT / "backend/app").glob("*.py"))
    return fingerprint({path.name: sha256(path.read_bytes()).hexdigest() for path in paths})


def policy_for(profile):
    """Isolated in-memory variants. Never register/export these to live policies."""
    policy = load_policy(ROOT / "policies/maintenance_v1.json")
    fields = policy.model_dump()
    if Profile(profile) == Profile.WEAK:
        fields["pressure_max"] = 50.0
    elif Profile(profile) == Profile.STRICT:
        fields["pressure_min"] = 36.0
    return type(policy).model_validate(fields)


def artifact(profile, version):
    policy = policy_for(profile)
    revision = source_revision()
    value = dict(profile=Profile(profile).value, artifact_version=version, software_revision=revision,
                 policy=policy.model_dump(mode="json"), test_only=True)
    return dict(sha256=fingerprint(value), software_revision=revision,
                policy_id=policy.policy_id, policy_version=policy.version, test_only=True)


def generate(data):
    """Deterministic input mutations only; this function never reads labels."""
    if not 1 <= len(data["scenarios"]) <= MAX_SCENARIOS:
        raise ValueError("Corpus count out of bounds")
    scenarios = []
    for row in data["scenarios"]:
        allowed = {"id", "version", "category", "target", "operation", "observation_patch", "context_patch", "role", "action", "numeric_variant"}
        if set(row) - allowed:
            raise ValueError("Unknown scenario definition fields")
        patch = row.get("observation_patch", {})
        observation = None if patch is None else {**deepcopy(data["base_observation"]), **deepcopy(patch)}
        context = {**data["base_context"], **row.get("context_patch", {})}
        scenarios.append(Scenario(id=row["id"], version=row["version"], source="SYNTHETIC",
            review_state="SPECIFICATION_REFERENCE", policy_id="fictional-pump-inspection", policy_version="1.0.0",
            category=row["category"], target=row["target"], operation=row["operation"],
            actor=dict(role=row.get("role", "SERVICE_AGENT"),
                tenant_id="synthetic-org-b" if row["operation"] == "CROSS_TENANT" else "synthetic-org-a",
                assigned=row["operation"] not in {"UNASSIGNED", "CROSS_TENANT"}),
            observation=observation, context=context, action=row.get("action", "prepare_invoice"),
            numeric_variant=row.get("numeric_variant", "NONE"), risk="HIGH" if row["category"] not in {"VALID", "VALID_LOWER", "VALID_UPPER", "PROVISIONAL"} else "MEDIUM",
            rationale="A restricted action must not gain authority; legitimate cases must retain their specified progression.",
            steps=("Use the isolated synthetic corpus and named candidate only.", f"Execute {row['id']} version {row['version']} via {row['target']} target {row['operation']}.", "Compare all recorded outcome dimensions against the separate fixed label.")))
    return tuple(sorted(scenarios, key=lambda item: (item.id, item.version)))


def assemble(data, labels):
    scenarios = generate(data)
    identities, semantic, labeled = set(), {}, {}
    for raw in labels["labels"]:
        label = Label.model_validate(raw)
        key = (label.scenario_id, label.scenario_version)
        if key in labeled:
            raise ValueError("Duplicate/conflicting oracle identity")
        labeled[key] = label
    for scenario in scenarios:
        key = (scenario.id, scenario.version)
        if key in identities or key not in labeled:
            raise ValueError("Duplicate scenario or missing independent label")
        identities.add(key)
        label = labeled[key]
        if scenario.target == "API" and label.expected.http_status is None:
            raise ValueError("API oracle must specify HTTP status")
        payload = scenario.model_dump(mode="json", exclude={"id", "version", "category", "steps", "risk", "rationale"})
        signature = fingerprint(payload)
        expected = canonical(label.expected.model_dump(mode="json"))
        if signature in semantic and semantic[signature] != expected:
            raise ValueError("Identical scenario inputs have conflicting labels")
        semantic[signature] = expected
    if identities != set(labeled):
        raise ValueError("Orphan oracle labels")
    return scenarios, labeled


def load_corpus():
    manifest = json.loads((CORPUS_ROOT / "manifest_v1.json").read_text(encoding="utf-8"))
    blobs = {name: (CORPUS_ROOT / name).read_bytes() for name in ("scenarios_v1.json", "labels_v1.json")}
    if any(sha256(blob).hexdigest() != manifest["files"][name] for name, blob in blobs.items()):
        raise ValueError("Reference corpus changed without its versioned manifest")
    def invalid(value):
        raise ValueError("Nonfinite JSON is forbidden; use explicit numeric mutation tags")
    data, labels = [json.loads(blobs[name], parse_constant=invalid) for name in blobs]
    if (data["corpus_id"], data["version"]) != (labels["corpus_id"], labels["version"]):
        raise ValueError("Corpus and label versions conflict")
    scenarios, oracle = assemble(data, labels)
    return scenarios, oracle, dict(id=data["corpus_id"], version=data["version"], sha256=fingerprint(manifest),
                                  count=len(scenarios), source="SYNTHETIC", runner_version=RUNNER_VERSION)

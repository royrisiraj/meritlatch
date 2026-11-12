from pathlib import Path
import subprocess
import sys


def test_pure_policy_import_and_evaluation_without_network_api_or_providers():
    script = r'''
import builtins
import json
from pathlib import Path
import socket
original_import = builtins.__import__
blocked = {"fastapi", "starlette", "uvicorn", "google", "firebase_admin", "httpx", "requests", "sqlalchemy"}
def checked_import(name, *args, **kwargs):
    if name.split(".")[0] in blocked:
        raise AssertionError("Forbidden policy dependency: " + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = checked_import
def no_connection(*args, **kwargs):
    raise AssertionError("Network unavailable")
socket.socket.connect = no_connection
socket.create_connection = no_connection
from backend.app.models import Policy
from backend.app.policy import authorize
sample = json.loads(Path("fixtures/synthetic_cases.json").read_text())
policy = Policy.model_validate_json(Path("policies/maintenance_v1.json").read_text())
decision = authorize(sample["valid_observation"], policy, sample["context"])
assert decision.max_permission == 2
assert decision.decision.value == "ALLOW"
print("Independent policy evaluation: ALLOW L2; network and API/provider imports blocked")
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[2],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ALLOW L2" in result.stdout

import json
from pathlib import Path

import pytest

from backend.app.config import load_policy

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample():
    return json.loads((ROOT / "fixtures/synthetic_cases.json").read_text(encoding="utf-8"))


@pytest.fixture
def policy():
    return load_policy(ROOT / "policies/maintenance_v1.json")


@pytest.fixture
def observation(sample):
    return sample["valid_observation"]


@pytest.fixture
def context(sample):
    return sample["context"]

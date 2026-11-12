"""Explicit local policy loading; never part of observation or model processing."""

from pathlib import Path

from pydantic import ValidationError

from .models import Policy


def load_policy(path: str | Path) -> Policy:
    try:
        return Policy.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise ValueError("Invalid policy configuration; supply a readable, valid job-specific policy JSON.") from exc

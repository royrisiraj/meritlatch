"""Explicit internal test factory. No application HTTP route imports this module."""

from pathlib import Path

from backend.app.api import create_app
from backend.app.settings import Settings


def create_test_app(database_path: Path, clock=None):
    return create_app(Settings(database_path=database_path, environment="test", allow_synthetic=True), clock=clock)

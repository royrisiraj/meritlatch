from dataclasses import dataclass
import os
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("backend/local.sqlite")
    environment: Literal["development", "test"] = "development"
    allow_synthetic: bool = False
    session_seconds: int = 3600
    challenge_seconds: int = 300
    max_challenges_per_window: int = 5

    def __post_init__(self):
        if self.environment not in {"development", "test"}:
            raise ValueError("Phase 01 supports local development/test only; production deployment is not configured.")
        if self.allow_synthetic and self.environment != "test":
            raise ValueError("Synthetic input requires an explicit internal test factory.")
        if not 1 <= self.challenge_seconds <= 600 or not 1 <= self.session_seconds <= 86400:
            raise ValueError("Invalid session or challenge lifetime.")
        if not 1 <= self.max_challenges_per_window <= 20:
            raise ValueError("Invalid challenge issuance limit.")

    @classmethod
    def from_env(cls):
        # Synthetic injection cannot be enabled through environment configuration.
        if os.getenv("SENTINEL_ALLOW_SYNTHETIC", "false").lower() != "false":
            raise ValueError("SENTINEL_ALLOW_SYNTHETIC is unsupported; use the internal test factory only.")
        return cls(database_path=Path(os.getenv("SENTINEL_DATABASE_PATH", "backend/local.sqlite")),
                   environment=os.getenv("SENTINEL_ENV", "development"))

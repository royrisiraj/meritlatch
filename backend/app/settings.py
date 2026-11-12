from dataclasses import dataclass, field
import os
import re
from pathlib import Path
from typing import Literal
from pydantic import SecretStr


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("backend/local.sqlite")
    environment: Literal["development", "test"] = "development"
    allow_synthetic: bool = False
    session_seconds: int = 3600
    challenge_seconds: int = 300
    max_challenges_per_window: int = 5
    provider_mode: Literal["DISABLED", "MOCK_AI", "LIVE_GEMINI"] = "DISABLED"
    gemini_model: str = "gemini-3.6-flash"
    gemini_api_key: SecretStr | None = field(default=None, repr=False)
    allow_billable: bool = False
    provider_timeout_seconds: float = 20.0
    provider_attempts: int = 1
    media_root: Path = Path("backend/private_media")
    max_image_bytes: int = 5 * 1024 * 1024
    max_image_pixels: int = 4_000_000
    max_image_dimension: int = 4096

    def __post_init__(self):
        if self.environment not in {"development", "test"}:
            raise ValueError("Phase 01 supports local development/test only; production deployment is not configured.")
        if self.allow_synthetic and self.environment != "test":
            raise ValueError("Synthetic input requires an explicit internal test factory.")
        if not 1 <= self.challenge_seconds <= 600 or not 1 <= self.session_seconds <= 86400:
            raise ValueError("Invalid session or challenge lifetime.")
        if not 1 <= self.max_challenges_per_window <= 20:
            raise ValueError("Invalid challenge issuance limit.")
        if self.provider_mode not in {"DISABLED", "MOCK_AI", "LIVE_GEMINI"}:
            raise ValueError("Choose DISABLED, MOCK_AI or LIVE_GEMINI explicitly.")
        if not 0 < self.provider_timeout_seconds <= 60 or not 1 <= self.provider_attempts <= 2:
            raise ValueError("Provider timeout must be <=60 seconds and attempts 1 or 2.")
        if not 1 <= self.max_image_bytes <= 10 * 1024 * 1024 or not 1 <= self.max_image_pixels <= 4_000_000 or not 1 <= self.max_image_dimension <= 8192:
            raise ValueError("Image byte/pixel/dimension limits exceed supported bounds.")
        if self.provider_mode == "LIVE_GEMINI" and (not self.gemini_api_key or not self.gemini_api_key.get_secret_value().strip() or not self.allow_billable):
            raise ValueError("LIVE_GEMINI needs GEMINI_API_KEY and explicit SENTINEL_ALLOW_BILLABLE=true; no mock fallback exists.")
        if not re.fullmatch(r"[A-Za-z0-9._/-]{1,100}", self.gemini_model):
            raise ValueError("Supply a nonblank configurable GEMINI_MODEL identifier.")

    @classmethod
    def from_env(cls):
        # Synthetic injection cannot be enabled through environment configuration.
        if os.getenv("SENTINEL_ALLOW_SYNTHETIC", "false").lower() != "false":
            raise ValueError("SENTINEL_ALLOW_SYNTHETIC is unsupported; use the internal test factory only.")
        return cls(database_path=Path(os.getenv("SENTINEL_DATABASE_PATH", "backend/local.sqlite")),
                   environment=os.getenv("SENTINEL_ENV", "development"),
                   provider_mode=os.getenv("SENTINEL_PROVIDER_MODE", "DISABLED"),
                   gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
                   gemini_api_key=SecretStr(os.environ["GEMINI_API_KEY"]) if os.getenv("GEMINI_API_KEY") else None,
                   allow_billable=os.getenv("SENTINEL_ALLOW_BILLABLE", "false").lower() == "true",
                   provider_timeout_seconds=float(os.getenv("SENTINEL_PROVIDER_TIMEOUT_SECONDS", "20")),
                   provider_attempts=int(os.getenv("SENTINEL_PROVIDER_ATTEMPTS", "1")),
                   media_root=Path(os.getenv("SENTINEL_MEDIA_ROOT", "backend/private_media")),
                   max_image_bytes=int(os.getenv("SENTINEL_MAX_IMAGE_BYTES", str(5 * 1024 * 1024))),
                   max_image_pixels=int(os.getenv("SENTINEL_MAX_IMAGE_PIXELS", "4000000")),
                   max_image_dimension=int(os.getenv("SENTINEL_MAX_IMAGE_DIMENSION", "4096")))

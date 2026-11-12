"""Private local media adapter; storage names are never supplied by the client."""

import os
from pathlib import Path
import re
import secrets
from typing import Protocol

from .errors import AppError


class MediaStorage(Protocol):
    def put(self, data: bytes) -> str: ...
    def read(self, key: str, maximum: int) -> bytes: ...
    def discard_uncommitted(self, key: str) -> None: ...


class LocalPrivateMediaStorage:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def _path(self, key):
        if not re.fullmatch(r"[a-f0-9]{64}\.bin", key):
            raise ValueError("Invalid internal storage reference")
        path = self.root / key
        if path.resolve().parent != self.root or path.is_symlink():
            raise ValueError("Unsafe internal storage reference")
        return path

    def put(self, data):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        key = secrets.token_hex(32) + ".bin"
        path = self._path(key)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
        except BaseException:
            path.unlink(missing_ok=True)  # Only this call's newly allocated file.
            raise
        return key

    def read(self, key, maximum):
        try:
            with self._path(key).open("rb") as source:
                data = source.read(maximum + 1)
            if len(data) > maximum:
                raise ValueError("Stored object exceeded its limit")
            return data
        except (OSError, ValueError):
            raise AppError(503, "MEDIA_UNAVAILABLE", "The private evidence could not be read; request operator review.") from None

    def discard_uncommitted(self, key):
        self._path(key).unlink(missing_ok=True)

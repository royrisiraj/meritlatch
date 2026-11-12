"""Bounded JPEG/PNG validation. MIME, filenames and metadata confer no trust."""

from dataclasses import dataclass, field
from hashlib import sha256
from io import BytesIO
import re
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from .errors import AppError


@dataclass(frozen=True)
class ValidatedImage:
    original: bytes = field(repr=False)
    provider_bytes: bytes = field(repr=False)
    mime_type: str
    sha256: str
    provider_sha256: str
    width: int
    height: int
    provenance: dict


def validate_image(data: bytes, declared_type: str, settings) -> ValidatedImage:
    if not data:
        raise AppError(422, "EMPTY_IMAGE", "Submit a nonempty JPEG or PNG image.")
    if len(data) > settings.max_image_bytes:
        raise AppError(413, "IMAGE_TOO_LARGE", "Use an image within the configured byte limit.")
    actual = "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg" if data.startswith(b"\xff\xd8\xff") else None
    if not actual:
        raise AppError(415, "UNSUPPORTED_MEDIA_TYPE", "Only decoded JPEG and PNG images are supported.")
    declared_type = declared_type.split(";", 1)[0].strip().lower()
    if declared_type not in {"image/jpeg", "image/png", "application/octet-stream"}:
        raise AppError(415, "UNSUPPORTED_MEDIA_TYPE", "Use image/jpeg, image/png or application/octet-stream.")
    if declared_type != "application/octet-stream" and declared_type != actual:
        raise AppError(415, "MEDIA_TYPE_MISMATCH", "The declared type does not match the image bytes.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as image:
                width, height = image.size
                if width * height > settings.max_image_pixels or max(width, height) > settings.max_image_dimension:
                    raise AppError(413, "IMAGE_DIMENSIONS_EXCEEDED", "Reduce the decoded image size to the configured limits.")
                if getattr(image, "n_frames", 1) != 1:
                    raise AppError(415, "MULTIFRAME_IMAGE_UNSUPPORTED", "Submit a single-frame JPEG or PNG; video/animation is deferred.")
                if Image.MIME.get(image.format) != actual:
                    raise AppError(415, "MEDIA_TYPE_MISMATCH", "Signature and decoder format disagree.")
                image.verify()
            with Image.open(BytesIO(data), formats=["JPEG", "PNG"]) as image:
                image.load()
                exif = image.getexif()
                claimed_time = exif.get(36867) or exif.get(306)
                provenance = dict(metadata_trust="UNTRUSTED_SUPPORTING_ONLY", exif_present=bool(exif),
                    gps_present=34853 in exif, claimed_capture_time=claimed_time if isinstance(claimed_time, str) and re.fullmatch(r"\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}", claimed_time) else "UNKNOWN")
                normalized = ImageOps.exif_transpose(image).convert("RGBA")
                background = Image.new("RGB", normalized.size, "white")
                background.paste(normalized, mask=normalized.getchannel("A"))
                output = BytesIO()
                background.save(output, format="PNG")  # Strip EXIF/GPS/text chunks before provider transmission.
                provider_bytes = output.getvalue()
                if len(provider_bytes) > 13 * 1024 * 1024:
                    raise AppError(413, "NORMALIZED_IMAGE_TOO_LARGE", "Reduce the image dimensions before analysis.")
                return ValidatedImage(data, provider_bytes, actual, sha256(data).hexdigest(),
                    sha256(provider_bytes).hexdigest(), width, height, provenance)
    except AppError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise AppError(413, "IMAGE_DIMENSIONS_EXCEEDED", "The image exceeds safe decoder limits.") from None
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, OverflowError):
        raise AppError(422, "INVALID_IMAGE", "The image could not be verified and fully decoded safely.") from None

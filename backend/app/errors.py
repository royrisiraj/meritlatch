"""Stable, redacted application failures."""


class AppError(Exception):
    def __init__(self, status: int, code: str, guidance: str):
        self.status = status
        self.code = code
        self.guidance = guidance
        super().__init__(code)


def forbidden():
    return AppError(403, "ROLE_FORBIDDEN", "Use an independently authenticated account authorized for this action.")


def not_found():
    return AppError(404, "NOT_FOUND", "Check the identifier and your tenant/job assignment.")


def conflict():
    return AppError(409, "VERSION_CONFLICT", "Reload the current case and retry with its current version.")

"""Public operational metadata only; business routes await Phase 01 authorization."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SENTINEL//LADDER", version="0.0.0", redoc_url=None)


class Health(BaseModel):
    status: Literal["ok"] = "ok"


@app.get("/healthz", response_model=Health, tags=["health"])
def healthz() -> Health:
    return Health()

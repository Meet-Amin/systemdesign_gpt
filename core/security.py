from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key_header: str = Security(API_KEY_HEADER)) -> str:
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API_KEY is not configured on the server.")
    if api_key_header == api_key:
        return api_key_header
    raise HTTPException(status_code=401, detail="Invalid or missing API key.")

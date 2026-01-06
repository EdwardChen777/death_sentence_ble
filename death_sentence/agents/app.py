from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ComposeRequest, ComposeResponse
from .settings import settings
from .openai_client import compose_with_openai


def load_scents() -> Dict[str, Any]:
    path: Path = settings.scents_path
    if not path.exists():
        raise FileNotFoundError(f"Scents JSON not found at {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


app = FastAPI(title="Etherea Scent Composer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/compose", response_model=ComposeResponse)
def compose(request: ComposeRequest) -> ComposeResponse:
    try:
        scents = load_scents()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not settings.openai_api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    try:
        result = compose_with_openai(request.sentence, scents)
        return result
    except Exception as e:
        # Surface errors for debugging; in production, sanitize
        raise HTTPException(status_code=422, detail=str(e))



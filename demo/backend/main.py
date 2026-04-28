"""FastAPI entry point for the QoverwRap demo backend."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import crypto, decode, encode, resolve, trust

app = FastAPI(
    title="QoverwRap Demo API",
    version="0.1.0",
    description=(
        "Thin REST wrapper around the QoverwRap core (encoder/decoder/crypto/resolver). "
        "Trust registry and issuer routing are application-layer policy, not part of the patent claim."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only — tighten for production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crypto.router)
app.include_router(encode.router)
app.include_router(decode.router)
app.include_router(resolve.router)
app.include_router(trust.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}

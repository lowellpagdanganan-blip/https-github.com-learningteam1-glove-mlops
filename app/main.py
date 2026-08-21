"""
FastAPI serving app (Deliverable 1).

Endpoints:
  GET  /health   -> {"status": "ok", model version + git commit}
  POST /predict  -> runs one inference row through the registered model

Design notes for the Q&A:
  * The model is loaded ONCE in the lifespan handler and stashed on app.state,
    not re-loaded per request. This is why /health can report the exact version
    that /predict will use â€” they share one loaded object.
  * Input validation is delegated entirely to Pydantic (see schemas.py). We do
    not hand-roll validation; a malformed body never reaches our handler, it is
    rejected with 422 by FastAPI before the function runs.
  * The model URI comes from env vars via model_loader, so the same image serves
    dev/staging/prod just by changing MODEL_VERSION / MODEL_ALIAS.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Request

from .features import FEATURE_NAMES
from .model_loader import LoadedModel, load_model
from .schemas import HealthResponse, PredictRequest, PredictResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model at startup and keep it on app.state for the process lifetime.
    app.state.loaded = load_model()
    yield
    app.state.loaded = None


app = FastAPI(
    title="Insulating Glove Dielectric Test - Fail Classifier",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    loaded: LoadedModel = request.app.state.loaded
    return HealthResponse(
        status="ok",
        model_name=loaded.name,
        model_version=loaded.version,
        git_commit=os.environ.get("GIT_COMMIT"),  # set in compose/CI; null locally
    )


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    loaded: LoadedModel = request.app.state.loaded

    # Build a one-row DataFrame with columns in the exact training order.
    row = payload.model_dump()
    frame = pd.DataFrame([[row[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES)

    raw = loaded.model.predict(frame)
    pred = int(raw[0])

    # Try to surface a probability if the underlying flavour exposes one.
    probability = None
    try:
        impl = loaded.model._model_impl  # sklearn pyfunc wrapper
        if hasattr(impl, "predict_proba"):
            probability = float(impl.predict_proba(frame)[0][1])
        elif hasattr(impl, "sklearn_model") and hasattr(impl.sklearn_model, "predict_proba"):
            probability = float(impl.sklearn_model.predict_proba(frame)[0][1])
    except Exception:
        probability = None  # probability is best-effort; never break a prediction

    return PredictResponse(
        prediction=pred,
        label="fail" if pred == 1 else "pass",
        probability=probability,
        model_version=loaded.version,
    )


"""Model loading. Resolves a model URI from env vars (nothing hardcoded):
  MODEL_URI      explicit path/URI -> loaded directly (used in Docker to point
                 at the mounted artifact folder, bypassing registry path lookup)
  otherwise      MODEL_NAME + (MODEL_ALIAS | MODEL_VERSION) via the registry
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import mlflow


@dataclass
class LoadedModel:
    model: object
    name: str
    version: str
    uri: str


def _resolve() -> tuple[str, str, str]:
    # Direct path/URI wins (Docker uses this to load from the mounted mlruns).
    direct = os.environ.get("MODEL_URI")
    if direct:
        name = os.environ.get("MODEL_NAME", "model")
        version = os.environ.get("MODEL_VERSION", "artifact")
        return direct, name, version

    name = os.environ.get("MODEL_NAME")
    if not name:
        raise RuntimeError("Set MODEL_URI, or MODEL_NAME with MODEL_VERSION/MODEL_ALIAS.")
    alias = os.environ.get("MODEL_ALIAS")
    version = os.environ.get("MODEL_VERSION")
    if alias:
        client = mlflow.MlflowClient()
        mv = client.get_model_version_by_alias(name, alias)
        return f"models:/{name}@{alias}", name, str(mv.version)
    if version:
        return f"models:/{name}/{version}", name, str(version)
    raise RuntimeError("Set MODEL_VERSION or MODEL_ALIAS.")


def load_model() -> LoadedModel:
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    uri, name, version = _resolve()
    model = mlflow.pyfunc.load_model(uri)
    return LoadedModel(model=model, name=name, version=version, uri=uri)

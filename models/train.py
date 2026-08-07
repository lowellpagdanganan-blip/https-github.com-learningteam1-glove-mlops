"""
Glove MLOps — Model Training with MLflow Tracking
MAIDA 211 · Milestone 2 · Deliverable 1

Reproduces the Milestone 1 candidate (SVM + Random Oversampling) under MLflow
experiment tracking, running on top of the Milestone 1 pipeline's clean output.

Data is produced by the Milestone 1 pipeline functions (_extract -> _validate ->
_load in dags/your_pipeline.py); this script reads the resulting clean artifact.

Feature engineering (Milestone 1 framing, Table 2) happens here, not in the data
pipeline, so feature logic evolves independently of the data contract:

    Usage_Rate     = Number_of_Usage / (Age_as_of_Test + 0.25)
    Liveline_Ratio = Liveline_Usage / (Liveline_Usage + PreArrange_Usage)

Leakage_mA is excluded at every stage — it directly determines Test_Result and
would leak the label.

Public functions (imported by the test suite):
    engineer_features(df) -> df
    make_xy(df)           -> (X, y)          y: Fail=1, Pass=0
    build_pipeline(...)   -> imblearn.Pipeline
    evaluate(model, X, y) -> dict[str, float]
    train(df, ...)        -> TrainResult      (no MLflow side effects)
    load_clean_dataset()  -> df               (runs the M1 pipeline)
    run_training(...)     -> TrainResult      (logs + registers to MLflow)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

# ---------------------------------------------------------------------------
# Feature definitions (Milestone 1 framing, Table 2)
# ---------------------------------------------------------------------------

TARGET = "Test_Result"
POSITIVE_LABEL = "Fail"  # the rare, safety-critical class -> encoded as 1

CATEGORICAL_FEATURES = ["LeftRight", "Area", "Brand", "Size", "Make", "Test_Quarter"]
NUMERIC_FEATURES = [
    "Test_Year",
    "Number_of_Owners",
    "Age_as_of_Test",
    "Usage_Rate",
    "Liveline_Ratio",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

# Never a feature: direct label determinant / label itself.
LEAKY_COLUMNS = ["Leakage_mA", TARGET]


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the two engineered features from the framing doc. Non-mutating."""
    out = df.copy()
    out["Usage_Rate"] = out["Number_of_Usage"] / (out["Age_as_of_Test"] + 0.25)
    denom = out["Liveline_Usage"] + out["PreArrange_Usage"]
    # Guard the divide-by-zero case (a glove with no recorded usage).
    out["Liveline_Ratio"] = (out["Liveline_Usage"] / denom).where(denom > 0, 0.0)
    return out


def make_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) with y encoded Fail=1 / Pass=0."""
    engineered = engineer_features(df)
    X = engineered[FEATURES]
    y = (engineered[TARGET] == POSITIVE_LABEL).astype(int)
    return X, y


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


def build_pipeline(
    C: float = 1.0,
    kernel: str = "rbf",
    gamma: str = "scale",
    oversample_strategy: str = "auto",
    random_state: int = 42,
) -> ImbPipeline:
    """Preprocess -> Random Oversample (train folds only) -> SVM."""
    preprocess = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    return ImbPipeline(
        steps=[
            ("preprocess", preprocess),
            (
                "oversample",
                RandomOverSampler(
                    sampling_strategy=oversample_strategy, random_state=random_state
                ),
            ),
            (
                "svm",
                SVC(
                    C=C,
                    kernel=kernel,
                    gamma=gamma,
                    probability=True,
                    random_state=random_state,
                ),
            ),
        ]
    )


def evaluate(model: ImbPipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
    """Compute business-relevant metrics. Fail (=1) is the positive class."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "fail_recall": recall_score(y_test, y_pred, pos_label=1, zero_division=0),
        "fail_precision": precision_score(y_test, y_pred, pos_label=1, zero_division=0),
        "fail_f1": f1_score(y_test, y_pred, pos_label=1, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_proba),
    }


@dataclass
class TrainResult:
    model: ImbPipeline
    metrics: dict[str, float]
    params: dict[str, object]
    X_test: pd.DataFrame
    y_test: pd.Series


def train(
    df: pd.DataFrame,
    C: float = 1.0,
    kernel: str = "rbf",
    gamma: str = "scale",
    oversample_strategy: str = "auto",
    test_size: float = 0.25,
    random_state: int = 42,
) -> TrainResult:
    """Fit the candidate on `df` and evaluate on a stratified holdout. No MLflow."""
    X, y = make_xy(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    model = build_pipeline(
        C=C,
        kernel=kernel,
        gamma=gamma,
        oversample_strategy=oversample_strategy,
        random_state=random_state,
    )
    model.fit(X_train, y_train)
    metrics = evaluate(model, X_test, y_test)
    params = {
        "C": C,
        "kernel": kernel,
        "gamma": gamma,
        "oversample_strategy": oversample_strategy,
        "test_size": test_size,
        "random_state": random_state,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    return TrainResult(model, metrics, params, X_test, y_test)


# ---------------------------------------------------------------------------
# Data loading — runs the Milestone 1 pipeline and reads its clean artifact
# ---------------------------------------------------------------------------


def _ensure_airflow_importable() -> None:
    """Install a no-op stand-in for airflow.decorators if Airflow can't init.

    dags/your_pipeline.py imports Airflow at module top; Airflow does not run on
    Windows. The pipeline functions are plain Python, so a lightweight stub lets
    training import them anywhere (mirrors conftest.py).
    """
    import types

    try:
        import airflow.decorators  # noqa: F401  (real Airflow available)
        return
    except Exception:
        pass

    airflow_mod = types.ModuleType("airflow")
    dec_mod = types.ModuleType("airflow.decorators")

    def _dag(*args, **kwargs):
        def decorator(func):
            def wrapper(*a, **k):
                return None

            return wrapper

        return decorator

    def _task(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    dec_mod.dag = _dag
    dec_mod.task = _task
    airflow_mod.decorators = dec_mod
    sys.modules["airflow"] = airflow_mod
    sys.modules["airflow.decorators"] = dec_mod


def load_clean_dataset() -> pd.DataFrame:
    """Run the M1 pipeline (extract -> validate -> load) and read the result."""
    # Ensure the repo root is importable when train.py runs as a script.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    _ensure_airflow_importable()
    from dags.your_pipeline import _extract, _load, _validate

    artifact = _load(_validate(_extract()))
    print(f"[train] Loaded clean dataset: {artifact}")
    return pd.read_csv(artifact)


# ---------------------------------------------------------------------------
# MLflow orchestration (Deliverable 1)
# ---------------------------------------------------------------------------

EXPERIMENT_NAME = "glove_fail_prediction"
REGISTERED_MODEL_NAME = "glove_fail_classifier"
# URI comes from the environment, never hardcoded. Local SQLite backend is
# acceptable per the milestone brief and is required for the Model Registry.
DEFAULT_TRACKING_URI = "sqlite:///mlflow/mlflow.db"


def run_training(
    df: pd.DataFrame | None = None,
    register: bool = True,
    **train_kwargs,
) -> TrainResult:
    """Train with MLflow tracking; log params/metrics/model and register a version."""
    import mlflow
    import mlflow.sklearn

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"[train] MLflow tracking URI: {tracking_uri}")

    if df is None:
        df = load_clean_dataset()

    # Autologging captures sklearn params/metrics/model automatically; we
    # augment it below with manual log_param / log_metric calls (required).
    mlflow.sklearn.autolog(log_models=False, silent=True)

    with mlflow.start_run() as run:
        result = train(df, **train_kwargs)

        # --- manual logging that autolog does NOT capture ------------------
        mlflow.log_param("positive_label", POSITIVE_LABEL)
        mlflow.log_param("engineered_features", ",".join(["Usage_Rate", "Liveline_Ratio"]))
        mlflow.log_param("excluded_leaky_columns", ",".join(LEAKY_COLUMNS))
        for name, value in result.params.items():
            mlflow.log_param(name, value)
        for name, value in result.metrics.items():
            mlflow.log_metric(name, float(value))
        # fail_recall is our primary selection metric -> tag it explicitly.
        mlflow.set_tag("primary_metric", "fail_recall")

        # Register the trained model to the Model Registry with a version.
        signature = mlflow.models.infer_signature(
            result.X_test, result.model.predict(result.X_test)
        )
        mlflow.sklearn.log_model(
            sk_model=result.model,
            name="model",
            signature=signature,
            input_example=result.X_test.head(3),
            registered_model_name=REGISTERED_MODEL_NAME if register else None,
        )
        print(f"[train] Logged run {run.info.run_id}")
        print(f"[train] Metrics: {result.metrics}")

    return result


if __name__ == "__main__":
    run_training()

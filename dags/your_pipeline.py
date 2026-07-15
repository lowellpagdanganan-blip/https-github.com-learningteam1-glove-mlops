"""
Glove MLOps — Airflow DAG
MAIDA 211 Milestone 1

Three tasks:
  1. extract  — read raw CSV from data/raw/
  2. validate — enforce Pandera schema (pipeline fails on bad data)
  3. load     — write versioned clean artifact to data/processed/
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check

from airflow.decorators import dag, task

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

GLOVE_TEST_SCHEMA = DataFrameSchema(
    {
        "LeftRight": Column(str, nullable=False),
        "Area": Column(str, nullable=False),
        "Test_Year": Column(int, Check.ge(2000), nullable=False),
        "Test_Quarter": Column(str, Check.isin(["Q1", "Q2", "Q3", "Q4"]), nullable=False),
        "Brand": Column(str, nullable=False),
        "Size": Column(str, nullable=False),
        "Make": Column(str, nullable=False),
        "Number_of_Owners": Column(int, Check.ge(1), nullable=False),
        "Age_as_of_Test": Column(float, Check.ge(0.0), nullable=False),
        "Liveline_Usage": Column(float, Check.ge(0.0), nullable=False),
        "PreArrange_Usage": Column(float, Check.ge(0.0), nullable=False),
        "Number_of_Usage": Column(float, Check.ge(0.0), nullable=False),
        "Leakage_mA": Column(float, Check.ge(0.0), nullable=False),
        "Test_Result": Column(
            str,
            Check.isin(["Pass", "Fail"]),
            nullable=False,
        ),
    },
    coerce=True,
    strict=False,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

RAW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "raw", "glove_test_extract.csv"
)
PROCESSED_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "processed"
)


# ---------------------------------------------------------------------------
# DAG
# ---------------------------------------------------------------------------


@dag(
    dag_id="glove_test_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["maida211", "milestone1"],
)
def glove_test_pipeline():
    """Extract → Validate → Load pipeline for insulating glove test data."""

    @task()
    def extract() -> str:
        raw_path = os.path.abspath(RAW_PATH)
        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Raw data not found at {raw_path}")
        df = pd.read_csv(raw_path)
        print(f"[extract] Loaded {len(df)} rows from {raw_path}")
        return raw_path

    @task()
    def validate(raw_path: str) -> str:
        df = pd.read_csv(raw_path)
        print(f"[validate] Validating {len(df)} rows ...")
        validated_df = GLOVE_TEST_SCHEMA.validate(df, lazy=True)
        print(f"[validate] All {len(validated_df)} rows passed schema checks.")
        tmp_path = raw_path.replace(".csv", "_validated_tmp.csv")
        validated_df.to_csv(tmp_path, index=False)
        return tmp_path

    @task()
    def load(validated_path: str) -> str:
        os.makedirs(os.path.abspath(PROCESSED_DIR), exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = os.path.abspath(
            os.path.join(PROCESSED_DIR, f"clean_glove_tests_{ts}.csv")
        )
        df = pd.read_csv(validated_path)
        df.to_csv(output_path, index=False)
        if os.path.exists(validated_path):
            os.remove(validated_path)
        print(f"[load] Pipeline succeeded. Clean artifact: {output_path}")
        return output_path

    raw = extract()
    validated = validate(raw)
    load(validated)


glove_test_pipeline()
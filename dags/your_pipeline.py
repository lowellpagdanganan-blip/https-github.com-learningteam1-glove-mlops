"""
Insulating Glove Test Data Pipeline
====================================

MAIDA 211 - Milestone 1

Business context: this pipeline ingests periodic dielectric test results for
rubber insulating gloves (PPE used by field electrical crews), validates the
extract against a data-quality contract, and writes a versioned clean
artifact that downstream model training (Milestone 2+) will consume.

Orchestrator: Prefect (chosen as the "equivalent orchestrated pipeline"
alternative to Airflow -- our group did not have a shared Airflow
environment, and Prefect gives the same task/flow/DAG semantics with a
single `uv run` entry point and no scheduler service to stand up).

Minimum DAG (3 tasks):
    1. extract   - pull the raw test-result extract from the file system
    2. validate  - enforce the Pandera schema; pipeline FAILS on bad data
    3. load      - write a versioned clean output artifact

Run:
    uv run python dags/your_pipeline.py
"""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pandera as pa
from pandera import Check, Column, DataFrameSchema
from prefect import flow, task

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = REPO_ROOT / "data" / "raw" / "glove_test_extract.csv"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# Data quality contract (Pandera)
# ---------------------------------------------------------------------------
# Values below reflect the business rules confirmed with the safety team:
#   - Leakage_mA cannot be negative (physically impossible reading)
#   - Test_Result is a strict Pass/Fail classification, no other categories
#   - Area is limited to the three operating regions currently in service
#   - Age_as_of_Test and usage counters cannot be negative
GLOVE_TEST_SCHEMA = DataFrameSchema(
    {
        "LeftRight": Column(str, Check.isin(["Left", "Right"])),
        "Area": Column(str, Check.isin(["North", "Central", "South"])),
        "Test_Year": Column(int, Check.in_range(2000, 2100)),
        "Test_Quarter": Column(str, Check.isin(["Q1", "Q2", "Q3", "Q4"])),
        "Brand": Column(str, Check.isin(["3M", "CATU", "Honeywell", "Novax"])),
        "Size": Column(int, Check.isin([7, 8, 9, 10])),
        "Make": Column(str, Check.isin(["Composite", "EPDM", "Latex Rubber"])),
        "Number_of_Owners": Column(int, Check.ge(0)),
        "Age_as_of_Test": Column(float, Check.ge(0)),
        "Liveline_Usage": Column(int, Check.ge(0)),
        "PreArrange_Usage": Column(int, Check.ge(0)),
        "Number_of_Usage": Column(int, Check.ge(0)),
        "Leakage_mA": Column(float, Check.ge(0)),
        "Test_Result": Column(str, Check.isin(["Pass", "Fail"])),
    },
    strict=False,
    coerce=False,
)


# ---------------------------------------------------------------------------
# Task 1: Extract
# ---------------------------------------------------------------------------
@task(name="extract", retries=1, retry_delay_seconds=5)
def extract(source_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Pull the raw glove test extract from the file system.

    In production this file is exported from the safety team's test-bench
    LIMS system. For this repo we ship a synthetic sample with the same
    schema and distribution shape (no proprietary or production data is
    committed).
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Raw extract not found at {source_path}")

    df = pd.read_csv(source_path)
    logger.info("Extracted %d rows, %d columns from %s", *df.shape, source_path)
    return df


# ---------------------------------------------------------------------------
# Task 2: Validate
# ---------------------------------------------------------------------------
@task(name="validate")
def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce the data quality contract. Raises and stops the pipeline
    if the extract does not conform -- this is not a warning, it is a gate.
    """
    try:
        validated = GLOVE_TEST_SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as err:
        logger.error("Schema validation failed with %d failure cases", len(err.failure_cases))
        logger.error("\n%s", err.failure_cases.to_string())
        raise

    logger.info("Validation passed: %d rows conform to schema", len(validated))
    return validated


# ---------------------------------------------------------------------------
# Task 3: Load
# ---------------------------------------------------------------------------
@task(name="load")
def load(df: pd.DataFrame, output_dir: Path = PROCESSED_DIR) -> Path:
    """Write the clean dataset as a versioned artifact (UTC run-id timestamp
    in the filename) so downstream consumers can pin to a specific version.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"clean_glove_tests_{run_id}.csv"
    df.to_csv(output_path, index=False)

    logger.info("Wrote versioned clean artifact to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Flow (DAG)
# ---------------------------------------------------------------------------
@flow(name="insulating-glove-data-pipeline")
def glove_data_pipeline(source_path: Path = RAW_DATA_PATH) -> Path:
    raw_df = extract(source_path)
    clean_df = validate(raw_df)
    output_path = load(clean_df)
    return output_path


if __name__ == "__main__":
    try:
        result_path = glove_data_pipeline()
        print(f"Pipeline succeeded. Clean artifact: {result_path}")
    except Exception as exc:  # noqa: BLE001 - top-level CLI failure boundary
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        sys.exit(1)

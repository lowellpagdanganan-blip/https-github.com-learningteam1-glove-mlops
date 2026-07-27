"""Basic tests for the Milestone 1 data pipeline.

Milestone 2 will expand this into the full 6+ test / 3-category suite
(data validation, model quality, integration). For M1 we confirm the
three pipeline tasks behave correctly in isolation and the quality gate
actually gates.
"""

from __future__ import annotations

import os

import pandas as pd
import pandera as pa
import pytest

import dags.your_pipeline as pipeline
from dags.your_pipeline import (
    GLOVE_TEST_SCHEMA,
)
from dags.your_pipeline import (
    _extract as extract,
)
from dags.your_pipeline import (
    _load as load,
)
from dags.your_pipeline import (
    _validate as validate,
)

VALID_ROW = {
    "LeftRight": "Left",
    "Area": "North",
    "Test_Year": 2024,
    "Test_Quarter": "Q1",
    "Brand": "3M",
    "Size": 8,
    "Make": "EPDM",
    "Number_of_Owners": 2,
    "Age_as_of_Test": 1.25,
    "Liveline_Usage": 100,
    "PreArrange_Usage": 50,
    "Number_of_Usage": 150,
    "Leakage_mA": 1.2,
    "Test_Result": "Pass",
}


def make_df(overrides: dict | None = None, n: int = 3) -> pd.DataFrame:
    row = {**VALID_ROW, **(overrides or {})}
    return pd.DataFrame([row for _ in range(n)])


def test_extract_reads_raw_csv(tmp_path, monkeypatch):
    raw_csv = tmp_path / "raw.csv"
    make_df().to_csv(raw_csv, index=False)
    monkeypatch.setattr(pipeline, "RAW_PATH", str(raw_csv))
    result_path = extract()
    df = pd.read_csv(result_path)
    assert not df.empty
    assert "Test_Result" in df.columns


def test_extract_raises_on_missing_file(tmp_path, monkeypatch):
    missing = tmp_path / "does_not_exist.csv"
    monkeypatch.setattr(pipeline, "RAW_PATH", str(missing))
    with pytest.raises(FileNotFoundError):
        extract()


def test_validate_passes_clean_data(tmp_path):
    raw_csv = tmp_path / "clean.csv"
    df = make_df()
    df.to_csv(raw_csv, index=False)
    validated_path = validate(str(raw_csv))
    validated = pd.read_csv(validated_path)
    assert len(validated) == len(df)


def test_validate_rejects_negative_leakage(tmp_path):
    raw_csv = tmp_path / "bad.csv"
    make_df({"Leakage_mA": -1.0}).to_csv(raw_csv, index=False)
    with pytest.raises(pa.errors.SchemaErrors):
        validate(str(raw_csv))


def test_validate_rejects_invalid_test_result_category(tmp_path):
    raw_csv = tmp_path / "bad.csv"
    make_df({"Test_Result": "Unknown"}).to_csv(raw_csv, index=False)
    with pytest.raises(pa.errors.SchemaErrors):
        validate(str(raw_csv))


def test_validate_rejects_out_of_domain_area(tmp_path):
    raw_csv = tmp_path / "bad.csv"
    make_df({"Area": "West"}).to_csv(raw_csv, index=False)
    with pytest.raises(pa.errors.SchemaErrors):
        validate(str(raw_csv))


def test_load_writes_versioned_artifact(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", str(processed_dir))
    validated_csv = tmp_path / "validated.csv"
    df = make_df()
    df.to_csv(validated_csv, index=False)
    output_path = load(str(validated_csv))
    assert os.path.exists(output_path)
    assert "clean_glove_tests_" in os.path.basename(output_path)
    reloaded = pd.read_csv(output_path)
    assert len(reloaded) == len(df)


def test_schema_is_not_strict_to_allow_future_columns():
    # strict=False was a deliberate choice: new sensor fields shouldn't
    # break the pipeline until we explicitly add them to the contract
    assert GLOVE_TEST_SCHEMA.strict is False

"""Basic tests for the Milestone 1 data pipeline.

Milestone 2 will expand this into the full 6+ test / 3-category suite
(data validation, model quality, integration). For M1 we confirm the
three pipeline tasks behave correctly in isolation and the quality gate
actually gates.
"""

from __future__ import annotations

import pandas as pd
import pandera as pa
import pytest

from dags.your_pipeline import GLOVE_TEST_SCHEMA, extract, load, validate

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


def test_extract_reads_raw_csv():
    df = extract.fn()
    assert not df.empty
    assert "Test_Result" in df.columns


def test_extract_raises_on_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError):
        extract.fn(missing)


def test_validate_passes_clean_data():
    df = make_df()
    validated = validate.fn(df)
    assert len(validated) == len(df)


def test_validate_rejects_negative_leakage():
    df = make_df({"Leakage_mA": -1.0})
    with pytest.raises(pa.errors.SchemaErrors):
        validate.fn(df)


def test_validate_rejects_invalid_test_result_category():
    df = make_df({"Test_Result": "Unknown"})
    with pytest.raises(pa.errors.SchemaErrors):
        validate.fn(df)


def test_validate_rejects_out_of_domain_area():
    df = make_df({"Area": "West"})
    with pytest.raises(pa.errors.SchemaErrors):
        validate.fn(df)


def test_load_writes_versioned_artifact(tmp_path):
    df = make_df()
    output_path = load.fn(df, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.parent == tmp_path
    # filename must carry a run-id / timestamp for version tracking
    assert "clean_glove_tests_" in output_path.name

    reloaded = pd.read_csv(output_path)
    assert len(reloaded) == len(df)


def test_schema_is_not_strict_to_allow_future_columns():
    # strict=False was a deliberate choice: new sensor fields shouldn't
    # break the pipeline until we explicitly add them to the contract
    assert GLOVE_TEST_SCHEMA.strict is False

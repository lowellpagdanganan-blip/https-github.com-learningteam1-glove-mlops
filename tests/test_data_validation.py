"""Deliverable 2a — data validation tests.

These run against the Pandera schema (GLOVE_TEST_SCHEMA) defined in Milestone 1,
exercised through the pipeline's _validate() stage. _validate reads a CSV path,
enforces the schema (lazy), and writes a validated temp file. We confirm the
schema REJECTS bad data (wrong types, out-of-range values, missing columns) and
lets clean data through.
"""

from __future__ import annotations

import os

import pandas as pd
import pandera as pa
import pytest

from dags.your_pipeline import _validate

SchemaError = (pa.errors.SchemaError, pa.errors.SchemaErrors)

# A single row that satisfies every check in GLOVE_TEST_SCHEMA.
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


def write_csv(tmp_path, overrides: dict | None = None, drop: list | None = None, n: int = 4):
    """Write an n-row CSV (with optional field overrides / dropped columns)."""
    row = {**VALID_ROW, **(overrides or {})}
    df = pd.DataFrame([row for _ in range(n)])
    if drop:
        df = df.drop(columns=drop)
    path = str(tmp_path / "extract.csv")
    df.to_csv(path, index=False)
    return path


# --- valid data passes -----------------------------------------------------


def test_valid_data_passes(tmp_path):
    validated_path = _validate(write_csv(tmp_path))
    assert os.path.exists(validated_path)
    assert len(pd.read_csv(validated_path)) == 4


# --- rejection: out-of-range values ----------------------------------------


def test_rejects_negative_leakage(tmp_path):
    # A negative leakage-current reading is physically impossible.
    with pytest.raises(SchemaError):
        _validate(write_csv(tmp_path, {"Leakage_mA": -0.5}))


def test_rejects_zero_owners_out_of_range(tmp_path):
    # Number_of_Owners must be >= 1.
    with pytest.raises(SchemaError):
        _validate(write_csv(tmp_path, {"Number_of_Owners": 0}))


# --- rejection: invalid category -------------------------------------------


def test_rejects_invalid_test_result_label(tmp_path):
    with pytest.raises(SchemaError):
        _validate(write_csv(tmp_path, {"Test_Result": "Maybe"}))


def test_rejects_out_of_domain_area(tmp_path):
    with pytest.raises(SchemaError):
        _validate(write_csv(tmp_path, {"Area": "West"}))


# --- rejection: wrong type -------------------------------------------------


def test_rejects_non_numeric_test_year(tmp_path):
    # coerce=True still cannot turn a non-numeric string into an int.
    with pytest.raises(SchemaError):
        _validate(write_csv(tmp_path, {"Test_Year": "not_a_year"}))


# --- rejection: missing required column ------------------------------------


def test_rejects_missing_required_column(tmp_path):
    with pytest.raises(SchemaError):
        _validate(write_csv(tmp_path, drop=["Leakage_mA"]))

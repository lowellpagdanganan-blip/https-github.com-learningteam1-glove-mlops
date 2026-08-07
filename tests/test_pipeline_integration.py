"""Deliverable 2c — integration test.

Runs the full Extract -> Validate -> Load pipeline end-to-end against a small
synthetic dataset and verifies the versioned output artifact is produced and
well-formed. RAW_PATH and PROCESSED_DIR are monkeypatched to temp locations so
_extract() reads the synthetic file and _load() writes into the temp dir.
"""

from __future__ import annotations

import os

import pandas as pd

import dags.your_pipeline as pipeline
from dags.your_pipeline import GLOVE_TEST_SCHEMA, _extract, _load, _validate

EXPECTED_COLUMNS = list(GLOVE_TEST_SCHEMA.columns.keys())

SYNTHETIC_ROWS = [
    {
        "LeftRight": "Left", "Area": "North", "Test_Year": 2024, "Test_Quarter": "Q1",
        "Brand": "3M", "Size": 9, "Make": "EPDM", "Number_of_Owners": 1,
        "Age_as_of_Test": 0.5, "Liveline_Usage": 40, "PreArrange_Usage": 20,
        "Number_of_Usage": 60, "Leakage_mA": 1.1, "Test_Result": "Pass",
    },
    {
        "LeftRight": "Right", "Area": "South", "Test_Year": 2023, "Test_Quarter": "Q3",
        "Brand": "CATU", "Size": 10, "Make": "Composite", "Number_of_Owners": 3,
        "Age_as_of_Test": 2.0, "Liveline_Usage": 300, "PreArrange_Usage": 200,
        "Number_of_Usage": 500, "Leakage_mA": 2.8, "Test_Result": "Fail",
    },
]


def test_pipeline_end_to_end_produces_artifact(tmp_path, monkeypatch):
    # Arrange: synthetic raw extract + temp output dir.
    raw = tmp_path / "synthetic_raw.csv"
    out_dir = tmp_path / "processed"
    pd.DataFrame(SYNTHETIC_ROWS).to_csv(raw, index=False)
    monkeypatch.setattr(pipeline, "RAW_PATH", str(raw))
    monkeypatch.setattr(pipeline, "PROCESSED_DIR", str(out_dir))

    # Act: run the full pipeline (extract -> validate -> load).
    artifact = _load(_validate(_extract()))

    # Assert: a versioned artifact exists, is well-formed, matches the contract.
    assert os.path.exists(artifact)
    assert os.path.basename(artifact).startswith("clean_glove_tests_")
    assert artifact.endswith(".csv")

    reloaded = pd.read_csv(artifact)
    assert len(reloaded) == len(SYNTHETIC_ROWS)
    assert list(reloaded.columns) == EXPECTED_COLUMNS

# Insulating Glove Test Data Pipeline

**MAIDA 211 — AI and Analytics Special Topics — Milestone 1**

## Project and Model

Field electrical crews wear rubber insulating gloves as primary protection against electric shock. Regulations (ASTM F496 / OSHA) require these gloves to be periodically dielectric-tested; a glove that leaks more than 3.00 mA under test fails and must be pulled from service. Today, test results are exported from the test-bench system into a spreadsheet and reviewed manually — there is no model and no automated pipeline. The eventual model (built in later milestones) will predict whether a glove is likely to Pass or Fail its next test from its usage history (age, number of usage cycles, number of owners, brand/material), so the safety team can proactively flag and replace high-risk gloves before they fail a live test, instead of only finding out at test time. This repository implements Milestone 1: the data pipeline that reads the raw test-result extract, enforces a data-quality contract, and writes a clean, versioned artifact for the modeling work in Milestone 2.

## Repository Structure

glove-mlops/
├── dags/
│   ├── __init__.py
│   └── your_pipeline.py
├── data/
│   ├── raw/
│   │   └── glove_test_extract.csv
│   └── processed/
├── tests/
│   └── test_pipeline.py
├── pyproject.toml
├── .pre-commit-config.yaml
└── README.md

## Running the Pipeline

Requires Python 3.11+ and uv (https://docs.astral.sh/uv/).

### Install dependencies
uv sync --extra dev

### Run the pipeline
uv run python dags/your_pipeline.py

### Run tests
uv run pytest tests/ -v

### Lint check
uv run ruff check .

## Output Artifact

On success, the pipeline writes a clean CSV to data/processed/ with a UTC timestamp in the filename:

data/processed/clean_glove_tests_<UTC-timestamp>.csv

For example:

data/processed/clean_glove_tests_20260715T140212Z.csv

The output file contains the same 14 columns as the raw extract (data/raw/glove_test_extract.csv) but is guaranteed to pass every check in GLOVE_TEST_SCHEMA — negative leakage values, invalid Test_Result entries, and unrecognized Area codes are all rejected before the file is written. If validation fails, the pipeline exits non-zero and prints the Pandera failure report instead of producing an artifact.
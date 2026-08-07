
# Insulating Glove Test Data Pipeline

**MAIDA 211 — AI and Analytics Special Topics — Milestone 1**

## Project and Model

Field electrical crews wear rubber insulating gloves as primary protection against electric shock. Regulations (ASTM F496 / OSHA) require these gloves to be periodically dielectric-tested; a glove that leaks more than 3.00 mA under test fails and must be pulled from service. Today, test results are exported from the test-bench system into a spreadsheet and reviewed manually — there is no model and no automated pipeline. The eventual model (built in later milestones) will predict whether a glove is likely to Pass or Fail its next test from its usage history (age, number of usage cycles, number of owners, brand/material), so the safety team can proactively flag and replace high-risk gloves before they fail a live test, instead of only finding out at test time. This repository implements Milestone 1: the data pipeline that reads the raw test-result extract, enforces a data-quality contract, and writes a clean, versioned artifact for the modeling work in Milestone 2.

## Repository Structure

```
glove-mlops/
├── .github/
│   └── workflows/
│       └── ci.yml              # lint + test + coverage, runs on push/PR
├── dags/
│   ├── __init__.py
│   └── your_pipeline.py
├── models/
│   ├── __init__.py
│   └── train.py                 # feature engineering, SVM training, MLflow logging
├── data/
│   └── raw/
│       └── glove_test_extract.csv
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_data_validation.py       # Deliverable 2a
│   ├── test_model_quality.py         # Deliverable 2b
│   └── test_pipeline_integration.py  # Deliverable 2c
├── conftest.py            # cross-platform Airflow import shim for tests
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml     # includes an `mlflow` tracking server service
├── pyproject.toml
├── .env.example           # copy to .env and fill in secrets (.env is gitignored)
└── README.md
```

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

---

# Milestone 2 — MLflow Tracking, Testing & CI

Milestone 2 adds three MLOps layers on top of the Milestone 1 pipeline:
experiment tracking (MLflow), an automated test suite (pytest), and CI
(GitHub Actions).

## Install

Same environment as Milestone 1 (Python 3.11+, `uv`), with a few new
dependencies (`scikit-learn`, `imbalanced-learn`, `mlflow`) already declared
in `pyproject.toml`.

```bash
uv sync --extra dev
```

## Running MLflow tracking

The tracking server runs in Docker with a SQLite backend (no external
services required):

```bash
docker compose up mlflow
```

This starts the MLflow UI at **http://localhost:5000**.

By default, `models/train.py` points at `sqlite:///mlflow/mlflow.db`, so it
will also work without Docker if you just want to log locally. To point at
the Dockerized server instead, set the tracking URI via environment variable:

```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
```

Then run a training run (this first executes the Milestone 1 pipeline to
produce a clean dataset, then trains and logs to MLflow):

```bash
uv run python models/train.py
```

Each run logs to the `glove_fail_prediction` experiment:
- **Params:** model hyperparameters (`C`, `kernel`, `gamma`, oversampling
  strategy, split sizes) plus pipeline config (engineered features, excluded
  leaky columns)
- **Metrics:** accuracy, fail-class precision/recall/F1, ROC-AUC
- **Model:** registered to the Model Registry as `glove_fail_classifier`
  with an incrementing version number

Open http://localhost:5000, select the `glove_fail_prediction` experiment,
and open the most recent run to see the logged params/metrics and the
linked registered model version.

## Running tests

```bash
uv run pytest --cov=. --cov-report=term-missing
```

19 tests across three categories:
- **Data validation** (`test_data_validation.py`) — confirms the Pandera
  schema rejects bad data (negative leakage, invalid categories, wrong
  types, missing columns) and passes valid data through
- **Model quality** (`test_model_quality.py`) — trains the candidate model
  and asserts fail-class F1 and ROC-AUC clear defined thresholds on a
  stratified holdout, and that predictions are well-formed
- **Integration** (`test_pipeline_integration.py`) — runs Extract → Validate
  → Load end-to-end on synthetic data and checks the output artifact

## CI

`.github/workflows/ci.yml` runs on every push to `main` and every pull
request: installs `uv`, lints with `ruff`, and runs the full test suite
with coverage. All checks must pass before merging.

Latest CI run: https://github.com/lowellpagdanganan-blip/https-github.com-learningteam1-glove-mlops/actions/runs/30488033013



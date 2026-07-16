# Insulating Glove Test Data Pipeline

**MAIDA 211 — AI and Analytics Special Topics — Milestone 1**

## Project \& Model

Field electrical crews wear rubber insulating gloves as primary protection
against electric shock. Regulations (ASTM F496 / OSHA) require these gloves
to be periodically dielectric-tested; a glove that leaks more than 3.00 mA
under test fails and must be pulled from service. Today, test results are
exported from the test-bench system into a spreadsheet and reviewed
manually — there is no model and no automated pipeline. The eventual model
(built in later milestones) will predict whether a glove is likely to
**Pass or Fail** its next test from its usage history (age, number of
usage cycles, number of owners, brand/material), so the safety team can
proactively flag and replace high-risk gloves *before* they fail a live
test, instead of only finding out at test time.

This repository implements **Milestone 1**: the data pipeline that reads
the raw test-result extract, enforces a data-quality contract, and writes
a clean, versioned artifact for the modeling work in Milestone 2.

## Repository Structure

```
glove-mlops/
├── dags/
│   ├── \_\_init\_\_.py
│   └── your\_pipeline.py      # extract -> validate -> load (Prefect flow)
├── data/
│   ├── raw/
│   │   └── glove\_test\_extract.csv   # synthetic sample, same schema as production extract
│   └── processed/                   # versioned clean output lands here (gitignored)
├── tests/
│   └── test\_pipeline.py
├── pyproject.toml
├── .pre-commit-config.yaml
└── README.md
```

## Orchestrator note

The spec defaults to Airflow but explicitly allows an equivalent
orchestrator when it fits the project better. Our group used **Prefect**:
no shared Airflow environment to stand up, but the same task/flow (DAG)
semantics — `@task` for each pipeline step, `@flow` composing them, a
single `uv run` entry point, retries, and structured logging.

## Pipeline

1. **Extract** — reads `data/raw/glove\_test\_extract.csv` (synthetic sample
mirroring the real test-bench export; no proprietary or production
data is committed to this repo).
2. **Validate** — runs a Pandera schema (`GLOVE\_TEST\_SCHEMA` in
`dags/your\_pipeline.py`) that enforces, among other things: leakage
current can't be negative, `Test\_Result` must be `Pass`/`Fail`, and
`Area` must be one of the three regions currently in service. **The
pipeline raises and stops if the data doesn't conform** — this is not
a warning.
3. **Load** — writes the validated data to
`data/processed/clean\_glove\_tests\_<UTC-timestamp>.csv`, so every run
produces its own versioned artifact.

## How to run

Requires Python 3.11+ and [`uv`](https://docs.astral.sh/uv/).

```bash
# install dependencies
uv sync --extra dev

# run the pipeline
uv run python dags/your\_pipeline.py

# run tests
uv run pytest tests/ -v --cov=dags

# lint
uv run ruff check .
```

If you don't use `uv`, a plain virtualenv works too:

```bash
python3 -m venv .venv \&\& source .venv/bin/activate
pip install -e ".\[dev]"
python dags/your\_pipeline.py
pytest tests/ -v
ruff check .
```

### Expected output

On success, the pipeline prints the path of the artifact it wrote, e.g.:

```
Pipeline succeeded. Clean artifact: data/processed/clean\_glove\_tests\_20260715T140212Z.csv
```

That CSV has the same 14 columns as the raw extract, but is guaranteed to
pass every check in `GLOVE\_TEST\_SCHEMA`. If you point `extract()` at a
file containing bad rows (negative leakage, an invalid `Test\_Result`
value, etc.), the pipeline exits non-zero and prints the Pandera failure
cases instead of writing an artifact — try it by editing a row in
`data/raw/glove\_test\_extract.csv` to see the gate in action.

## What's next (Milestone 2)

MLflow experiment tracking, an expanded pytest suite (6+ tests / 3
categories / ≥60% coverage), and a GitHub Actions CI workflow will be
added on top of this pipeline without changing it.


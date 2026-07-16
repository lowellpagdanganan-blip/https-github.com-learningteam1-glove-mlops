# Insulating Glove Test Data Pipeline

**MAIDA 211 — AI and Analytics Special Topics — Milestone 1**

## Project & Model

Field electrical crews wear rubber insulating gloves as primary protection against electric shock. Regulations (ASTM F496 / OSHA) require these gloves to be periodically dielectric-tested; a glove that leaks more than 3.00 mA under test fails and must be pulled from service. Today, test results are exported from the test-bench system into a spreadsheet and reviewed manually. The eventual model will predict whether a glove is likely to Pass or Fail its next test from its usage history (age, usage cycles, number of owners, brand, and material), so the safety team can proactively flag and replace high-risk gloves before they fail a live test.

This repository implements Milestone 1: the data pipeline that reads the raw test-result extract, enforces a data-quality contract via Pandera, and writes a clean versioned artifact for modeling in Milestone 2.

## Repository Structure

glove-mlops/
├── dags/
│   ├── __init__.py
│   └── your_pipeline.py      # Airflow DAG: extract -> validate -> load
├── data/
│   ├── raw/
│   │   └── glove_test_extract.csv
│   └── processed/
├── tests/
│   └── test_pipeline.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .pre-commit-config.yaml
├── .gitignore
└── README.md

## Orchestrator

This pipeline uses Apache Airflow via Docker Compose. The DAG implements three tasks: Extract, Validate, and Load using Airflow TaskFlow API (@dag/@task decorators).

## Pipeline

1. Extract - reads data/raw/glove_test_extract.csv
2. Validate - enforces Pandera schema checks. Pipeline stops if data is invalid.
3. Load - writes data/processed/clean_glove_tests_<UTC-timestamp>.csv

## How to Run

Prerequisites: Docker Desktop installed and running, at least 4 GB RAM.

Step 1 - Clone the repo:
git clone https://github.com/lowellpagdanganan-blip/https-github.com-learningteam1-glove-mlops.git
cd https-github.com-learningteam1-glove-mlops

Step 2 - Create required directories:
mkdir logs
mkdir data\processed

Step 3 - Initialize Airflow database:
docker compose up airflow-init

Step 4 - Start Airflow:
docker compose up

Step 5 - Open browser and go to:
http://localhost:8081
Login: admin / admin

Step 6 - Trigger the pipeline:
Find glove_test_pipeline, toggle it On, click the Trigger DAG button.
Watch Extract, Validate, and Load turn green.

## Output Artifact

On success, a timestamped CSV is written to:
data/processed/clean_glove_tests_<UTC-timestamp>.csv

Example: data/processed/clean_glove_tests_20260715T140212Z.csv

The file contains the same columns as the raw extract but is guaranteed to pass all Pandera schema checks. If any row fails validation, the pipeline stops and no output file is written.

## Tear Down

docker compose down

## What is Next - Milestone 2

MLflow experiment tracking, expanded pytest suite, and GitHub Actions CI workflow.

\# Insulating Glove Test Data Pipeline



\*\*MAIDA 211 — AI and Analytics Special Topics — Milestone 1\*\*



\## Project \& Model



Field electrical crews wear rubber insulating gloves as primary protection

against electric shock. Regulations (ASTM F496 / OSHA) require these gloves

to be periodically dielectric-tested; a glove that leaks more than 3.00 mA

under test fails and must be pulled from service. Today, test results are

exported from the test-bench system into a spreadsheet and reviewed

manually. The eventual model will predict whether a glove is likely to

\*\*Pass or Fail\*\* its next test from its usage history (age, number of usage

cycles, number of owners, brand/material), so the safety team can

proactively flag and replace high-risk gloves before they fail a live test.



This repository implements \*\*Milestone 1\*\*: the data pipeline that reads

the raw test-result extract, enforces a data-quality contract, and writes

a clean, versioned artifact for the modeling work in Milestone 2.



\## Repository Structure



glove-mlops/

├── dags/

│   ├── \_\_init\_\_.py

│   └── your\_pipeline.py      # Airflow DAG: extract → validate → load

├── data/

│   ├── raw/

│   │   └── glove\_test\_extract.csv   # synthetic sample, same schema as production extract

│   └── processed/                   # versioned clean output lands here (gitignored)

├── tests/

│   └── test\_pipeline.py

├── docker-compose.yml

├── Dockerfile

├── pyproject.toml

├── .pre-commit-config.yaml

├── .gitignore

└── README.md



\## Orchestrator



This pipeline uses \*\*Apache Airflow\*\* via Docker Compose. The DAG follows

the minimum required structure: extract → validate → load, implemented

using Airflow's @dag / @task decorators (TaskFlow API).



\## Pipeline



1\. \*\*Extract\*\* — reads data/raw/glove\_test\_extract.csv

2\. \*\*Validate\*\* — runs Pandera schema checks. Pipeline stops with an error

&#x20;  if data does not conform — this is not a warning.

3\. \*\*Load\*\* — writes validated data to

&#x20;  data/processed/clean\_glove\_tests\_<UTC-timestamp>.csv



\## How to Run



\### Prerequisites

\- Docker Desktop installed and running

\- At least 4 GB RAM allocated to Docker



\### First run



\# 1. Clone the repo

git clone https://github.com/lowellpagdanganan-blip/https-github.com-learningteam1-glove-mlops.git

cd https-github.com-learningteam1-glove-mlops



\# 2. Create required local directories

mkdir -p logs data/processed



\# 3. Initialise the Airflow database

docker compose up airflow-init



\# 4. Start Airflow

docker compose up



\### Trigger the pipeline



Open your browser and go to: http://localhost:8081



Login: admin / admin



1\. Find the glove\_test\_pipeline DAG

2\. Toggle it On

3\. Click the Trigger DAG button

4\. Watch Extract → Validate → Load turn green



\### Check the output artifact



ls data/processed/

\# clean\_glove\_tests\_20260715T140212Z.csv



\### Tear down



docker compose down



\## What's Next (Milestone 2)



MLflow experiment tracking, an expanded pytest suite, and a GitHub Actions

CI workflow will be added on top of this pipeline.


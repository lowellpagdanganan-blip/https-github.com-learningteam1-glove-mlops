# Glove MLOps — Airflow image
# Extends the official Airflow image with project-specific dependencies.

FROM apache/airflow:2.9.3-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy dependency spec first (layer-cache friendly)
COPY pyproject.toml /opt/airflow/pyproject.toml

# Install project deps (Airflow itself is already in the base image)
RUN pip install --no-cache-dir \
    "pandas==2.2.3" \
    "pandera==0.20.4"

# DAGs and data are bind-mounted at runtime via docker-compose volumes,
# but copy them here too so the image is self-contained for CI.
COPY dags/ /opt/airflow/dags/
COPY data/  /opt/airflow/data/
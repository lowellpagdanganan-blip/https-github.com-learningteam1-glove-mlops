"""Pytest bootstrap — make the suite runnable on Windows.

Importing dags/your_pipeline.py runs `from airflow.decorators import dag, task`
and instantiates the DAG at import time. Real Airflow does not support Windows:
on import it tries to configure a SQLite path and a logging formatter and raises
(`Cannot use relative path ... sqlite`, `Unable to configure formatter 'airflow'`),
which breaks test collection.

The pipeline's actual logic (_extract / _validate / _load and the Pandera schema)
is plain Python and needs no Airflow. So before any test imports the pipeline, we
install a minimal stand-in for `airflow.decorators` that provides no-op `dag` and
`task` decorators. This lets the identical suite run on Windows, macOS, Linux, and
CI, without modifying dags/your_pipeline.py.
"""

import sys
import types

_airflow = types.ModuleType("airflow")
_decorators = types.ModuleType("airflow.decorators")


def _dag(*args, **kwargs):
    def decorator(func):
        def wrapper(*a, **k):
            # Never execute the DAG body at import time (no side effects).
            return None

        return wrapper

    return decorator


def _task(*args, **kwargs):
    def decorator(func):
        return func

    return decorator


_decorators.dag = _dag
_decorators.task = _task
_airflow.decorators = _decorators

# Install the stand-in before dags/your_pipeline.py is imported.
sys.modules["airflow"] = _airflow
sys.modules["airflow.decorators"] = _decorators

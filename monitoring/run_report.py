"""Monitoring dashboard (Deliverable 2) for glove_fail_classifier.
Reference = clean training data. Current = simulated drifted production sample.
DataDrift + TargetDrift presets (>=2) with an explicit ColumnMapping, plus a
4-test suite covering data quality."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from evidently import ColumnMapping
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
from evidently.test_suite import TestSuite
from evidently.tests import (
    TestNumberOfDriftedColumns, TestShareOfMissingValues,
    TestNumberOfColumnsWithMissingValues, TestNumberOfRowsWithMissingValues,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS = os.path.join(ROOT, "reports")
DATA = os.path.join(ROOT, "data")
RNG = np.random.default_rng(7)
CAT = ["LeftRight", "Area", "Brand", "Make", "Test_Quarter"]
NUM = ["Test_Year", "Size", "Number_of_Owners", "Age_as_of_Test", "Usage_Rate", "Liveline_Ratio"]
TARGET = "Test_Result"


def engineer(df):
    df = df.copy()
    df["Usage_Rate"] = df["Number_of_Usage"] / (df["Age_as_of_Test"] + 0.25)
    ll = df["Liveline_Usage"] + df["PreArrange_Usage"]
    df["Liveline_Ratio"] = np.where(ll > 0, df["Liveline_Usage"] / ll, 0.0)
    return df[CAT + NUM + ([TARGET] if TARGET in df.columns else [])]


def simulate_drift(ref):
    cur = ref.sample(n=min(400, len(ref)), random_state=7).copy()
    cur["Age_as_of_Test"] = cur["Age_as_of_Test"] + RNG.normal(4.0, 1.0, len(cur))
    cur["Usage_Rate"] = cur["Usage_Rate"] * RNG.uniform(1.5, 2.0, len(cur))
    cur["Number_of_Owners"] = cur["Number_of_Owners"] + RNG.integers(1, 3, len(cur))
    cur["Liveline_Ratio"] = np.clip(cur["Liveline_Ratio"] + RNG.normal(0.18, 0.05, len(cur)), 0, 1)
    cur["Size"] = np.clip(cur["Size"] + RNG.integers(0, 2, len(cur)), 7, 12)
    return cur


def main():
    os.makedirs(REPORTS, exist_ok=True)
    reference = engineer(pd.read_csv(os.path.join(DATA, "reference.csv")))
    current = simulate_drift(reference)
    mapping = ColumnMapping(target=TARGET, prediction=None,
                            numerical_features=NUM, categorical_features=CAT)

    report = Report(metrics=[DataDriftPreset(), TargetDriftPreset()])
    report.run(reference_data=reference, current_data=current, column_mapping=mapping)
    report.save_html(os.path.join(REPORTS, "drift_report.html"))

    suite = TestSuite(tests=[
        TestNumberOfDriftedColumns(lt=(len(CAT + NUM) + 1) // 2),
        TestShareOfMissingValues(lte=0.0),
        TestNumberOfColumnsWithMissingValues(eq=0),
        TestNumberOfRowsWithMissingValues(eq=0),
    ])
    suite.run(reference_data=reference, current_data=current, column_mapping=mapping)
    suite.save_html(os.path.join(REPORTS, "test_suite.html"))

    drift = next(m for m in report.as_dict()["metrics"]
                 if m["metric"] == "DatasetDriftMetric")["result"]
    print(f"Dataset drift: {drift['dataset_drift']} "
          f"({drift['number_of_drifted_columns']}/{len(CAT + NUM)} columns, "
          f"share={drift['share_of_drifted_columns']:.3f})")
    passed = sum(1 for t in suite.as_dict()["tests"] if t["status"] == "SUCCESS")
    print(f"Tests passed: {passed}/{len(suite.as_dict()['tests'])}")


if __name__ == "__main__":
    main()

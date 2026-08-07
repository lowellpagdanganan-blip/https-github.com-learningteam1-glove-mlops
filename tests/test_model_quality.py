"""Deliverable 2b — model quality tests.

Not unit tests of model internals: they train the Milestone 1 candidate
(SVM + Random Oversampling) on the committed sample and assert its outputs meet
business-relevant criteria — a minimum performance floor and a well-formed
prediction output. Data is read from the raw extract and validated with the
Milestone 1 schema (no file side effects).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from dags.your_pipeline import GLOVE_TEST_SCHEMA, RAW_PATH
from models.train import train

# --- thresholds (named constants, not magic numbers) -----------------------
# Chosen relative to the committed 800-row sample, deterministically
# reproducible at random_state=42. We gate on Fail-class F1 rather than raw
# accuracy: Random Oversampling deliberately trades overall accuracy for Fail
# recall, so under heavy class imbalance accuracy is a weak signal (a
# predict-everything-Pass baseline already scores ~0.77). Observed on this
# sample: fail_f1 ~= 0.57, roc_auc ~= 0.82. Floors sit safely below those but
# well above a naive/random model, so the gate catches real regressions
# without being flaky.
MIN_FAIL_F1 = 0.45
MIN_ROC_AUC = 0.70


@pytest.fixture(scope="module")
def trained():
    df = pd.read_csv(RAW_PATH)
    df = GLOVE_TEST_SCHEMA.validate(df, lazy=True)
    return train(df)


def test_fail_f1_above_threshold(trained):
    assert trained.metrics["fail_f1"] >= MIN_FAIL_F1, (
        f"Fail-class F1 {trained.metrics['fail_f1']:.3f} below floor {MIN_FAIL_F1}"
    )


def test_roc_auc_above_threshold(trained):
    assert trained.metrics["roc_auc"] >= MIN_ROC_AUC, (
        f"ROC-AUC {trained.metrics['roc_auc']:.3f} below floor {MIN_ROC_AUC}"
    )


def test_prediction_output_is_well_formed(trained):
    preds = trained.model.predict(trained.X_test)
    # correct shape
    assert preds.shape[0] == len(trained.X_test)
    # valid class labels only (0 = Pass, 1 = Fail)
    assert set(np.unique(preds)).issubset({0, 1})
    # no NaN predictions
    assert not np.any(pd.isna(preds))

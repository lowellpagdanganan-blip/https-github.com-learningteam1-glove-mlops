"""Feature schema — single source of truth for the model inputs.
Matched to the real glove_fail_classifier: SVM predicting Test_Result
(Fail=1 / Pass=0). Usage_Rate and Liveline_Ratio are engineered in train.py;
the endpoint accepts the already-computed values."""
from __future__ import annotations

CATEGORICAL_FEATURES: dict[str, list[str]] = {
    "LeftRight":    ["Left", "Right"],
    "Area":         ["North", "South", "East", "West"],
    "Brand":        ["CATU", "3M", "Honeywell", "Regeltex"],
    "Make":         ["Composite", "EPDM", "Latex"],
    "Test_Quarter": ["Q1", "Q2", "Q3", "Q4"],
}

NUMERIC_FEATURES: dict[str, tuple[float, float, float]] = {
    "Test_Year":        (2015, 2030, 2025),
    "Size":             (7, 12, 9),
    "Number_of_Owners": (1, 10, 3),
    "Age_as_of_Test":   (0.0, 20.0, 3.5),
    "Usage_Rate":       (0.0, 5000.0, 100.0),
    "Liveline_Ratio":   (0.0, 1.0, 0.5),
}

TARGET = "Test_Result"
POSITIVE_LABEL_IS = 1

FEATURE_NAMES: list[str] = list(CATEGORICAL_FEATURES) + list(NUMERIC_FEATURES)
CAT_NAMES: list[str] = list(CATEGORICAL_FEATURES)
NUM_NAMES: list[str] = list(NUMERIC_FEATURES)

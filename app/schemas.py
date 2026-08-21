"""Pydantic request/response models. Fields match the 11 model features.
extra="forbid" + type checks give automatic 422 on bad input."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    LeftRight: str = Field(..., examples=["Left"])
    Area: str = Field(..., examples=["North"])
    Brand: str = Field(..., examples=["CATU"])
    Make: str = Field(..., examples=["Composite"])
    Test_Quarter: str = Field(..., examples=["Q4"])
    Test_Year: int = Field(..., ge=2000, le=2100, examples=[2025])
    Size: int = Field(..., ge=0, le=20, examples=[9])
    Number_of_Owners: int = Field(..., ge=0, le=100, examples=[3])
    Age_as_of_Test: float = Field(..., ge=0, le=100, examples=[3.5])
    Usage_Rate: float = Field(..., ge=0, le=100000, examples=[100.0])
    Liveline_Ratio: float = Field(..., ge=0.0, le=1.0, examples=[0.5])


class PredictResponse(BaseModel):
    prediction: int = Field(..., description="1 = predicted FAIL, 0 = predicted PASS")
    label: str = Field(..., description="'fail' or 'pass'")
    probability: float | None = Field(None, description="P(fail) if available, else null")
    model_version: str


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    model_name: str
    model_version: str
    git_commit: str | None = None

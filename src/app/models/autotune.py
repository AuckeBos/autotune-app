"""Pydantic models for Autotune data structures."""

from pydantic import BaseModel, Field


class AutotuneBasalEntry(BaseModel):
    """Single basal rate entry from autotune output."""

    start: str = Field(..., description="Start time in HH:MM:SS format")
    minutes: int = Field(..., ge=0, description="Duration in minutes")
    rate: float = Field(..., ge=0, description="Basal rate in U/hr")


class AutotuneCarbRatioEntry(BaseModel):
    """Carb ratio from autotune output."""

    ratio: float = Field(..., gt=0, description="Carb ratio (g/U)")


class AutotuneSensitivityEntry(BaseModel):
    """Insulin sensitivity from autotune output."""

    sensitivity: float = Field(..., gt=0, description="ISF in mg/dL per U")


class AutotuneResult(BaseModel):
    """Complete autotune result."""

    basalprofile: list[AutotuneBasalEntry] = Field(..., description="Basal schedule")
    carb_ratio: float = Field(..., gt=0, description="Recommended carb ratio")
    sens: float = Field(..., gt=0, description="Recommended ISF")
    dia: float | None = Field(None, gt=0, description="Duration of insulin action")


class AutotuneRecommendations(BaseModel):
    """Autotune recommendations with additional metadata."""

    result: AutotuneResult = Field(..., description="Autotune calculation results")
    profile_name: str = Field(..., description="Name of the profile analyzed")
    analysis_date: str = Field(..., description="Date of analysis")
    days_analyzed: int = Field(..., ge=1, description="Number of days analyzed")

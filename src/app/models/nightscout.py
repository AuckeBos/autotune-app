"""Pydantic models for Nightscout data structures."""

from datetime import datetime

from pydantic import BaseModel, Field


class BasalScheduleEntry(BaseModel):
    """Single basal rate entry in a schedule."""

    time: str = Field(..., description="Time in HH:MM format")
    value: float = Field(..., ge=0, description="Basal rate in U/hr")
    timeAsSeconds: int = Field(..., ge=0, description="Time as seconds from midnight")


class CarbRatioEntry(BaseModel):
    """Single carb ratio entry in a schedule."""

    time: str = Field(..., description="Time in HH:MM format")
    value: float = Field(..., gt=0, description="Carb ratio (g/U)")
    timeAsSeconds: int = Field(..., ge=0, description="Time as seconds from midnight")


class SensitivityEntry(BaseModel):
    """Single insulin sensitivity entry in a schedule."""

    time: str = Field(..., description="Time in HH:MM format")
    value: float = Field(..., gt=0, description="ISF in mg/dL per U")
    timeAsSeconds: int = Field(..., ge=0, description="Time as seconds from midnight")


class TargetEntry(BaseModel):
    """Single target BG entry in a schedule."""

    time: str = Field(..., description="Time in HH:MM format")
    value: float = Field(..., gt=0, description="Target BG in mg/dL")
    low: float = Field(..., gt=0, description="Low target in mg/dL")
    high: float = Field(..., gt=0, description="High target in mg/dL")
    timeAsSeconds: int = Field(..., ge=0, description="Time as seconds from midnight")


class ProfileStore(BaseModel):
    """Individual profile within a profile store."""

    dia: float = Field(..., gt=0, description="Duration of insulin action in hours")
    carbratio: list[CarbRatioEntry] = Field(..., description="Carb ratio schedule")
    sens: list[SensitivityEntry] = Field(
        ..., description="Insulin sensitivity schedule"
    )
    basal: list[BasalScheduleEntry] = Field(..., description="Basal rate schedule")
    target_low: list[TargetEntry] = Field(..., description="Low target schedule")
    target_high: list[TargetEntry] = Field(..., description="High target schedule")
    timezone: str = Field(..., description="Timezone for the profile")
    units: str = Field(..., description="Units (mg/dL or mmol/L)")


class NightscoutProfile(BaseModel):
    """Complete Nightscout profile document."""

    _id: str = Field(..., description="Profile document ID")
    defaultProfile: str = Field(..., description="Name of the default profile")
    store: dict[str, ProfileStore] = Field(
        ..., description="Profile store with named profiles"
    )
    startDate: str = Field(..., description="Profile start date")
    mills: int = Field(..., description="Profile timestamp in milliseconds")
    units: str = Field(..., description="Units (mg/dL or mmol/L)")
    created_at: str = Field(..., description="Creation timestamp")

    @property
    def num_profiles(self) -> int:
        """Return the number of profiles in the store."""
        return len(self.store)

    @property
    def profile_names(self) -> list[str]:
        """Return a list of profile names in the store."""
        return list(self.store.keys())

    @property
    def default_profile(self) -> ProfileStore:
        """Return the default profile from the store."""
        return self.store[self.defaultProfile]


class NightscoutEntry(BaseModel):
    """Nightscout glucose entry."""

    _id: str = Field(..., description="Entry ID")
    sgv: int = Field(..., ge=20, le=600, description="Glucose value in mg/dL")
    date: int = Field(..., description="Timestamp in milliseconds")
    dateString: str = Field(..., description="ISO format date string")
    type: str = Field(..., description="Entry type (e.g., sgv)")
    direction: str | None = Field(None, description="Trend direction")
    device: str | None = Field(None, description="Device name")


class NightscoutTreatment(BaseModel):
    """Nightscout treatment entry."""

    _id: str = Field(..., description="Treatment ID")
    eventType: str = Field(..., description="Type of treatment")
    created_at: str = Field(..., description="Creation timestamp")
    timestamp: str | None = Field(None, description="Treatment timestamp")
    insulin: float | None = Field(None, ge=0, description="Insulin amount in U")
    carbs: float | None = Field(None, ge=0, description="Carbs in grams")
    glucose: int | None = Field(None, description="BG value")
    glucoseType: str | None = Field(None, description="Meter or sensor")
    notes: str | None = Field(None, description="Treatment notes")
    enteredBy: str | None = Field(None, description="Who entered the treatment")


class HistoricalData(BaseModel):
    """Container for historical Nightscout data."""

    entries: list[NightscoutEntry] = Field(..., description="Glucose entries")
    treatments: list[NightscoutTreatment] = Field(..., description="Treatment entries")
    start_date: datetime = Field(..., description="Start date of data range")
    end_date: datetime = Field(..., description="End date of data range")

"""Unit tests for Autotune service."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.models.autotune import AutotuneRecommendations, AutotuneResult
from app.models.nightscout import (
    HistoricalData,
    NightscoutEntry,
    NightscoutTreatment,
    ProfileStore,
)
from app.services.autotune_service import AutotuneService


@pytest.fixture
def mock_autotune_client():
    """Fixture providing a mocked Autotune client."""
    with patch("app.services.autotune_service.AutotuneClient") as mock:
        yield mock


@pytest.fixture
def autotune_service(mock_autotune_client):
    """Fixture providing an Autotune service instance."""
    return AutotuneService("/usr/local/bin/oref0-autotune")


@pytest.fixture
def mock_profile_store():
    """Fixture providing a ProfileStore instance."""
    return ProfileStore(
        dia=5.0,
        carbratio=[{"time": "00:00", "value": 10.0, "timeAsSeconds": 0}],
        sens=[{"time": "00:00", "value": 50.0, "timeAsSeconds": 0}],
        basal=[{"time": "00:00", "value": 1.0, "timeAsSeconds": 0}],
        target_low=[
            {
                "time": "00:00",
                "value": 100.0,
                "low": 90.0,
                "high": 110.0,
                "timeAsSeconds": 0,
            }
        ],
        target_high=[
            {
                "time": "00:00",
                "value": 120.0,
                "low": 110.0,
                "high": 130.0,
                "timeAsSeconds": 0,
            }
        ],
        timezone="UTC",
        units="mg/dL",
    )


@pytest.fixture
def mock_historical_data():
    """Fixture providing HistoricalData instance."""
    entries = [
        NightscoutEntry(
            _id="entry1",
            sgv=120,
            date=1704067200000,
            dateString="2024-01-01T00:00:00Z",
            type="sgv",
        ),
        NightscoutEntry(
            _id="entry2",
            sgv=130,
            date=1704070800000,
            dateString="2024-01-01T01:00:00Z",
            type="sgv",
        ),
    ]

    treatments = [
        NightscoutTreatment(
            _id="treatment1",
            eventType="Meal Bolus",
            created_at="2024-01-01T00:00:00Z",
            insulin=5.0,
            carbs=50.0,
        )
    ]

    return HistoricalData(
        entries=entries,
        treatments=treatments,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 8),
    )


@pytest.fixture
def mock_autotune_result():
    """Fixture providing autotune result data."""
    return {
        "basalprofile": [
            {"start": "00:00:00", "minutes": 60, "rate": 1.1},
            {"start": "01:00:00", "minutes": 60, "rate": 1.2},
        ],
        "carb_ratio": 12.0,
        "sens": 55.0,
        "dia": 5.0,
    }


class TestAutotuneServiceInit:
    """Tests for AutotuneService initialization."""

    def test_init_creates_client(self, mock_autotune_client):
        """Test that service initializes client correctly."""
        service = AutotuneService("/custom/path/autotune")

        mock_autotune_client.assert_called_once_with("/custom/path/autotune")

    def test_init_with_default_path(self, mock_autotune_client):
        """Test initialization with default autotune path."""
        service = AutotuneService()

        mock_autotune_client.assert_called_once_with("/usr/local/bin/oref0-autotune")


class TestAutotuneServiceRunAnalysis:
    """Tests for run_analysis method."""

    def test_run_analysis_returns_validated_model(
        self,
        autotune_service,
        mock_profile_store,
        mock_historical_data,
        mock_autotune_result,
    ):
        """Test that run_analysis returns validated AutotuneRecommendations."""
        autotune_service.client.run_autotune = Mock(return_value=mock_autotune_result)

        result = autotune_service.run_analysis(
            mock_profile_store, mock_historical_data, "Default", days=7
        )

        assert isinstance(result, AutotuneRecommendations)
        assert isinstance(result.result, AutotuneResult)
        assert result.result.carb_ratio == 12.0
        assert result.result.sens == 55.0
        assert result.profile_name == "Default"
        assert result.days_analyzed == 7

    def test_run_analysis_converts_models_to_dicts(
        self,
        autotune_service,
        mock_profile_store,
        mock_historical_data,
        mock_autotune_result,
    ):
        """Test that Pydantic models are converted to dicts for client."""
        autotune_service.client.run_autotune = Mock(return_value=mock_autotune_result)

        autotune_service.run_analysis(
            mock_profile_store, mock_historical_data, "Default"
        )

        # Verify run_autotune was called with dicts
        call_args = autotune_service.client.run_autotune.call_args[0]
        assert isinstance(call_args[0], dict)  # profile_data
        assert isinstance(call_args[1], list)  # entries_data
        assert isinstance(call_args[2], list)  # treatments_data

    def test_run_analysis_invalid_result_raises_validation_error(
        self, autotune_service, mock_profile_store, mock_historical_data
    ):
        """Test that invalid autotune result raises ValidationError."""
        invalid_result = {"invalid": "data"}
        autotune_service.client.run_autotune = Mock(return_value=invalid_result)

        with pytest.raises(ValidationError):
            autotune_service.run_analysis(
                mock_profile_store, mock_historical_data, "Default"
            )


class TestAutotuneServiceApplyRecommendations:
    """Tests for apply_recommendations method."""

    def test_apply_recommendations_updates_profile(
        self, autotune_service, mock_profile_store
    ):
        """Test that apply_recommendations updates profile correctly."""
        recommendations = AutotuneRecommendations(
            result=AutotuneResult(
                basalprofile=[
                    {"start": "00:00:00", "minutes": 60, "rate": 1.1},
                    {"start": "06:00:00", "minutes": 360, "rate": 1.2},
                ],
                carb_ratio=12.0,
                sens=55.0,
                dia=5.5,
            ),
            profile_name="Default",
            analysis_date=datetime.now().isoformat(),
            days_analyzed=7,
        )

        result = autotune_service.apply_recommendations(
            mock_profile_store, recommendations
        )

        # Verify updates
        assert isinstance(result, ProfileStore)
        assert result.carbratio[0].value == 12.0
        assert result.sens[0].value == 55.0
        assert result.dia == 5.5
        assert len(result.basal) == 2
        assert result.basal[0].value == 1.1
        assert result.basal[1].value == 1.2

    def test_apply_recommendations_does_not_modify_original(
        self, autotune_service, mock_profile_store
    ):
        """Test that original profile is not modified."""
        original_carb_ratio = mock_profile_store.carbratio[0].value

        recommendations = AutotuneRecommendations(
            result=AutotuneResult(
                basalprofile=[{"start": "00:00:00", "minutes": 1440, "rate": 1.5}],
                carb_ratio=15.0,
                sens=60.0,
            ),
            profile_name="Default",
            analysis_date=datetime.now().isoformat(),
            days_analyzed=7,
        )

        result = autotune_service.apply_recommendations(
            mock_profile_store, recommendations
        )

        # Original should be unchanged
        assert mock_profile_store.carbratio[0].value == original_carb_ratio
        # Result should be updated
        assert result.carbratio[0].value == 15.0

    def test_apply_recommendations_converts_time_format(
        self, autotune_service, mock_profile_store
    ):
        """Test that basal time format is converted correctly."""
        recommendations = AutotuneRecommendations(
            result=AutotuneResult(
                basalprofile=[
                    {"start": "06:30:00", "minutes": 60, "rate": 1.3},
                ],
                carb_ratio=12.0,
                sens=55.0,
            ),
            profile_name="Default",
            analysis_date=datetime.now().isoformat(),
            days_analyzed=7,
        )

        result = autotune_service.apply_recommendations(
            mock_profile_store, recommendations
        )

        # Verify time conversion (HH:MM:SS -> HH:MM)
        assert result.basal[0].time == "06:30"
        assert result.basal[0].timeAsSeconds == 6 * 3600 + 30 * 60

    def test_apply_recommendations_without_dia(
        self, autotune_service, mock_profile_store
    ):
        """Test applying recommendations when DIA is not provided."""
        original_dia = mock_profile_store.dia

        recommendations = AutotuneRecommendations(
            result=AutotuneResult(
                basalprofile=[{"start": "00:00:00", "minutes": 1440, "rate": 1.0}],
                carb_ratio=12.0,
                sens=55.0,
                dia=None,  # No DIA recommendation
            ),
            profile_name="Default",
            analysis_date=datetime.now().isoformat(),
            days_analyzed=7,
        )

        result = autotune_service.apply_recommendations(
            mock_profile_store, recommendations
        )

        # DIA should remain unchanged
        assert result.dia == original_dia

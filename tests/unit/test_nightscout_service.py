"""Unit tests for Nightscout service."""

from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.models.nightscout import HistoricalData, NightscoutProfile, ProfileStore
from app.services.nightscout_service import NightscoutService


@pytest.fixture
def mock_nightscout_client():
    """Fixture providing a mocked Nightscout client."""
    with patch("app.services.nightscout_service.NightscoutClient") as mock:
        yield mock


@pytest.fixture
def nightscout_service(mock_nightscout_client):
    """Fixture providing a Nightscout service instance."""
    return NightscoutService("https://test.nightscout.com", "test-secret")


@pytest.fixture
def mock_profile_data():
    """Fixture providing valid profile data."""
    return {
        "_id": "test-id",
        "defaultProfile": "Default",
        "store": {
            "Default": {
                "dia": 5.0,
                "carbratio": [{"time": "00:00", "value": 10.0, "timeAsSeconds": 0}],
                "sens": [{"time": "00:00", "value": 50.0, "timeAsSeconds": 0}],
                "basal": [{"time": "00:00", "value": 1.0, "timeAsSeconds": 0}],
                "target_low": [
                    {
                        "time": "00:00",
                        "value": 100.0,
                        "low": 90.0,
                        "high": 110.0,
                        "timeAsSeconds": 0,
                    }
                ],
                "target_high": [
                    {
                        "time": "00:00",
                        "value": 120.0,
                        "low": 110.0,
                        "high": 130.0,
                        "timeAsSeconds": 0,
                    }
                ],
                "timezone": "UTC",
                "units": "mg/dL",
            }
        },
        "startDate": "2024-01-01T00:00:00Z",
        "mills": 1704067200000,
        "units": "mg/dL",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_entries_data():
    """Fixture providing valid entries data."""
    return [
        {
            "_id": "entry1",
            "sgv": 120,
            "date": 1704067200000,
            "dateString": "2024-01-01T00:00:00Z",
            "type": "sgv",
        },
        {
            "_id": "entry2",
            "sgv": 130,
            "date": 1704070800000,
            "dateString": "2024-01-01T01:00:00Z",
            "type": "sgv",
        },
    ]


@pytest.fixture
def mock_treatments_data():
    """Fixture providing valid treatments data."""
    return [
        {
            "_id": "treatment1",
            "eventType": "Meal Bolus",
            "created_at": "2024-01-01T00:00:00Z",
            "insulin": 5.0,
            "carbs": 50.0,
        }
    ]


class TestNightscoutServiceInit:
    """Tests for NightscoutService initialization."""

    def test_init_creates_client(self, mock_nightscout_client):
        """Test that service initializes client correctly."""
        service = NightscoutService("https://test.com", "secret")

        mock_nightscout_client.assert_called_once_with("https://test.com", "secret", 30)


class TestNightscoutServiceGetProfile:
    """Tests for get_profile method."""

    def test_get_profile_returns_validated_model(
        self, nightscout_service, mock_profile_data
    ):
        """Test that get_profile returns validated NightscoutProfile."""
        nightscout_service.client.get_profile = Mock(return_value=mock_profile_data)

        result = nightscout_service.get_profile()

        assert isinstance(result, NightscoutProfile)
        assert result.defaultProfile == "Default"
        assert "Default" in result.store

    def test_get_profile_with_name(self, nightscout_service, mock_profile_data):
        """Test get_profile with specific profile name."""
        nightscout_service.client.get_profile = Mock(return_value=mock_profile_data)

        result = nightscout_service.get_profile("Default")

        nightscout_service.client.get_profile.assert_called_once_with("Default")
        assert isinstance(result, NightscoutProfile)

    def test_get_profile_invalid_data_raises_validation_error(self, nightscout_service):
        """Test that invalid profile data raises ValidationError."""
        invalid_data = {"invalid": "data"}
        nightscout_service.client.get_profile = Mock(return_value=invalid_data)

        with pytest.raises(ValidationError):
            nightscout_service.get_profile()


class TestNightscoutServiceGetProfileStore:
    """Tests for get_profile_store method."""

    def test_get_profile_store_returns_validated_model(
        self, nightscout_service, mock_profile_data
    ):
        """Test that get_profile_store returns validated ProfileStore."""
        nightscout_service.client.get_profile = Mock(return_value=mock_profile_data)

        result = nightscout_service.get_profile_store("Default")

        assert isinstance(result, ProfileStore)
        assert result.dia == 5.0
        assert len(result.basal) == 1

    def test_get_profile_store_nonexistent_raises_error(
        self, nightscout_service, mock_profile_data
    ):
        """Test that requesting nonexistent profile raises ValueError."""
        nightscout_service.client.get_profile = Mock(return_value=mock_profile_data)

        with pytest.raises(ValueError, match="not found in store"):
            nightscout_service.get_profile_store("NonExistent")


class TestNightscoutServiceGetHistoricalData:
    """Tests for get_historical_data method."""

    def test_get_historical_data_returns_validated_model(
        self, nightscout_service, mock_entries_data, mock_treatments_data
    ):
        """Test that get_historical_data returns validated HistoricalData."""
        nightscout_service.client.get_historical_data = Mock(
            return_value=(mock_entries_data, mock_treatments_data)
        )

        result = nightscout_service.get_historical_data(days=7)

        assert isinstance(result, HistoricalData)
        assert len(result.entries) == 2
        assert len(result.treatments) == 1
        assert result.entries[0].sgv == 120

    def test_get_historical_data_skips_invalid_entries(self, nightscout_service):
        """Test that invalid entries are skipped with warning."""
        valid_entry = {
            "_id": "entry1",
            "sgv": 120,
            "date": 1704067200000,
            "dateString": "2024-01-01T00:00:00Z",
            "type": "sgv",
        }
        invalid_entry = {"invalid": "data"}

        nightscout_service.client.get_historical_data = Mock(
            return_value=([valid_entry, invalid_entry], [])
        )

        result = nightscout_service.get_historical_data()

        # Only valid entry should be included
        assert len(result.entries) == 1
        assert result.entries[0].sgv == 120

    def test_get_historical_data_with_custom_days(
        self, nightscout_service, mock_entries_data, mock_treatments_data
    ):
        """Test get_historical_data with custom number of days."""
        nightscout_service.client.get_historical_data = Mock(
            return_value=(mock_entries_data, mock_treatments_data)
        )

        result = nightscout_service.get_historical_data(days=14)

        nightscout_service.client.get_historical_data.assert_called_once_with(14)
        assert isinstance(result, HistoricalData)


class TestNightscoutServiceSyncProfile:
    """Tests for sync_profile method."""

    def test_sync_profile_converts_to_dict(self, nightscout_service, mock_profile_data):
        """Test that sync_profile converts ProfileStore to dict."""
        nightscout_service.client.update_profile = Mock()

        profile_store = ProfileStore(**mock_profile_data["store"]["Default"])

        nightscout_service.sync_profile(profile_store, "Default")

        # Verify update_profile was called with dict
        call_args = nightscout_service.client.update_profile.call_args
        assert isinstance(call_args[0][0], dict)
        assert call_args[0][1] == "Default"

    def test_sync_profile_without_name(self, nightscout_service, mock_profile_data):
        """Test sync_profile without specifying profile name."""
        nightscout_service.client.update_profile = Mock()

        profile_store = ProfileStore(**mock_profile_data["store"]["Default"])

        nightscout_service.sync_profile(profile_store)

        # Verify update_profile was called with None as profile name
        call_args = nightscout_service.client.update_profile.call_args
        assert call_args[0][1] is None

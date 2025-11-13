"""Unit tests for Nightscout client."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests

from app.clients.nightscout_client import NightscoutClient


@pytest.fixture
def nightscout_client():
    """Fixture providing a Nightscout client instance."""
    return NightscoutClient("https://test.nightscout.com", "test-secret")


@pytest.fixture
def mock_profile_response():
    """Fixture providing mock profile response data."""
    return [
        {
            "_id": "test-profile-id",
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
    ]


@pytest.fixture
def mock_entries_response():
    """Fixture providing mock entries response data."""
    return [
        {
            "_id": "entry1",
            "sgv": 120,
            "date": 1704067200000,
            "dateString": "2024-01-01T00:00:00Z",
            "type": "sgv",
            "direction": "Flat",
            "device": "test-device",
        },
        {
            "_id": "entry2",
            "sgv": 130,
            "date": 1704070800000,
            "dateString": "2024-01-01T01:00:00Z",
            "type": "sgv",
            "direction": "FortyFiveUp",
            "device": "test-device",
        },
    ]


@pytest.fixture
def mock_treatments_response():
    """Fixture providing mock treatments response data."""
    return [
        {
            "_id": "treatment1",
            "eventType": "Meal Bolus",
            "created_at": "2024-01-01T00:00:00Z",
            "timestamp": "2024-01-01T00:00:00Z",
            "insulin": 5.0,
            "carbs": 50.0,
            "glucose": 120,
            "glucoseType": "Finger",
            "notes": "Test meal",
            "enteredBy": "test-user",
        }
    ]


class TestNightscoutClientInit:
    """Tests for NightscoutClient initialization."""

    def test_init_with_https_url(self):
        """Test that client initializes successfully with HTTPS URL."""
        client = NightscoutClient("https://test.nightscout.com", "secret")
        assert client.url == "https://test.nightscout.com"
        assert client.api_secret == "secret"
        assert client.timeout == 30

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        client = NightscoutClient("https://test.nightscout.com/", "secret")
        assert client.url == "https://test.nightscout.com"

    def test_init_with_http_url_raises_error(self):
        """Test that HTTP URLs are rejected."""
        with pytest.raises(ValueError, match="must use HTTPS"):
            NightscoutClient("http://test.nightscout.com", "secret")

    def test_init_with_custom_timeout(self):
        """Test that custom timeout is set correctly."""
        client = NightscoutClient("https://test.nightscout.com", "secret", timeout=60)
        assert client.timeout == 60


class TestNightscoutClientAuth:
    """Tests for authentication header generation."""

    def test_get_auth_headers(self, nightscout_client):
        """Test that authentication headers are generated correctly."""
        headers = nightscout_client._get_auth_headers()

        assert "API-SECRET" in headers
        assert "Content-Type" in headers
        assert "Accept" in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        # API-SECRET should be SHA1 hash of the secret
        assert len(headers["API-SECRET"]) == 40  # SHA1 hash length


class TestNightscoutClientGetProfile:
    """Tests for get_profile method."""

    @patch("requests.Session.get")
    def test_get_profile_success(
        self, mock_get, nightscout_client, mock_profile_response
    ):
        """Test successful profile retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_profile_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = nightscout_client.get_profile()

        assert result == mock_profile_response[0]
        assert result["defaultProfile"] == "Default"
        assert "Default" in result["store"]

    @patch("requests.Session.get")
    def test_get_profile_with_name(
        self, mock_get, nightscout_client, mock_profile_response
    ):
        """Test profile retrieval with specific profile name."""
        mock_response = Mock()
        mock_response.json.return_value = mock_profile_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = nightscout_client.get_profile("Default")

        assert "Default" in result["store"]

    @patch("requests.Session.get")
    def test_get_profile_nonexistent_name_raises_error(
        self, mock_get, nightscout_client, mock_profile_response
    ):
        """Test that requesting nonexistent profile raises ValueError."""
        mock_response = Mock()
        mock_response.json.return_value = mock_profile_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Profile 'NonExistent' not found"):
            nightscout_client.get_profile("NonExistent")

    @patch("requests.Session.get")
    def test_get_profile_empty_response_raises_error(self, mock_get, nightscout_client):
        """Test that empty profile response raises ValueError."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="No profiles found"):
            nightscout_client.get_profile()

    @patch("requests.Session.get")
    def test_get_profile_http_error(self, mock_get, nightscout_client):
        """Test that HTTP errors are propagated."""
        mock_get.side_effect = requests.HTTPError("API error")

        with pytest.raises(requests.HTTPError):
            nightscout_client.get_profile()


class TestNightscoutClientGetEntries:
    """Tests for get_entries method."""

    @patch("requests.Session.get")
    def test_get_entries_success(
        self, mock_get, nightscout_client, mock_entries_response
    ):
        """Test successful entries retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_entries_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        result = nightscout_client.get_entries(start_date, end_date)

        assert len(result) == 2
        assert result[0]["sgv"] == 120
        assert result[1]["sgv"] == 130

    @patch("requests.Session.get")
    def test_get_entries_with_custom_count(
        self, mock_get, nightscout_client, mock_entries_response
    ):
        """Test entries retrieval with custom count."""
        mock_response = Mock()
        mock_response.json.return_value = mock_entries_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        nightscout_client.get_entries(start_date, end_date, count=50)

        # Verify count parameter was passed
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["count"] == 50


class TestNightscoutClientGetTreatments:
    """Tests for get_treatments method."""

    @patch("requests.Session.get")
    def test_get_treatments_success(
        self, mock_get, nightscout_client, mock_treatments_response
    ):
        """Test successful treatments retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = mock_treatments_response
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        result = nightscout_client.get_treatments(start_date, end_date)

        assert len(result) == 1
        assert result[0]["insulin"] == 5.0
        assert result[0]["carbs"] == 50.0


class TestNightscoutClientGetHistoricalData:
    """Tests for get_historical_data method."""

    @patch("requests.Session.get")
    def test_get_historical_data_success(
        self,
        mock_get,
        nightscout_client,
        mock_entries_response,
        mock_treatments_response,
    ):
        """Test successful historical data retrieval."""
        mock_response = Mock()
        # Alternate responses for entries and treatments calls
        mock_response.json.side_effect = [
            mock_entries_response,
            mock_treatments_response,
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        entries, treatments = nightscout_client.get_historical_data(days=7)

        assert len(entries) == 2
        assert len(treatments) == 1
        assert mock_get.call_count == 2


class TestNightscoutClientUpdateProfile:
    """Tests for update_profile method."""

    @patch("requests.Session.post")
    @patch("requests.Session.get")
    def test_update_profile_success(
        self, mock_get, mock_post, nightscout_client, mock_profile_response
    ):
        """Test successful profile update."""
        # Mock GET response (to fetch current profile)
        mock_get_response = Mock()
        mock_get_response.json.return_value = mock_profile_response
        mock_get_response.status_code = 200
        mock_get.return_value = mock_get_response

        # Mock POST response
        mock_post_response = Mock()
        mock_post_response.json.return_value = {"ok": True}
        mock_post_response.status_code = 200
        mock_post.return_value = mock_post_response

        new_profile_data = {
            "dia": 6.0,
            "carbratio": [{"time": "00:00", "value": 12.0, "timeAsSeconds": 0}],
            "sens": [{"time": "00:00", "value": 55.0, "timeAsSeconds": 0}],
            "basal": [{"time": "00:00", "value": 1.2, "timeAsSeconds": 0}],
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

        result = nightscout_client.update_profile(new_profile_data, "Default")

        assert result == {"ok": True}
        assert mock_get.call_count == 1
        assert mock_post.call_count == 1

    @patch("requests.Session.get")
    def test_update_profile_no_default_raises_error(self, mock_get, nightscout_client):
        """Test that missing default profile raises ValueError."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "_id": "test-id",
                "store": {},
                "mills": 1234567890,
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="No profile name specified"):
            nightscout_client.update_profile({})

"""Unit tests for Autotune client."""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from app.clients.autotune_client import AutotuneClient


@pytest.fixture
def autotune_client():
    """Fixture providing an Autotune client instance."""
    return AutotuneClient("/usr/local/bin/oref0-autotune")


@pytest.fixture
def mock_profile_data():
    """Fixture providing mock profile data."""
    return {
        "dia": 5.0,
        "carbratio": [{"time": "00:00", "value": 10.0}],
        "sens": [{"time": "00:00", "value": 50.0}],
        "basal": [{"time": "00:00", "value": 1.0}],
    }


@pytest.fixture
def mock_entries_data():
    """Fixture providing mock entries data."""
    return [
        {"sgv": 120, "date": 1704067200000, "type": "sgv"},
        {"sgv": 130, "date": 1704070800000, "type": "sgv"},
    ]


@pytest.fixture
def mock_treatments_data():
    """Fixture providing mock treatments data."""
    return [
        {
            "insulin": 5.0,
            "carbs": 50.0,
            "created_at": "2024-01-01T00:00:00Z",
            "eventType": "Meal Bolus",
        }
    ]


@pytest.fixture
def mock_autotune_result():
    """Fixture providing mock autotune result."""
    return {
        "basalprofile": [
            {"start": "00:00:00", "minutes": 60, "rate": 1.1},
            {"start": "01:00:00", "minutes": 60, "rate": 1.2},
        ],
        "carb_ratio": 12.0,
        "sens": 55.0,
        "dia": 5.0,
    }


class TestAutotuneClientInit:
    """Tests for AutotuneClient initialization."""

    def test_init_with_default_path(self):
        """Test client initialization with default path."""
        client = AutotuneClient()
        assert client.autotune_path == "/usr/local/bin/oref0-autotune"

    def test_init_with_custom_path(self):
        """Test client initialization with custom path."""
        custom_path = "/custom/path/to/autotune"
        client = AutotuneClient(custom_path)
        assert client.autotune_path == custom_path


class TestAutotuneClientRunAutotune:
    """Tests for run_autotune method."""

    @patch("subprocess.run")
    @patch("tempfile.TemporaryDirectory")
    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_run_autotune_success(
        self,
        mock_exists,
        mock_read_text,
        mock_write_text,
        mock_tempdir,
        mock_run,
        autotune_client,
        mock_profile_data,
        mock_entries_data,
        mock_treatments_data,
        mock_autotune_result,
    ):
        """Test successful autotune execution."""
        # Setup mocks
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"
        mock_exists.return_value = True
        mock_read_text.return_value = json.dumps(mock_autotune_result)

        mock_result = Mock()
        mock_result.stdout = "Autotune completed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Run autotune
        result = autotune_client.run_autotune(
            mock_profile_data, mock_entries_data, mock_treatments_data, days=7
        )

        # Verify result
        assert result == mock_autotune_result
        assert result["carb_ratio"] == 12.0
        assert result["sens"] == 55.0
        assert len(result["basalprofile"]) == 2

        # Verify subprocess was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/local/bin/oref0-autotune"
        assert "--days" in call_args
        assert "7" in call_args

    @patch("subprocess.run")
    @patch("tempfile.TemporaryDirectory")
    def test_run_autotune_timeout(
        self,
        mock_tempdir,
        mock_run,
        autotune_client,
        mock_profile_data,
        mock_entries_data,
        mock_treatments_data,
    ):
        """Test autotune execution timeout."""
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 600)

        with pytest.raises(ValueError, match="timed out"):
            autotune_client.run_autotune(
                mock_profile_data, mock_entries_data, mock_treatments_data
            )

    @patch("subprocess.run")
    @patch("tempfile.TemporaryDirectory")
    def test_run_autotune_execution_failure(
        self,
        mock_tempdir,
        mock_run,
        autotune_client,
        mock_profile_data,
        mock_entries_data,
        mock_treatments_data,
    ):
        """Test autotune execution failure."""
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error message"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "cmd", output="", stderr="Error message"
        )

        with pytest.raises(subprocess.CalledProcessError):
            autotune_client.run_autotune(
                mock_profile_data, mock_entries_data, mock_treatments_data
            )

    @patch("subprocess.run")
    @patch("tempfile.TemporaryDirectory")
    @patch("pathlib.Path.exists")
    def test_run_autotune_no_output_file(
        self,
        mock_exists,
        mock_tempdir,
        mock_run,
        autotune_client,
        mock_profile_data,
        mock_entries_data,
        mock_treatments_data,
    ):
        """Test autotune when no recommendations file is produced."""
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"
        mock_exists.return_value = False  # Recommendations file doesn't exist

        mock_result = Mock()
        mock_result.stdout = "Completed"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with pytest.raises(ValueError, match="did not produce recommendations"):
            autotune_client.run_autotune(
                mock_profile_data, mock_entries_data, mock_treatments_data
            )


class TestAutotuneClientUploadProfile:
    """Tests for upload_profile method."""

    @patch("subprocess.run")
    @patch("tempfile.TemporaryDirectory")
    def test_upload_profile_not_implemented(
        self, mock_tempdir, mock_run, autotune_client, mock_profile_data
    ):
        """Test that upload raises NotImplementedError if tool not found."""
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"
        mock_run.side_effect = FileNotFoundError()

        with pytest.raises(NotImplementedError, match="Use NightscoutClient"):
            autotune_client.upload_profile(
                mock_profile_data, "https://test.com", "secret"
            )

    @patch("subprocess.run")
    @patch("tempfile.TemporaryDirectory")
    def test_upload_profile_execution_failure(
        self, mock_tempdir, mock_run, autotune_client, mock_profile_data
    ):
        """Test upload profile execution failure."""
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "cmd", output="", stderr="Upload failed"
        )

        with pytest.raises(subprocess.CalledProcessError):
            autotune_client.upload_profile(
                mock_profile_data, "https://test.com", "secret"
            )

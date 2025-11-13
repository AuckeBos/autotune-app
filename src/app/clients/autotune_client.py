"""Client for running autotune analysis."""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AutotuneClient:
    """
    Client for running autotune analysis.

    Wraps the oref0-autotune command-line tool to analyze
    glucose and treatment data and generate profile recommendations.
    """

    def __init__(self, autotune_path: str = "/usr/local/bin/oref0-autotune"):
        """
        Initialize Autotune client.

        Args:
            autotune_path: Path to oref0-autotune executable
        """
        self.autotune_path = autotune_path
        logger.info(f"Initialized Autotune client with path: {autotune_path}")

    def run_autotune(
        self,
        profile_data: dict[str, Any],
        entries: list[dict[str, Any]],
        treatments: list[dict[str, Any]],
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Run autotune analysis on historical data.

        Args:
            profile_data: Current profile to use as baseline
            entries: List of glucose entries
            treatments: List of treatment entries
            days: Number of days to analyze

        Returns:
            Dict containing autotune recommendations

        Raises:
            subprocess.CalledProcessError: If autotune execution fails
            ValueError: If autotune produces invalid output
        """
        logger.info(f"Running autotune analysis for {days} days")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write input files
            profile_file = tmppath / "profile.json"
            entries_file = tmppath / "entries.json"
            treatments_file = tmppath / "treatments.json"
            output_dir = tmppath / "autotune"
            output_dir.mkdir()

            profile_file.write_text(json.dumps(profile_data, indent=2))
            entries_file.write_text(json.dumps(entries, indent=2))
            treatments_file.write_text(json.dumps(treatments, indent=2))

            logger.debug("Wrote input files to %s", tmpdir)

            # Run autotune
            try:
                cmd = [
                    self.autotune_path,
                    "--dir",
                    str(tmpdir),
                    "--ns-entries",
                    str(entries_file),
                    "--ns-treatments",
                    str(treatments_file),
                    "--profile",
                    str(profile_file),
                    "--days",
                    str(days),
                ]

                logger.debug(f"Executing autotune command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=600,  # 10 minute timeout
                )

                logger.debug("Autotune stdout: %s", result.stdout)
                if result.stderr:
                    logger.debug("Autotune stderr: %s", result.stderr)

            except subprocess.TimeoutExpired as e:
                logger.error("Autotune execution timed out")
                raise ValueError("Autotune analysis timed out") from e
            except subprocess.CalledProcessError as e:
                logger.error(f"Autotune failed with exit code {e.returncode}")
                logger.error(f"stdout: {e.stdout}")
                logger.error(f"stderr: {e.stderr}")
                raise

            # Read results
            recommendations_file = output_dir / "autotune_recommendations.json"
            if not recommendations_file.exists():
                raise ValueError(
                    "Autotune did not produce recommendations file. "
                    "Check that enough valid data was provided."
                )

            recommendations = json.loads(recommendations_file.read_text())

            logger.info("Successfully completed autotune analysis")
            return recommendations

    def upload_profile(
        self, profile_data: dict[str, Any], nightscout_url: str, api_secret: str
    ) -> dict[str, Any]:
        """
        Upload profile to Nightscout using autotune's upload functionality.

        This is an alternative to using the NightscoutClient directly,
        utilizing autotune's built-in upload capability.

        Args:
            profile_data: Profile data to upload
            nightscout_url: Nightscout URL
            api_secret: Nightscout API secret

        Returns:
            Dict containing upload result

        Raises:
            subprocess.CalledProcessError: If upload fails
        """
        logger.info("Uploading profile to Nightscout via autotune")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Write profile to file
            profile_file = tmppath / "profile.json"
            profile_file.write_text(json.dumps(profile_data, indent=2))

            try:
                # Use oref0-upload command if available
                # This is a simplified version - actual implementation may vary
                # based on available autotune utilities
                cmd = [
                    "oref0-upload",
                    str(profile_file),
                    nightscout_url,
                    api_secret,
                ]

                logger.debug(f"Executing upload command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=True, timeout=30
                )

                logger.info("Successfully uploaded profile via autotune")
                return {"success": True, "output": result.stdout}

            except FileNotFoundError:
                logger.warning(
                    "oref0-upload not found. "
                    "Use NightscoutClient.update_profile() instead."
                )
                raise NotImplementedError(
                    "Upload via autotune not available. Use NightscoutClient instead."
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Profile upload failed: {e.stderr}")
                raise

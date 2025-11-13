"""Client for interacting with Nightscout API."""

import hashlib
import logging
from datetime import datetime, timedelta
from functools import cached_property
from typing import Any

import requests
from pydantic import BaseModel
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.app.models.nightscout import NightscoutProfile, ProfileStore

logger = logging.getLogger(__name__)


class NightscoutClient(BaseModel):
    """
    Client for Nightscout API operations.

    Handles authentication and provides methods for:
    - Loading profiles
    - Loading historical glucose and treatment data
    - Syncing updated profiles
    """

    url: str
    api_secret: str
    timeout: int = 30

    @cached_property
    def _session(self) -> Session:
        """Setup requests session with retries."""
        session = Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    @property
    def _auth_headers(self) -> dict[str, str]:
        """
        Generate authentication headers for Nightscout API.

        Returns:
            Dict containing API-SECRET header with hashed secret
        """
        api_secret_hash = hashlib.sha1(self.api_secret.encode()).hexdigest()
        return {
            "API-SECRET": api_secret_hash,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_profiles(self) -> NightscoutProfile:
        """
        Internal method to fetch all profiles from Nightscout.

        Returns:
            NightscoutProfile containing all profile data
        """
        url = f"{self.url}/api/v1/profile"
        headers = self._auth_headers

        logger.info("Fetching all profiles from Nightscout")

        response = self._session.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError("No profiles found in Nightscout")

        profile_doc = data[0] if isinstance(data, list) else data

        profile = NightscoutProfile(**profile_doc)

        logger.info(
            f"Successfully loaded profile with {profile.num_profiles} profile(s)"
        )
        return profile

    def get_profile(self, profile_name: str) -> ProfileStore:
        """
        Load a profile from Nightscout.

        Args:
            profile_name: Name of the profile to load.

        Returns:
            Validated ProfileStore model for the specified profile

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If profile_name specified but not found
        """
        profiles = self._get_profiles()
        profile_store = profiles.store.get(profile_name)
        if not profile_store:
            raise ValueError(
                f"Profile '{profile_name}' not found. "
                f"Available profiles: {profiles.profile_names}"
            )
        return profile_store

    def get_entries(
        self, start_date: datetime, end_date: datetime, count: int = 100000
    ) -> list[dict[str, Any]]:
        """
        Load glucose entries from Nightscout for a date range.

        Args:
            start_date: Start date for entries
            end_date: End date for entries
            count: Maximum number of entries to retrieve

        Returns:
            List of glucose entry dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.url}/api/v1/entries"
        headers = self._auth_headers

        # Convert dates to ISO format
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        params = {
            "find[dateString][$gte]": start_iso,
            "find[dateString][$lte]": end_iso,
            "count": count,
        }

        logger.info(f"Fetching entries from {start_date} to {end_date}")

        try:
            response = self._session.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            entries = response.json()

            logger.info(f"Successfully loaded {len(entries)} entries")
            return entries

        except requests.RequestException as e:
            logger.error(f"Failed to fetch entries: {e}")
            raise

    def get_treatments(
        self, start_date: datetime, end_date: datetime, count: int = 100000
    ) -> list[dict[str, Any]]:
        """
        Load treatment entries from Nightscout for a date range.

        Args:
            start_date: Start date for treatments
            end_date: End date for treatments
            count: Maximum number of treatments to retrieve

        Returns:
            List of treatment entry dictionaries

        Raises:
            requests.HTTPError: If API request fails
        """
        url = f"{self.url}/api/v1/treatments"
        headers = self._auth_headers

        # Convert dates to ISO format
        start_iso = start_date.isoformat()
        end_iso = end_date.isoformat()

        params = {
            "find[created_at][$gte]": start_iso,
            "find[created_at][$lte]": end_iso,
            "count": count,
        }

        logger.info(f"Fetching treatments from {start_date} to {end_date}")

        try:
            response = self._session.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            treatments = response.json()

            logger.info(f"Successfully loaded {len(treatments)} treatments")
            return treatments

        except requests.RequestException as e:
            logger.error(f"Failed to fetch treatments: {e}")
            raise

    def get_historical_data(
        self, days: int = 7
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Load historical glucose and treatment data for specified number of days.

        Args:
            days: Number of days of historical data to load

        Returns:
            Tuple of (entries, treatments) lists

        Raises:
            requests.HTTPError: If API request fails
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        entries = self.get_entries(start_date, end_date)
        treatments = self.get_treatments(start_date, end_date)

        return entries, treatments

    def update_profile(
        self, profile_data: dict[str, Any], profile_name: str | None = None
    ) -> dict[str, Any]:
        """
        Update a profile in Nightscout.

        This method updates an existing profile document by modifying
        the specified profile within the store.

        Args:
            profile_data: Profile data to update (store entry format)
            profile_name: Name of the profile to update (uses default if None)

        Returns:
            Dict containing the updated profile response

        Raises:
            requests.HTTPError: If API request fails
            ValueError: If profile not found
        """
        # First, get the current profile document
        current_profile = self._get_profiles().default_profile

        # Update the store with new profile data
        if "store" not in current_profile:
            current_profile["store"] = {}

        current_profile["store"][target_profile] = profile_data

        # Update timestamp
        current_profile["mills"] = int(datetime.now().timestamp() * 1000)

        # POST the updated profile
        url = f"{self.url}/api/v1/profile"
        headers = self._auth_headers

        logger.info(f"Updating profile '{target_profile}' in Nightscout")

        try:
            response = self.session.post(
                url, headers=headers, json=current_profile, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully updated profile '{target_profile}'")
            return result

        except requests.RequestException as e:
            logger.error(f"Failed to update profile: {e}")
            raise

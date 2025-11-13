"""Service for Nightscout operations with Pydantic model validation."""

import logging
from datetime import datetime, timedelta

from app.clients.nightscout_client import NightscoutClient
from app.models.nightscout import (
    HistoricalData,
    NightscoutEntry,
    NightscoutProfile,
    NightscoutTreatment,
    ProfileStore,
)

logger = logging.getLogger(__name__)


class NightscoutService:
    """
    High-level service for Nightscout operations.

    Wraps NightscoutClient and returns validated Pydantic models
    for type-safe, user-friendly interaction with Nightscout data.
    """

    def __init__(self, url: str, api_secret: str, timeout: int = 30):
        """
        Initialize Nightscout service.

        Args:
            url: Nightscout URL (must be HTTPS)
            api_secret: API secret for authentication
            timeout: Request timeout in seconds
        """
        self.client = NightscoutClient(url, api_secret, timeout)
        logger.info("Initialized Nightscout service")

    def get_profile(self, profile_name: str | None = None) -> NightscoutProfile:
        """
        Load and validate a profile from Nightscout.

        Args:
            profile_name: Name of the profile to load. If None, loads default profile

        Returns:
            Validated NightscoutProfile model

        Raises:
            ValidationError: If profile data doesn't match expected format
            ValueError: If profile not found
        """
        logger.info(f"Loading profile: {profile_name or 'default'}")

        profile_data = self.client.get_profile(profile_name)
        profile = NightscoutProfile(**profile_data)

        logger.info(f"Successfully loaded profile with {len(profile.store)} profile(s)")
        return profile

    def get_profile_store(self, profile_name: str) -> ProfileStore:
        """
        Load a specific profile from the profile store.

        Args:
            profile_name: Name of the profile to load from store

        Returns:
            Validated ProfileStore model for the specified profile

        Raises:
            ValidationError: If profile data doesn't match expected format
            ValueError: If profile not found
        """
        logger.info(f"Loading profile store entry: {profile_name}")

        profile = self.get_profile(profile_name)

        if profile_name not in profile.store:
            available = list(profile.store.keys())
            raise ValueError(
                f"Profile '{profile_name}' not found in store. "
                f"Available profiles: {available}"
            )

        store_entry = ProfileStore(**profile.store[profile_name].model_dump())

        logger.info(f"Successfully loaded profile store entry: {profile_name}")
        return store_entry

    def get_historical_data(self, days: int = 7) -> HistoricalData:
        """
        Load and validate historical glucose and treatment data.

        Args:
            days: Number of days of historical data to load

        Returns:
            Validated HistoricalData model containing entries and treatments

        Raises:
            ValidationError: If data doesn't match expected format
        """
        logger.info(f"Loading {days} days of historical data")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        entries_raw, treatments_raw = self.client.get_historical_data(days)

        # Validate entries
        entries = []
        for entry_data in entries_raw:
            try:
                entry = NightscoutEntry(**entry_data)
                entries.append(entry)
            except Exception as e:
                logger.warning(f"Skipping invalid entry: {e}")
                continue

        # Validate treatments
        treatments = []
        for treatment_data in treatments_raw:
            try:
                treatment = NightscoutTreatment(**treatment_data)
                treatments.append(treatment)
            except Exception as e:
                logger.warning(f"Skipping invalid treatment: {e}")
                continue

        historical_data = HistoricalData(
            entries=entries,
            treatments=treatments,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(
            f"Successfully loaded {len(entries)} entries and "
            f"{len(treatments)} treatments"
        )
        return historical_data

    def sync_profile(
        self, profile_store: ProfileStore, profile_name: str | None = None
    ) -> None:
        """
        Sync an updated profile back to Nightscout.

        Args:
            profile_store: ProfileStore model with updated profile data
            profile_name: Name of the profile to update (uses default if None)

        Raises:
            ValidationError: If profile data is invalid
            requests.HTTPError: If API request fails
        """
        logger.info(f"Syncing profile: {profile_name or 'default'}")

        # Convert Pydantic model to dict for API
        profile_data = profile_store.model_dump()

        self.client.update_profile(profile_data, profile_name)

        logger.info(f"Successfully synced profile: {profile_name or 'default'}")

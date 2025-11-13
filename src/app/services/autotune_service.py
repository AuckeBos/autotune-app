"""Service for Autotune operations with Pydantic model validation."""

import logging
from datetime import datetime

from app.clients.autotune_client import AutotuneClient
from app.models.autotune import AutotuneRecommendations, AutotuneResult
from app.models.nightscout import HistoricalData, ProfileStore

logger = logging.getLogger(__name__)


class AutotuneService:
    """
    High-level service for Autotune operations.

    Wraps AutotuneClient and returns validated Pydantic models
    for type-safe, user-friendly autotune analysis.
    """

    def __init__(self, autotune_path: str = "/usr/local/bin/oref0-autotune"):
        """
        Initialize Autotune service.

        Args:
            autotune_path: Path to oref0-autotune executable
        """
        self.client = AutotuneClient(autotune_path)
        logger.info("Initialized Autotune service")

    def run_analysis(
        self,
        profile: ProfileStore,
        historical_data: HistoricalData,
        profile_name: str,
        days: int = 7,
    ) -> AutotuneRecommendations:
        """
        Run autotune analysis and return validated recommendations.

        Args:
            profile: Current profile to use as baseline
            historical_data: Historical glucose and treatment data
            profile_name: Name of the profile being analyzed
            days: Number of days to analyze

        Returns:
            Validated AutotuneRecommendations model

        Raises:
            ValidationError: If autotune output is invalid
            ValueError: If autotune fails or produces no results
        """
        logger.info(f"Running autotune analysis for profile '{profile_name}'")

        # Convert Pydantic models to dicts for autotune client
        profile_data = profile.model_dump()
        entries_data = [entry.model_dump() for entry in historical_data.entries]
        treatments_data = [
            treatment.model_dump() for treatment in historical_data.treatments
        ]

        # Run autotune
        result_data = self.client.run_autotune(
            profile_data, entries_data, treatments_data, days
        )

        # Validate and wrap result
        result = AutotuneResult(**result_data)

        recommendations = AutotuneRecommendations(
            result=result,
            profile_name=profile_name,
            analysis_date=datetime.now().isoformat(),
            days_analyzed=days,
        )

        logger.info(
            f"Autotune analysis complete for '{profile_name}': "
            f"carb_ratio={result.carb_ratio}, sens={result.sens}"
        )
        return recommendations

    def apply_recommendations(
        self, profile: ProfileStore, recommendations: AutotuneRecommendations
    ) -> ProfileStore:
        """
        Apply autotune recommendations to a profile.

        Creates a new ProfileStore with updated values from autotune.
        Does not modify the original profile.

        Args:
            profile: Original profile
            recommendations: Autotune recommendations to apply

        Returns:
            New ProfileStore with applied recommendations
        """
        logger.info("Applying autotune recommendations to profile")

        # Create a copy of the profile
        updated_profile = profile.model_copy(deep=True)

        # Apply recommendations
        result = recommendations.result

        # Update carb ratio for all entries
        for entry in updated_profile.carbratio:
            entry.value = result.carb_ratio

        # Update insulin sensitivity for all entries
        for entry in updated_profile.sens:
            entry.value = result.sens

        # Update basal rates from autotune basalprofile
        if result.basalprofile:
            # Clear existing basal schedule
            updated_profile.basal = []

            # Convert autotune basal format to Nightscout format
            from app.models.nightscout import BasalScheduleEntry

            for basal_entry in result.basalprofile:
                # Convert HH:MM:SS to HH:MM
                time_parts = basal_entry.start.split(":")
                time_str = f"{time_parts[0]}:{time_parts[1]}"

                # Calculate seconds from midnight
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                time_as_seconds = hours * 3600 + minutes * 60

                ns_basal = BasalScheduleEntry(
                    time=time_str,
                    value=basal_entry.rate,
                    timeAsSeconds=time_as_seconds,
                )
                updated_profile.basal.append(ns_basal)

        # Update DIA if provided
        if result.dia:
            updated_profile.dia = result.dia

        logger.info("Successfully applied autotune recommendations")
        return updated_profile

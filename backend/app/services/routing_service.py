"""
Abstract base class for routing services.

This module defines the interface that all routing service implementations
must follow, allowing seamless switching between different routing APIs
(Google Routes, Ekispert, etc.) based on region and requirements.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class AbstractRoutingService(ABC):
    """Base class for all routing service implementations."""

    @abstractmethod
    async def compute_route(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "DRIVE",
        departure_time: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Compute a route between origin and destination.

        Args:
            origin: Starting location (address, coordinates, or place name)
            destination: Ending location (address, coordinates, or place name)
            travel_mode: Travel mode (DRIVE, WALK, BICYCLE, TRANSIT, etc.)
            departure_time: Departure time in ISO 8601 format (optional)
            **kwargs: Additional service-specific parameters

        Returns:
            Dictionary containing route information in service-specific format

        Raises:
            Exception: If route calculation fails
        """
        pass

    @abstractmethod
    def transform_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform service-specific API response to unified application format.

        Args:
            api_response: Raw response from the routing API

        Returns:
            Dictionary in unified RouteResponse-compatible format with fields:
            - duration_seconds: Total duration in seconds
            - duration_text: Human-readable duration
            - distance_meters: Total distance in meters
            - distance_text: Human-readable distance
            - polyline: Encoded polyline (optional)
            - start_location: Start coordinates (optional)
            - end_location: End coordinates (optional)
            - transit_steps: List of transit steps (for TRANSIT mode)
            - fare: Fare information (optional)

        Raises:
            ValueError: If response format is invalid
        """
        pass

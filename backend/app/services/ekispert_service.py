"""
Ekispert (駅すぱあと) API integration service.

This service provides routing functionality for Japan using the Ekispert Web Service API,
which offers comprehensive transit routing with fare information, transfer details,
and accurate arrival/departure times for Japanese public transportation.

API Documentation: https://docs.ekispert.com/
"""

import httpx
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging

from .routing_service import AbstractRoutingService

logger = logging.getLogger(__name__)


class EkispertService(AbstractRoutingService):
    """Ekispert API routing service implementation."""

    def __init__(self, api_key: str):
        """
        Initialize Ekispert service.

        Args:
            api_key: Ekispert API access key
        """
        self.api_key = api_key
        self.base_url = "https://api.ekispert.jp/v1/json"
        self.timeout = 30.0

    async def compute_route(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "TRANSIT",
        departure_time: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Compute route using Ekispert API.

        Args:
            origin: Starting station/location name
            destination: Ending station/location name
            travel_mode: Travel mode (only TRANSIT is supported)
            departure_time: Departure time in ISO 8601 format
            **kwargs: Additional parameters (arrival_time, etc.)

        Returns:
            Ekispert API response dictionary

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If non-TRANSIT mode is requested
        """
        if travel_mode != "TRANSIT":
            raise ValueError(f"Ekispert API only supports TRANSIT mode, got: {travel_mode}")

        # Prepare search parameters
        params = {
            "key": self.api_key,
            "viaList": f"{origin}:{destination}",
            "answerCount": 3,  # Get top 3 routes
            "sort": "time",  # Sort by time (other options: price, teiki, ekispert)
        }

        # Add departure/arrival time if specified
        if departure_time:
            # Convert ISO 8601 to Ekispert format (YYYYMMDDHHMM)
            dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
            params["date"] = dt.strftime("%Y%m%d")
            params["time"] = dt.strftime("%H%M")
            params["searchType"] = "departure"
        elif kwargs.get("arrival_time"):
            dt = datetime.fromisoformat(kwargs["arrival_time"].replace('Z', '+00:00'))
            params["date"] = dt.strftime("%Y%m%d")
            params["time"] = dt.strftime("%H%M")
            params["searchType"] = "arrival"

        # Make API request
        endpoint = f"{self.base_url}/search/course/extreme"

        logger.info(f"Ekispert API request: {origin} -> {destination}")

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()

            # Check for API errors
            if "ResultSet" not in data or "Course" not in data.get("ResultSet", {}):
                logger.warning(f"Ekispert API returned no routes: {data}")
                return {"ResultSet": {"Course": []}}

            logger.info(f"Ekispert API returned {len(data['ResultSet']['Course'])} routes")
            return data

    def transform_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Ekispert API response to unified format.

        Ekispert response structure:
        {
          "ResultSet": {
            "Course": [{
              "Route": [...],
              "Price": [{"Oneway": 160, "kind": "普通運賃"}],
              "timeTotal": 10,
              "timeOnBoard": 8,
              "timeWalk": 2,
              "distance": 3400,
              "transferCount": 0
            }]
          }
        }

        Args:
            api_response: Raw Ekispert API response

        Returns:
            Unified route information dictionary

        Raises:
            ValueError: If response format is invalid
        """
        if not api_response.get("ResultSet", {}).get("Course"):
            return {
                "success": False,
                "routes": [],
                "error_message": "指定された条件でルートが見つかりませんでした"
            }

        # Extract first (best) route
        course = api_response["ResultSet"]["Course"][0]

        # Extract duration (in minutes from Ekispert, convert to seconds)
        duration_minutes = course.get("timeTotal", 0)
        duration_seconds = duration_minutes * 60

        # Extract distance (meters)
        distance_meters = course.get("distance", 0)

        # Extract fare information
        fare = None
        if course.get("Price"):
            price_data = course["Price"][0]
            fare = {
                "currency_code": "JPY",
                "units": str(price_data.get("Oneway", 0)),
                "nanos": 0
            }

        # Extract transit steps
        transit_steps = self._extract_transit_steps(course)

        return {
            "success": True,
            "duration_seconds": duration_seconds,
            "duration_text": self._format_duration(duration_seconds),
            "distance_meters": distance_meters,
            "distance_text": self._format_distance(distance_meters),
            "polyline": None,  # Ekispert doesn't provide polylines in free plan
            "start_location": None,  # Would need separate geocoding
            "end_location": None,
            "transit_steps": transit_steps,
            "fare": fare,
            "transfer_count": course.get("transferCount", 0),
            "walking_time_seconds": course.get("timeWalk", 0) * 60,
            "on_board_time_seconds": course.get("timeOnBoard", 0) * 60
        }

    def _extract_transit_steps(self, course: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract transit steps from Ekispert course.

        Args:
            course: Ekispert course dictionary

        Returns:
            List of transit step dictionaries
        """
        steps = []
        routes = course.get("Route", [])

        for idx, route in enumerate(routes):
            # Check if this is a Line (transit) or Walk segment
            if "Line" in route:
                line = route["Line"]
                step = {
                    "mode": "TRANSIT",
                    "line_name": line.get("Name", ""),
                    "line_type": line.get("Type", ""),
                    "departure_station": route.get("Point", [{}])[0].get("Station", {}).get("Name", ""),
                    "arrival_station": route.get("Point", [{}])[-1].get("Station", {}).get("Name", "") if len(route.get("Point", [])) > 1 else "",
                    "departure_time": route.get("timeOnBoard"),  # In minutes
                    "num_stops": route.get("stopCount", 0),
                    "distance_meters": route.get("distance", 0)
                }
                steps.append(step)
            elif "Walk" in route:
                step = {
                    "mode": "WALK",
                    "distance_meters": route.get("distance", 0),
                    "duration_seconds": route.get("timeOnBoard", 0) * 60
                }
                steps.append(step)

        return steps

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable text."""
        if seconds < 60:
            return f"{seconds}秒"

        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}分"

        hours = minutes // 60
        mins = minutes % 60
        if mins > 0:
            return f"{hours}時間{mins}分"
        return f"{hours}時間"

    def _format_distance(self, meters: int) -> str:
        """Format distance in meters to human-readable text."""
        if meters < 1000:
            return f"{meters}m"

        km = meters / 1000
        return f"{km:.1f}km"

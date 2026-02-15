"""
Google Maps API統合サービス
"""

import httpx
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Google Maps API（Routes API, Geocoding API）を扱うサービスクラス"""

    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.routes_api_url = (
            "https://routes.googleapis.com/directions/v2:computeRoutes"
        )
        self.geocoding_api_url = "https://maps.googleapis.com/maps/api/geocode/json"

    async def geocode_address(self, address: str) -> Tuple[float, float]:
        """
        住所を座標に変換（Geocoding API）

        Args:
            address: 住所または地名

        Returns:
            Tuple[float, float]: (latitude, longitude)

        Raises:
            ValueError: ジオコーディングに失敗した場合
        """
        params = {"address": address, "key": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(self.geocoding_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "OK" or not data.get("results"):
                raise ValueError(f"住所のジオコーディングに失敗しました: {address}")

            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]

    async def compute_route(
        self,
        origin: str,
        destination: str,
        travel_mode: str = "DRIVE",
        compute_alternative_routes: bool = False,
        departure_time: Optional[str] = None,
        transit_preferences: Optional[Dict] = None,
    ) -> Dict:
        """
        Routes APIを使用して経路を計算

        Args:
            origin: 出発地（住所または座標）
            destination: 目的地（住所または座標）
            travel_mode: 移動手段（DRIVE, WALK, TRANSIT, BICYCLE, TWO_WHEELER）
            compute_alternative_routes: 代替ルートを計算するか

        Returns:
            Dict: Routes APIのレスポンス

        Raises:
            httpx.HTTPStatusError: API呼び出しが失敗した場合
        """
        # 住所を座標に変換
        try:
            origin_lat, origin_lng = await self.geocode_address(origin)
            dest_lat, dest_lng = await self.geocode_address(destination)
        except ValueError as e:
            logger.error(f"Geocoding error: {e}")
            raise

        # Field Maskの構築（TRANSITモードでは追加フィールドを含める）
        field_mask_parts = [
            "routes.distanceMeters",
            "routes.duration",
            "routes.polyline.encodedPolyline",
            "routes.legs",
        ]
        if travel_mode == "TRANSIT":
            field_mask_parts.extend(
                [
                    "routes.legs.steps.transitDetails",
                    "routes.legs.steps.travelMode",
                    "routes.travelAdvisory.transitFare",
                ]
            )

        # Routes APIリクエストヘッダー
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": ",".join(field_mask_parts),
        }

        # リクエストボディ
        payload = {
            "origin": {
                "location": {
                    "latLng": {"latitude": origin_lat, "longitude": origin_lng}
                }
            },
            "destination": {
                "location": {"latLng": {"latitude": dest_lat, "longitude": dest_lng}}
            },
            "travelMode": travel_mode,
            "computeAlternativeRoutes": compute_alternative_routes,
        }

        # TRANSITモード固有の設定
        if travel_mode == "TRANSIT":
            # departureTime: 未指定時は現在時刻をデフォルトで設定
            if departure_time:
                payload["departureTime"] = departure_time
            else:
                payload["departureTime"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            # transitPreferences の設定
            if transit_preferences:
                payload["transitPreferences"] = transit_preferences
        else:
            # TRANSITモード以外はリアルタイムトラフィック考慮を有効化
            payload["routingPreference"] = "TRAFFIC_AWARE"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                logger.info(f"Routes API request payload: {payload}")
                logger.info(f"Routes API request headers: {headers}")

                response = await client.post(
                    self.routes_api_url, json=payload, headers=headers
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Routes API response status: {response.status_code}")
                logger.info(f"Routes API response keys: {list(result.keys())}")
                logger.info(f"Routes API response body: {result}")

                return result
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Routes API error: {e.response.status_code} - {e.response.text}"
                )
                raise

    def format_duration(self, duration_seconds: int) -> str:
        """
        秒を人間が読める形式に変換

        Args:
            duration_seconds: 秒数

        Returns:
            str: "1時間25分" のような形式
        """
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}時間{minutes}分"
        else:
            return f"{minutes}分"

    def format_distance(self, distance_meters: int) -> str:
        """
        メートルを人間が読める形式に変換

        Args:
            distance_meters: メートル

        Returns:
            str: "5.2 km" または "850 m" のような形式
        """
        if distance_meters >= 1000:
            km = distance_meters / 1000
            return f"{km:.1f} km"
        else:
            return f"{distance_meters} m"

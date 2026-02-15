"""
経路検索APIエンドポイント
"""

from fastapi import APIRouter, HTTPException
from app.models.request import RouteRequest
from app.models.response import (
    RouteResponse,
    RouteInfo,
    TransitStep,
    TransitDetails,
    TransitStop,
    FareInfo,
)
from app.services.google_maps import GoogleMapsService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["directions"])


@router.post("/routes", response_model=RouteResponse)
async def calculate_route(request: RouteRequest):
    """
    経路を計算し、所要時間と推奨出発時刻を返す

    Args:
        request: 経路検索リクエスト

    Returns:
        RouteResponse: 経路情報と推奨出発時刻
    """
    try:
        maps_service = GoogleMapsService()

        # TRANSITモード用パラメータの準備
        departure_time_str = None
        transit_prefs = None

        if request.travel_mode == "TRANSIT":
            if request.departure_time:
                departure_time_str = request.departure_time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            if request.transit_preferences:
                transit_prefs = {}
                if request.transit_preferences.routing_preference:
                    transit_prefs["routingPreference"] = (
                        request.transit_preferences.routing_preference
                    )
                if request.transit_preferences.allowed_travel_modes:
                    transit_prefs["allowedTravelModes"] = (
                        request.transit_preferences.allowed_travel_modes
                    )

        # Routes APIで経路を計算
        route_data = await maps_service.compute_route(
            origin=request.origin,
            destination=request.destination,
            travel_mode=request.travel_mode,
            compute_alternative_routes=request.compute_alternative_routes,
            departure_time=departure_time_str,
            transit_preferences=transit_prefs,
        )

        # ルートが見つからない場合
        if not route_data.get("routes"):
            return RouteResponse(
                success=False,
                route=None,
                travel_mode=request.travel_mode,
                error_message="指定された条件でルートが見つかりませんでした",
            )

        # メインルートの情報を抽出
        main_route = route_data["routes"][0]
        duration_seconds = int(main_route["duration"].rstrip("s"))  # "1234s" -> 1234
        distance_meters = main_route["distanceMeters"]

        # 座標情報を抽出（latitude/longitude → lat/lng に変換）
        start_location = {
            "lat": main_route["legs"][0]["startLocation"]["latLng"]["latitude"],
            "lng": main_route["legs"][0]["startLocation"]["latLng"]["longitude"],
        }
        end_location = {
            "lat": main_route["legs"][0]["endLocation"]["latLng"]["latitude"],
            "lng": main_route["legs"][0]["endLocation"]["latLng"]["longitude"],
        }

        # ポリライン情報を取得
        polyline = main_route.get("polyline", {}).get("encodedPolyline")

        # TRANSIT モードの場合、ステップ詳細と運賃を抽出
        transit_steps = None
        fare = None
        if request.travel_mode == "TRANSIT":
            transit_steps = _extract_transit_steps(main_route, maps_service)
            fare = _extract_fare(route_data)

        route_info = RouteInfo(
            duration_seconds=duration_seconds,
            duration_text=maps_service.format_duration(duration_seconds),
            distance_meters=distance_meters,
            distance_text=maps_service.format_distance(distance_meters),
            polyline=polyline,
            start_location=start_location,
            end_location=end_location,
            transit_steps=transit_steps,
            fare=fare,
        )

        # 代替ルートの情報を抽出
        alternative_routes = []
        if request.compute_alternative_routes and len(route_data["routes"]) > 1:
            for alt_route in route_data["routes"][1:]:
                alt_duration = int(alt_route["duration"].rstrip("s"))
                alt_distance = alt_route["distanceMeters"]
                alt_start = {
                    "lat": alt_route["legs"][0]["startLocation"]["latLng"]["latitude"],
                    "lng": alt_route["legs"][0]["startLocation"]["latLng"]["longitude"],
                }
                alt_end = {
                    "lat": alt_route["legs"][0]["endLocation"]["latLng"]["latitude"],
                    "lng": alt_route["legs"][0]["endLocation"]["latLng"]["longitude"],
                }
                alt_polyline = alt_route.get("polyline", {}).get("encodedPolyline")

                alternative_routes.append(
                    RouteInfo(
                        duration_seconds=alt_duration,
                        duration_text=maps_service.format_duration(alt_duration),
                        distance_meters=alt_distance,
                        distance_text=maps_service.format_distance(alt_distance),
                        polyline=alt_polyline,
                        start_location=alt_start,
                        end_location=alt_end,
                    )
                )

        # 推奨出発時刻の計算
        recommended_departure_time = None
        if request.desired_arrival_time:
            recommended_departure_time = request.desired_arrival_time - timedelta(
                seconds=duration_seconds
            )

        return RouteResponse(
            success=True,
            route=route_info,
            alternative_routes=alternative_routes,
            recommended_departure_time=recommended_departure_time,
            travel_mode=request.travel_mode,
            error_message=None,
        )

    except ValueError as e:
        # ジオコーディングエラー
        logger.error(f"Geocoding error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # その他のエラー
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="経路計算中にエラーが発生しました。しばらくしてから再度お試しください。",
        )


def _extract_transit_steps(
    route: dict, maps_service: GoogleMapsService
) -> list[TransitStep]:
    """ルートからTRANSITステップ情報を抽出"""
    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            step_mode = step.get("travelMode", "WALK")
            duration_sec = (
                int(step.get("staticDuration", "0s").rstrip("s"))
                if step.get("staticDuration")
                else 0
            )
            distance_m = step.get("distanceMeters", 0)

            transit_details = None
            raw_td = step.get("transitDetails")
            if raw_td:
                # 乗車駅
                dep_stop_data = raw_td.get("stopDetails", {}).get("departureStop", {})
                dep_stop = (
                    TransitStop(name=dep_stop_data.get("name", ""), location=None)
                    if dep_stop_data.get("name")
                    else None
                )

                # 降車駅
                arr_stop_data = raw_td.get("stopDetails", {}).get("arrivalStop", {})
                arr_stop = (
                    TransitStop(name=arr_stop_data.get("name", ""), location=None)
                    if arr_stop_data.get("name")
                    else None
                )

                # 路線情報
                line_info = raw_td.get("transitLine", {})
                vehicle_info = line_info.get("vehicle", {})

                transit_details = TransitDetails(
                    departure_stop=dep_stop,
                    arrival_stop=arr_stop,
                    departure_time=raw_td.get("stopDetails", {}).get("departureTime"),
                    arrival_time=raw_td.get("stopDetails", {}).get("arrivalTime"),
                    line_name=line_info.get("name"),
                    short_name=line_info.get("nameShort"),
                    vehicle_type=vehicle_info.get("type"),
                    num_stops=raw_td.get("stopCount"),
                )

            steps.append(
                TransitStep(
                    travel_mode=step_mode,
                    duration_text=(
                        maps_service.format_duration(duration_sec)
                        if duration_sec
                        else None
                    ),
                    distance_text=(
                        maps_service.format_distance(distance_m) if distance_m else None
                    ),
                    transit_details=transit_details,
                )
            )
    return steps


def _extract_fare(route_data: dict) -> FareInfo | None:
    """レスポンスから運賃情報を抽出"""
    routes = route_data.get("routes", [])
    if not routes:
        return None
    fare_data = routes[0].get("travelAdvisory", {}).get("transitFare")
    if not fare_data:
        return None
    return FareInfo(
        currency_code=fare_data.get("currencyCode", ""),
        units=fare_data.get("units", "0"),
    )


@router.get("/health")
async def health_check():
    """
    ヘルスチェックエンドポイント

    Returns:
        dict: ステータス情報
    """
    return {
        "status": "ok",
        "service": "Google Directions API Demo",
        "timestamp": datetime.now().isoformat(),
    }

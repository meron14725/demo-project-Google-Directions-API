"""
経路検索APIエンドポイント
"""
from fastapi import APIRouter, HTTPException
from app.models.request import RouteRequest
from app.models.response import RouteResponse, RouteInfo
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

        # Routes APIで経路を計算
        route_data = await maps_service.compute_route(
            origin=request.origin,
            destination=request.destination,
            travel_mode=request.travel_mode,
            compute_alternative_routes=request.compute_alternative_routes
        )

        # ルートが見つからない場合
        if not route_data.get("routes"):
            return RouteResponse(
                success=False,
                route=None,
                travel_mode=request.travel_mode,
                error_message="指定された条件でルートが見つかりませんでした"
            )

        # メインルートの情報を抽出
        main_route = route_data["routes"][0]
        duration_seconds = int(main_route["duration"].rstrip("s"))  # "1234s" -> 1234
        distance_meters = main_route["distanceMeters"]

        # 座標情報を抽出（latitude/longitude → lat/lng に変換）
        start_location = {
            "lat": main_route["legs"][0]["startLocation"]["latLng"]["latitude"],
            "lng": main_route["legs"][0]["startLocation"]["latLng"]["longitude"]
        }
        end_location = {
            "lat": main_route["legs"][0]["endLocation"]["latLng"]["latitude"],
            "lng": main_route["legs"][0]["endLocation"]["latLng"]["longitude"]
        }

        # ポリライン情報を取得
        polyline = main_route.get("polyline", {}).get("encodedPolyline")

        route_info = RouteInfo(
            duration_seconds=duration_seconds,
            duration_text=maps_service.format_duration(duration_seconds),
            distance_meters=distance_meters,
            distance_text=maps_service.format_distance(distance_meters),
            polyline=polyline,
            start_location=start_location,
            end_location=end_location
        )

        # 代替ルートの情報を抽出
        alternative_routes = []
        if request.compute_alternative_routes and len(route_data["routes"]) > 1:
            for alt_route in route_data["routes"][1:]:
                alt_duration = int(alt_route["duration"].rstrip("s"))
                alt_distance = alt_route["distanceMeters"]
                alt_start = {
                    "lat": alt_route["legs"][0]["startLocation"]["latLng"]["latitude"],
                    "lng": alt_route["legs"][0]["startLocation"]["latLng"]["longitude"]
                }
                alt_end = {
                    "lat": alt_route["legs"][0]["endLocation"]["latLng"]["latitude"],
                    "lng": alt_route["legs"][0]["endLocation"]["latLng"]["longitude"]
                }
                alt_polyline = alt_route.get("polyline", {}).get("encodedPolyline")

                alternative_routes.append(RouteInfo(
                    duration_seconds=alt_duration,
                    duration_text=maps_service.format_duration(alt_duration),
                    distance_meters=alt_distance,
                    distance_text=maps_service.format_distance(alt_distance),
                    polyline=alt_polyline,
                    start_location=alt_start,
                    end_location=alt_end
                ))

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
            error_message=None
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
            detail="経路計算中にエラーが発生しました。しばらくしてから再度お試しください。"
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
        "timestamp": datetime.now().isoformat()
    }

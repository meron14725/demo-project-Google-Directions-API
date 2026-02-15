"""
経路検索APIエンドポイント
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.models.request import RouteRequest
from app.models.response import (
    RouteResponse, RouteInfo, TransitStep, TransitDetails, TransitStop, FareInfo
)
from app.services.google_maps import GoogleMapsService, is_japan_region
from app.services.ekispert_service import EkispertService
from app.config import settings
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

        # TRANSITモードの場合、地域を判定して適切なAPIを選択
        if request.travel_mode == "TRANSIT":
            # 座標を取得
            origin_lat, origin_lng = await maps_service.geocode_address(request.origin)
            dest_lat, dest_lng = await maps_service.geocode_address(request.destination)

            # 日本国内かチェック
            if is_japan_region(origin_lat, origin_lng, dest_lat, dest_lng):
                # 駅すぱあとAPIキーが設定されているかチェック
                if not settings.EKISPERT_API_KEY or settings.EKISPERT_API_KEY == "your_ekispert_api_key_here":
                    logger.warning("EKISPERT_API_KEYが未設定です。日本国内のTRANSIT検索にはAPIキーが必要です。")
                    return RouteResponse(
                        success=False,
                        route=None,
                        travel_mode="TRANSIT",
                        error_message="日本国内の公共交通検索には駅すぱあとAPIキーが必要です。.envファイルにEKISPERT_API_KEYを設定してください。"
                    )

                logger.info(f"日本国内のTRANSIT検索: 駅すぱあとAPIを使用")
                print(f"\n=== Using Ekispert API for Japan TRANSIT ===")
                print(f"Origin: {request.origin} ({origin_lat}, {origin_lng})")
                print(f"Destination: {request.destination} ({dest_lat}, {dest_lng})")

                # 駅すぱあとAPIを使用
                try:
                    ekispert_service = EkispertService(settings.EKISPERT_API_KEY)
                    ekispert_response = await ekispert_service.compute_route(
                        origin=request.origin,
                        destination=request.destination,
                        travel_mode="TRANSIT",
                        departure_time=departure_time_str
                    )

                    # レスポンス変換処理
                    return _build_response_from_ekispert(
                        ekispert_response,
                        request,
                        origin_lat,
                        origin_lng,
                        dest_lat,
                        dest_lng
                    )
                except Exception as e:
                    logger.error(f"駅すぱあとAPI呼び出しエラー: {e}")
                    return RouteResponse(
                        success=False,
                        route=None,
                        travel_mode="TRANSIT",
                        error_message=f"駅すぱあとAPIエラー: {str(e)}"
                    )
            else:
                logger.info(f"海外のTRANSIT検索: Google Routes APIを使用")
                print(f"\n=== Using Google Routes API for overseas TRANSIT ===")

        # Routes APIで経路を計算（TRANSITモード以外、または海外のTRANSIT）
        route_data = await maps_service.compute_route(
            origin=request.origin,
            destination=request.destination,
            travel_mode=request.travel_mode,
            compute_alternative_routes=request.compute_alternative_routes,
            departure_time=departure_time_str,
            transit_preferences=transit_prefs
        )

        # ルートが見つからない場合
        if not route_data.get("routes"):
            # APIレスポンスの詳細をログ出力
            error_detail = route_data.get("error", {})
            print(f"\n=== No routes found ===")
            print(f"API Response: {route_data}")

            error_msg = "指定された条件でルートが見つかりませんでした"
            if error_detail:
                error_msg += f" (API Error: {error_detail.get('message', 'Unknown')})"

            return RouteResponse(
                success=False,
                route=None,
                travel_mode=request.travel_mode,
                error_message=error_msg
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
            fare=fare
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


def _extract_transit_steps(route: dict, maps_service: GoogleMapsService) -> list[TransitStep]:
    """ルートからTRANSITステップ情報を抽出"""
    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            step_mode = step.get("travelMode", "WALK")
            duration_sec = int(step.get("staticDuration", "0s").rstrip("s")) if step.get("staticDuration") else 0
            distance_m = step.get("distanceMeters", 0)

            transit_details = None
            raw_td = step.get("transitDetails")
            if raw_td:
                # 乗車駅
                dep_stop_data = raw_td.get("stopDetails", {}).get("departureStop", {})
                dep_stop = TransitStop(
                    name=dep_stop_data.get("name", ""),
                    location=None
                ) if dep_stop_data.get("name") else None

                # 降車駅
                arr_stop_data = raw_td.get("stopDetails", {}).get("arrivalStop", {})
                arr_stop = TransitStop(
                    name=arr_stop_data.get("name", ""),
                    location=None
                ) if arr_stop_data.get("name") else None

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

            steps.append(TransitStep(
                travel_mode=step_mode,
                duration_text=maps_service.format_duration(duration_sec) if duration_sec else None,
                distance_text=maps_service.format_distance(distance_m) if distance_m else None,
                transit_details=transit_details,
            ))
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


def _build_response_from_ekispert(
    ekispert_data: dict,
    request: RouteRequest,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float
) -> RouteResponse:
    """
    駅すぱあとAPIのレスポンスをRouteResponseに変換

    Args:
        ekispert_data: 駅すぱあとAPIのレスポンス
        request: 元のリクエスト
        origin_lat: 出発地の緯度
        origin_lng: 出発地の経度
        dest_lat: 目的地の緯度
        dest_lng: 目的地の経度

    Returns:
        RouteResponse: アプリケーション統一形式のレスポンス
    """
    if not ekispert_data.get("ResultSet", {}).get("Course"):
        return RouteResponse(
            success=False,
            route=None,
            travel_mode="TRANSIT",
            error_message="指定された条件でルートが見つかりませんでした（駅すぱあとAPI）"
        )

    # 最初のルート（最適ルート）を取得
    course = ekispert_data["ResultSet"]["Course"][0]

    # 所要時間（分→秒に変換）
    duration_minutes = course.get("timeTotal", 0)
    duration_seconds = duration_minutes * 60

    # 距離（メートル）
    distance_meters = course.get("distance", 0)

    # 運賃情報
    fare = None
    if course.get("Price"):
        price_data = course["Price"][0]
        fare = FareInfo(
            currency_code="JPY",
            units=str(price_data.get("Oneway", 0))
        )

    # 座標情報
    start_location = {"lat": origin_lat, "lng": origin_lng}
    end_location = {"lat": dest_lat, "lng": dest_lng}

    # ステップ情報を抽出
    transit_steps = _extract_ekispert_steps(course)

    route_info = RouteInfo(
        duration_seconds=duration_seconds,
        duration_text=_format_duration_jp(duration_seconds),
        distance_meters=distance_meters,
        distance_text=_format_distance_jp(distance_meters),
        polyline=None,  # 駅すぱあとはポリライン非対応（フリープラン）
        start_location=start_location,
        end_location=end_location,
        transit_steps=transit_steps,
        fare=fare
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
        alternative_routes=[],  # 駅すぱあとAPIでは複数ルートを個別に返すため、ここでは単一ルートのみ
        recommended_departure_time=recommended_departure_time,
        travel_mode="TRANSIT",
        error_message=None
    )


def _extract_ekispert_steps(course: dict) -> list[TransitStep]:
    """
    駅すぱあとAPIのレスポンスからTRANSITステップ情報を抽出

    駅すぱあとのデータ構造:
    {
      "Route": [
        {
          "Line": {"Name": "JR山手線", "Type": "train"},
          "Point": [
            {"Station": {"Name": "新宿"}},
            {"Station": {"Name": "渋谷"}}
          ],
          "timeOnBoard": 8,
          "distance": 3400
        }
      ]
    }

    Args:
        course: 駅すぱあとのCourseオブジェクト

    Returns:
        list[TransitStep]: TransitStepのリスト
    """
    steps = []
    routes = course.get("Route", [])

    for route_segment in routes:
        # 電車/バス区間
        if "Line" in route_segment:
            line = route_segment["Line"]
            points = route_segment.get("Point", [])

            # 乗車駅と降車駅
            departure_station = None
            arrival_station = None
            if len(points) >= 2:
                departure_station = points[0].get("Station", {}).get("Name", "")
                arrival_station = points[-1].get("Station", {}).get("Name", "")

            # 所要時間（分→秒）
            time_on_board_min = route_segment.get("timeOnBoard", 0)
            duration_seconds = time_on_board_min * 60

            # 距離
            distance_meters = route_segment.get("distance", 0)

            # TransitDetailsの構築
            transit_details = None
            if departure_station or arrival_station:
                dep_stop = TransitStop(
                    name=departure_station,
                    location=None
                ) if departure_station else None

                arr_stop = TransitStop(
                    name=arrival_station,
                    location=None
                ) if arrival_station else None

                transit_details = TransitDetails(
                    departure_stop=dep_stop,
                    arrival_stop=arr_stop,
                    departure_time=None,  # 駅すぱあとAPIでは時刻情報は別途取得が必要
                    arrival_time=None,
                    line_name=line.get("Name", ""),
                    short_name=None,
                    vehicle_type=line.get("Type", "RAIL"),  # train/bus/etc
                    num_stops=route_segment.get("stopCount")
                )

            steps.append(TransitStep(
                travel_mode="TRANSIT",
                duration_text=_format_duration_jp(duration_seconds),
                distance_text=_format_distance_jp(distance_meters),
                transit_details=transit_details
            ))

        # 徒歩区間
        elif "Walk" in route_segment:
            time_walk_min = route_segment.get("timeWalk", 0)
            duration_seconds = time_walk_min * 60
            distance_meters = route_segment.get("distance", 0)

            steps.append(TransitStep(
                travel_mode="WALK",
                duration_text=_format_duration_jp(duration_seconds),
                distance_text=_format_distance_jp(distance_meters),
                transit_details=None
            ))

    return steps


def _format_duration_jp(seconds: int) -> str:
    """
    秒を日本語の人間が読める形式に変換

    Args:
        seconds: 秒数

    Returns:
        str: "1時間25分" のような形式
    """
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


def _format_distance_jp(meters: int) -> str:
    """
    メートルを日本語の人間が読める形式に変換

    Args:
        meters: メートル

    Returns:
        str: "5.2 km" または "850 m" のような形式
    """
    if meters < 1000:
        return f"{meters}m"

    km = meters / 1000
    return f"{km:.1f}km"


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

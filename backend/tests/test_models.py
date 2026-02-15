"""
Pydantic モデルのバリデーションテスト
"""

import pytest
from pydantic import ValidationError
from app.models.request import RouteRequest, TransitPreferences
from app.models.response import (
    RouteInfo,
    RouteResponse,
    TransitStep,
    TransitDetails,
    TransitStop,
    FareInfo,
)


class TestRouteRequest:
    """RouteRequest モデルのテスト"""

    def test_minimal_request(self):
        """必須フィールドのみで作成できる"""
        req = RouteRequest(origin="東京駅", destination="渋谷駅")
        assert req.origin == "東京駅"
        assert req.destination == "渋谷駅"
        assert req.travel_mode == "DRIVE"
        assert req.compute_alternative_routes is False

    def test_full_request(self):
        """全フィールド指定で作成できる"""
        req = RouteRequest(
            origin="東京駅",
            destination="渋谷駅",
            travel_mode="TRANSIT",
            compute_alternative_routes=True,
            desired_arrival_time="2026-02-14T15:00:00",
            departure_time="2026-02-14T14:00:00",
            transit_preferences=TransitPreferences(
                routing_preference="FEWER_TRANSFERS",
                allowed_travel_modes=["TRAIN", "SUBWAY"],
            ),
        )
        assert req.travel_mode == "TRANSIT"
        assert req.transit_preferences.routing_preference == "FEWER_TRANSFERS"
        assert req.transit_preferences.allowed_travel_modes == ["TRAIN", "SUBWAY"]

    def test_missing_origin_raises(self):
        """origin が未指定だとバリデーションエラー"""
        with pytest.raises(ValidationError):
            RouteRequest(destination="渋谷駅")

    def test_missing_destination_raises(self):
        """destination が未指定だとバリデーションエラー"""
        with pytest.raises(ValidationError):
            RouteRequest(origin="東京駅")


class TestRouteResponse:
    """RouteResponse モデルのテスト"""

    def test_success_response(self):
        """成功レスポンスが正しく構築できる"""
        route = RouteInfo(
            duration_seconds=1500,
            duration_text="25分",
            distance_meters=5200,
            distance_text="5.2 km",
            start_location={"lat": 35.6812, "lng": 139.7671},
            end_location={"lat": 35.6580, "lng": 139.7016},
        )
        resp = RouteResponse(
            success=True,
            route=route,
            travel_mode="DRIVE",
        )
        assert resp.success is True
        assert resp.route.duration_seconds == 1500
        assert resp.alternative_routes == []
        assert resp.error_message is None

    def test_failure_response(self):
        """失敗レスポンスが正しく構築できる"""
        resp = RouteResponse(
            success=False,
            route=None,
            travel_mode="DRIVE",
            error_message="ルートが見つかりません",
        )
        assert resp.success is False
        assert resp.route is None
        assert resp.error_message == "ルートが見つかりません"

    def test_transit_step_model(self):
        """TransitStep が正しく構築できる"""
        step = TransitStep(
            travel_mode="TRANSIT",
            duration_text="10分",
            distance_text="5.0 km",
            transit_details=TransitDetails(
                departure_stop=TransitStop(name="東京駅"),
                arrival_stop=TransitStop(name="渋谷駅"),
                line_name="山手線",
                vehicle_type="TRAIN",
                num_stops=5,
            ),
        )
        assert step.transit_details.line_name == "山手線"
        assert step.transit_details.num_stops == 5

    def test_fare_info_model(self):
        """FareInfo が正しく構築できる"""
        fare = FareInfo(currency_code="JPY", units="200")
        assert fare.currency_code == "JPY"
        assert fare.units == "200"

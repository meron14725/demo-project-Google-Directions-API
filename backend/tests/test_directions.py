"""
経路検索APIエンドポイントのテスト
"""

from unittest.mock import AsyncMock, patch

from tests.conftest import (
    MOCK_GEOCODE_RESPONSE,
    MOCK_ROUTES_RESPONSE,
    MOCK_TRANSIT_ROUTES_RESPONSE,
)


def _mock_google_apis(geocode_resp=None, routes_resp=None):
    """Google Maps API 呼び出しをモックするヘルパー"""
    geocode = geocode_resp or MOCK_GEOCODE_RESPONSE
    routes = routes_resp or MOCK_ROUTES_RESPONSE

    async def mock_geocode(*args, **kwargs):
        return (
            geocode["results"][0]["geometry"]["location"]["lat"],
            geocode["results"][0]["geometry"]["location"]["lng"],
        )

    async def mock_compute_route(*args, **kwargs):
        return routes

    return patch.multiple(
        "app.services.google_maps.GoogleMapsService",
        geocode_address=AsyncMock(side_effect=mock_geocode),
        compute_route=AsyncMock(side_effect=mock_compute_route),
    )


class TestCalculateRoute:
    """POST /api/v1/routes のテスト"""

    def test_drive_route_success(self, client):
        """DRIVE モードで正常にルートを取得できる"""
        with _mock_google_apis():
            response = client.post(
                "/api/v1/routes",
                json={
                    "origin": "東京駅",
                    "destination": "渋谷駅",
                    "travel_mode": "DRIVE",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["travel_mode"] == "DRIVE"
        assert data["route"]["duration_seconds"] == 1500
        assert data["route"]["distance_meters"] == 5200
        assert data["route"]["duration_text"] == "25分"
        assert data["route"]["distance_text"] == "5.2 km"

    def test_transit_route_success(self, client):
        """TRANSIT モードで乗り換え情報と運賃を取得できる"""
        with _mock_google_apis(routes_resp=MOCK_TRANSIT_ROUTES_RESPONSE):
            response = client.post(
                "/api/v1/routes",
                json={
                    "origin": "東京駅",
                    "destination": "渋谷駅",
                    "travel_mode": "TRANSIT",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["travel_mode"] == "TRANSIT"

        # 乗り換えステップ
        steps = data["route"]["transit_steps"]
        assert len(steps) == 3
        assert steps[0]["travel_mode"] == "WALK"
        assert steps[1]["travel_mode"] == "TRANSIT"
        assert steps[1]["transit_details"]["line_name"] == "山手線"
        assert steps[1]["transit_details"]["departure_stop"]["name"] == "東京駅"
        assert steps[1]["transit_details"]["arrival_stop"]["name"] == "渋谷駅"
        assert steps[2]["travel_mode"] == "WALK"

        # 運賃
        assert data["route"]["fare"]["currency_code"] == "JPY"
        assert data["route"]["fare"]["units"] == "200"

    def test_no_routes_found(self, client):
        """ルートが見つからない場合は success=False"""
        empty_routes = {"routes": []}
        with _mock_google_apis(routes_resp=empty_routes):
            response = client.post(
                "/api/v1/routes",
                json={
                    "origin": "東京駅",
                    "destination": "渋谷駅",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["route"] is None
        assert "見つかりませんでした" in data["error_message"]

    def test_recommended_departure_time(self, client):
        """到着希望時刻から推奨出発時刻を計算できる"""
        with _mock_google_apis():
            response = client.post(
                "/api/v1/routes",
                json={
                    "origin": "東京駅",
                    "destination": "渋谷駅",
                    "travel_mode": "DRIVE",
                    "desired_arrival_time": "2026-02-14T15:00:00",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_departure_time"] is not None
        # 1500秒 = 25分前
        assert "14:35" in data["recommended_departure_time"]

    def test_geocoding_error_returns_400(self, client):
        """ジオコーディング失敗時に 400 エラーを返す"""
        with patch(
            "app.services.google_maps.GoogleMapsService.compute_route",
            new_callable=AsyncMock,
            side_effect=ValueError("住所のジオコーディングに失敗しました"),
        ):
            response = client.post(
                "/api/v1/routes",
                json={
                    "origin": "不明な場所",
                    "destination": "渋谷駅",
                },
            )
        assert response.status_code == 400

    def test_missing_origin_returns_422(self, client):
        """origin 未指定で 422 バリデーションエラー"""
        response = client.post(
            "/api/v1/routes",
            json={"destination": "渋谷駅"},
        )
        assert response.status_code == 422

    def test_missing_destination_returns_422(self, client):
        """destination 未指定で 422 バリデーションエラー"""
        response = client.post(
            "/api/v1/routes",
            json={"origin": "東京駅"},
        )
        assert response.status_code == 422

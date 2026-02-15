"""
GoogleMapsService ユニットテスト
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.google_maps import GoogleMapsService


class TestFormatDuration:
    """format_duration のテスト"""

    def setup_method(self):
        self.service = GoogleMapsService()

    def test_minutes_only(self):
        assert self.service.format_duration(300) == "5分"

    def test_hours_and_minutes(self):
        assert self.service.format_duration(5100) == "1時間25分"

    def test_zero_minutes(self):
        assert self.service.format_duration(3600) == "1時間0分"

    def test_zero_seconds(self):
        assert self.service.format_duration(0) == "0分"

    def test_large_duration(self):
        assert self.service.format_duration(36000) == "10時間0分"


class TestFormatDistance:
    """format_distance のテスト"""

    def setup_method(self):
        self.service = GoogleMapsService()

    def test_meters(self):
        assert self.service.format_distance(850) == "850 m"

    def test_kilometers(self):
        assert self.service.format_distance(5200) == "5.2 km"

    def test_boundary_1000m(self):
        assert self.service.format_distance(1000) == "1.0 km"

    def test_zero(self):
        assert self.service.format_distance(0) == "0 m"


class TestGeocodeAddress:
    """geocode_address のテスト"""

    @pytest.fixture()
    def service(self):
        return GoogleMapsService()

    async def test_successful_geocode(self, service):
        """正常にジオコーディングできる"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [{"geometry": {"location": {"lat": 35.6812, "lng": 139.7671}}}],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.google_maps.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            lat, lng = await service.geocode_address("東京駅")
            assert lat == 35.6812
            assert lng == 139.7671

    async def test_failed_geocode_raises(self, service):
        """ジオコーディング失敗時にValueErrorを発生させる"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ZERO_RESULTS",
            "results": [],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.google_maps.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            with pytest.raises(ValueError, match="ジオコーディングに失敗"):
                await service.geocode_address("存在しない場所")

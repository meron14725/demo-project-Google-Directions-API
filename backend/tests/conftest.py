"""
テスト共通フィクスチャ
"""

import os
import pytest

# テスト用環境変数を設定（Settings のインスタンス化に必要）
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "test-api-key-for-ci")

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.fixture()
def client():
    """同期テストクライアント"""
    return TestClient(app)


@pytest.fixture()
async def async_client():
    """非同期テストクライアント"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Google Maps API モックレスポンス ---

MOCK_GEOCODE_RESPONSE = {
    "status": "OK",
    "results": [{"geometry": {"location": {"lat": 35.6812, "lng": 139.7671}}}],
}

MOCK_ROUTES_RESPONSE = {
    "routes": [
        {
            "distanceMeters": 5200,
            "duration": "1500s",
            "polyline": {"encodedPolyline": "abc123"},
            "legs": [
                {
                    "startLocation": {
                        "latLng": {"latitude": 35.6812, "longitude": 139.7671}
                    },
                    "endLocation": {
                        "latLng": {"latitude": 35.6580, "longitude": 139.7016}
                    },
                    "steps": [],
                }
            ],
        }
    ]
}

MOCK_TRANSIT_ROUTES_RESPONSE = {
    "routes": [
        {
            "distanceMeters": 8400,
            "duration": "1800s",
            "polyline": {"encodedPolyline": "transit123"},
            "legs": [
                {
                    "startLocation": {
                        "latLng": {"latitude": 35.6812, "longitude": 139.7671}
                    },
                    "endLocation": {
                        "latLng": {"latitude": 35.6580, "longitude": 139.7016}
                    },
                    "steps": [
                        {
                            "travelMode": "WALK",
                            "staticDuration": "180s",
                            "distanceMeters": 200,
                        },
                        {
                            "travelMode": "TRANSIT",
                            "staticDuration": "600s",
                            "distanceMeters": 5000,
                            "transitDetails": {
                                "stopDetails": {
                                    "departureStop": {"name": "東京駅"},
                                    "arrivalStop": {"name": "渋谷駅"},
                                    "departureTime": "2026-02-14T14:00:00Z",
                                    "arrivalTime": "2026-02-14T14:30:00Z",
                                },
                                "transitLine": {
                                    "name": "山手線",
                                    "nameShort": "JY",
                                    "vehicle": {"type": "TRAIN"},
                                },
                                "stopCount": 5,
                            },
                        },
                        {
                            "travelMode": "WALK",
                            "staticDuration": "120s",
                            "distanceMeters": 150,
                        },
                    ],
                }
            ],
            "travelAdvisory": {
                "transitFare": {
                    "currencyCode": "JPY",
                    "units": "200",
                }
            },
        }
    ]
}

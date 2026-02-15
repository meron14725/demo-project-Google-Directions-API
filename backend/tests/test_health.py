"""
ヘルスチェック・ルートエンドポイントのテスト
"""


def test_root_endpoint(client):
    """ルートエンドポイントがアプリ情報を返す"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["docs"] == "/docs"
    assert data["version"] == "1.0.0"


def test_health_check(client):
    """ヘルスチェックが正常に動作する"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

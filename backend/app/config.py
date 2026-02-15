"""
環境変数管理
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Google Maps API設定
    GOOGLE_MAPS_API_KEY: str

    # サーバー設定
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS設定
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite開発サーバー
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # 予備
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# グローバル設定インスタンス
settings = Settings()

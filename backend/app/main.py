"""
FastAPIメインアプリケーション
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.directions import router as directions_router
from app.config import settings
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="Google Directions API Demo",
    description="執事アプリ技術検証プロジェクト - Google Routes APIを使用した経路検索デモ",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(directions_router)


@app.get("/")
async def root():
    """
    ルートエンドポイント

    Returns:
        dict: アプリケーション情報
    """
    return {
        "message": "Google Directions API Demo - 執事アプリ技術検証プロジェクト",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": "1.0.0"
    }


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("Starting Google Directions API Demo...")
    logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("Shutting down Google Directions API Demo...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True
    )

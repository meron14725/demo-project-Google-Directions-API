"""
リクエストモデル
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RouteRequest(BaseModel):
    """経路検索リクエスト"""

    origin: str = Field(..., description="出発地（住所または地名）", example="東京駅")
    destination: str = Field(..., description="目的地（住所または地名）", example="渋谷駅")
    travel_mode: str = Field(
        default="DRIVE",
        description="移動手段 (DRIVE, WALK, TRANSIT, BICYCLE, TWO_WHEELER)",
        example="DRIVE"
    )
    compute_alternative_routes: bool = Field(
        default=False,
        description="代替ルートを計算するか",
        example=False
    )
    desired_arrival_time: Optional[datetime] = Field(
        default=None,
        description="到着希望時刻（ISO8601形式）",
        example="2026-02-14T15:00:00"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "origin": "東京駅",
                "destination": "渋谷駅",
                "travel_mode": "DRIVE",
                "compute_alternative_routes": False,
                "desired_arrival_time": "2026-02-14T15:00:00"
            }
        }

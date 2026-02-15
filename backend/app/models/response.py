"""
レスポンスモデル
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class TransitStop(BaseModel):
    """乗降駅情報"""

    name: str = Field(..., description="駅名")
    location: Optional[Dict[str, float]] = Field(None, description="座標")


class TransitDetails(BaseModel):
    """TRANSIT ステップの詳細情報"""

    departure_stop: Optional[TransitStop] = Field(None, description="乗車駅")
    arrival_stop: Optional[TransitStop] = Field(None, description="降車駅")
    departure_time: Optional[str] = Field(None, description="出発時刻")
    arrival_time: Optional[str] = Field(None, description="到着時刻")
    line_name: Optional[str] = Field(None, description="路線名")
    short_name: Optional[str] = Field(None, description="路線短縮名")
    vehicle_type: Optional[str] = Field(
        None, description="車両タイプ (BUS, SUBWAY, TRAIN 等)"
    )
    num_stops: Optional[int] = Field(None, description="停車駅数")


class TransitStep(BaseModel):
    """TRANSIT ルートの各ステップ"""

    travel_mode: str = Field(..., description="移動手段 (WALK, TRANSIT)")
    duration_text: Optional[str] = Field(None, description="所要時間")
    distance_text: Optional[str] = Field(None, description="距離")
    transit_details: Optional[TransitDetails] = Field(
        None, description="乗り換え詳細（TRANSIT時のみ）"
    )


class FareInfo(BaseModel):
    """運賃情報"""

    currency_code: str = Field(..., description="通貨コード (JPY等)")
    units: str = Field(..., description="金額")


class RouteInfo(BaseModel):
    """ルート情報"""

    duration_seconds: int = Field(..., description="所要時間（秒）")
    duration_text: str = Field(
        ..., description="所要時間（人間が読める形式）", example="25分"
    )
    distance_meters: int = Field(..., description="距離（メートル）")
    distance_text: str = Field(
        ..., description="距離（人間が読める形式）", example="5.2 km"
    )
    polyline: Optional[str] = Field(
        None, description="経路のポリライン（エンコード済み）"
    )
    start_location: Dict[str, float] = Field(..., description="出発地の座標")
    end_location: Dict[str, float] = Field(..., description="目的地の座標")
    transit_steps: Optional[List[TransitStep]] = Field(
        None, description="TRANSIT モードの各ステップ"
    )
    fare: Optional[FareInfo] = Field(None, description="運賃情報")


class RouteResponse(BaseModel):
    """経路検索レスポンス"""

    success: bool = Field(..., description="成功フラグ")
    route: Optional[RouteInfo] = Field(None, description="メインルート情報")
    alternative_routes: List[RouteInfo] = Field(
        default_factory=list, description="代替ルート情報"
    )
    recommended_departure_time: Optional[datetime] = Field(
        None, description="推奨出発時刻"
    )
    travel_mode: str = Field(..., description="移動手段")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "route": {
                    "duration_seconds": 1500,
                    "duration_text": "25分",
                    "distance_meters": 5200,
                    "distance_text": "5.2 km",
                    "polyline": "encoded_polyline_string",
                    "start_location": {"lat": 35.6812, "lng": 139.7671},
                    "end_location": {"lat": 35.6580, "lng": 139.7016},
                },
                "alternative_routes": [],
                "recommended_departure_time": "2026-02-14T14:35:00",
                "travel_mode": "DRIVE",
                "error_message": None,
            }
        }

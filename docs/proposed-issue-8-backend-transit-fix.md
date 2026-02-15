# Proposed Issue #8: TRANSIT モード修正: Field Mask 拡張・departureTime 追加・レスポンスモデル対応

## 概要

Issue #7 の調査結果に基づき、TRANSIT モードで空レスポンス `{}` が返る根本原因を修正する。

## 背景

調査の結果、以下の2つが主要な原因であると判明した：

1. **Field Mask が TRANSIT モードに対応していない**（可能性: 高）
2. **`departureTime` がリクエストに含まれていない**（可能性: 高）

詳細は `docs/investigation-issue-7-transit-empty-response.md` を参照。

## 対応内容

### 1. Field Mask の TRANSIT 対応（`google_maps.py`）

現在は全モード共通の Field Mask を使用している：
```
routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,routes.legs
```

TRANSIT モード時に以下を追加する：
- `routes.legs.steps.transitDetails` — 乗り換え情報（路線名、駅名、出発/到着時刻）
- `routes.legs.steps.travelMode` — 各ステップの移動手段（WALK / TRANSIT）
- `routes.travelAdvisory.transitFare` — 運賃情報

### 2. `departureTime` のリクエスト追加（`google_maps.py`, `request.py`）

- TRANSIT モードではスケジュール依存のため `departureTime` が重要
- 未指定時は現在時刻をデフォルトで設定する
- リクエストモデルに `departure_time` フィールドを追加

### 3. レスポンスモデルの TRANSIT 対応（`response.py`, `directions.py`）

- `RouteInfo` モデルに TRANSIT 固有フィールドを追加：
  - `transit_details`: 乗り換え情報のリスト（路線名、駅名、出発/到着時刻）
  - `fare`: 運賃情報
- `directions.py` のレスポンス処理を TRANSIT レスポンス構造に対応させる

### 4. エラーハンドリングの改善

- 空レスポンス時に原因（運行時間外、経路なし等）を特定しやすいログ出力
- ユーザー向けエラーメッセージの改善

## 対象ファイル

- `backend/app/services/google_maps.py`
- `backend/app/models/request.py`
- `backend/app/models/response.py`
- `backend/app/api/directions.py`

## 関連 Issue

- #7 Routes API v2: TRANSIT モードが空のレスポンスを返す問題（調査）
- #5 Phase 3: 執事機能の実装
- #6 Phase 4: 交通手段比較機能

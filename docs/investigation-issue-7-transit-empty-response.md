# Issue #7 調査報告: Routes API v2 TRANSIT モードが空レスポンスを返す問題

## 調査日: 2026-02-15

---

## 1. 問題の概要

Routes API v2 で `travelMode: "TRANSIT"` を指定すると、HTTP 200 OK が返るにもかかわらず、レスポンスボディが空 `{}` になる。同じ条件で `travelMode: "DRIVE"` は正常に動作する。

---

## 2. 現在の実装の分析

**対象ファイル:** `backend/app/services/google_maps.py`

### 2.1 Field Mask（ヘッダー）

```python
# 現在の実装（83-86行目）
"X-Goog-FieldMask": (
    "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,"
    "routes.legs"
)
```

**問題:** 全モード共通の Field Mask を使用しており、TRANSIT 固有のフィールドが含まれていない。`routes.legs` は TRANSIT でも有効だが、TRANSIT 特有の詳細情報（乗り換え情報、駅名など）が取得できない。

### 2.2 リクエストペイロード

```python
# 現在の実装（90-114行目）
payload = {
    "origin": { "location": { "latLng": { ... } } },
    "destination": { "location": { "latLng": { ... } } },
    "travelMode": travel_mode,
    "computeAlternativeRoutes": compute_alternative_routes
}
# routingPreference は TRANSIT 以外のみ設定（正しい）
if travel_mode != "TRANSIT":
    payload["routingPreference"] = "TRAFFIC_AWARE"
```

**良い点:** `routingPreference: "TRAFFIC_AWARE"` を TRANSIT モードで除外しているのは正しい。

**問題:** `departureTime` がリクエストに含まれていない。TRANSIT モードはスケジュールに依存するため、出発時刻が重要。

---

## 3. 空レスポンスの原因分析

調査の結果、以下の複数の原因が空レスポンスを引き起こしている可能性がある。

### 原因 A: `departureTime` の未指定（**可能性: 高**）

TRANSIT モードは公共交通機関の時刻表に依存する。`departureTime` を指定しない場合、API は現在時刻を使用するが、深夜帯や運行外の時間帯ではルートが見つからず空レスポンスになる。

**Routes API ドキュメントより:**
- TRANSIT では `departureTime` または `arrivalTime` の指定が推奨される
- 未指定の場合は現在時刻がデフォルトで使われるが、運行時間外だと `routes` が空配列になる

### 原因 B: Field Mask の不足（**可能性: 中**）

現在の Field Mask は基本的なフィールドのみ。TRANSIT モード固有のフィールドを要求していないため、API がフィルタリングした結果、返せるデータがなくなっている可能性がある。

**TRANSIT で追加すべき Field Mask:**
- `routes.legs.steps.transitDetails` — 乗り換え情報（路線名、駅名、出発/到着時刻）
- `routes.legs.steps.travelMode` — 各ステップの移動手段（WALK / TRANSIT）
- `routes.travelAdvisory.transitFare` — 運賃情報

### 原因 C: 地域・経路の制約（**可能性: 低〜中**）

Google Issue Tracker に東京エリアでの TRANSIT モードの `ZERO_RESULTS` に関する報告がある（[#35826181](https://issuetracker.google.com/issues/35826181)）。ただし、東京圏は一般的に TRANSIT データが豊富なため、他の原因と複合している可能性が高い。

### 原因 D: `transitPreferences` の未指定（**可能性: 低**）

`transitPreferences` はオプションであり、未指定でも全公共交通手段が対象になる。空レスポンスの直接的な原因にはなりにくい。

---

## 4. DRIVE モードと TRANSIT モードの主要な違い

| 項目 | DRIVE | TRANSIT |
|------|-------|---------|
| `routingPreference` (トップレベル) | `TRAFFIC_AWARE` 等が有効 | **使用不可**（無視される） |
| `departureTime` | オプション | **重要**（スケジュール依存） |
| `arrivalTime` | 未サポート | サポート（7日前〜100日後） |
| `transitPreferences` | 非対応 | オプション（LESS_WALKING, FEWER_TRANSFERS） |
| 中間ウェイポイント | 最大25個 | **未サポート** |
| `routeModifiers` (有料道路回避等) | 対応 | **非対応** |
| 固有のレスポンスフィールド | `tollInfo` | `transitDetails`, `transitFare` |
| Field Mask の違い | 共通フィールドで十分 | TRANSIT 固有フィールドの追加が必要 |

---

## 5. 修正方針

### 修正 1: TRANSIT モード用の Field Mask を拡張する

```python
# TRANSIT の場合、追加のフィールドを含める
if travel_mode == "TRANSIT":
    field_mask = (
        "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,"
        "routes.legs,routes.legs.steps.transitDetails,"
        "routes.legs.steps.travelMode,routes.travelAdvisory.transitFare"
    )
else:
    field_mask = (
        "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,"
        "routes.legs"
    )
```

### 修正 2: `departureTime` をリクエストに追加する

```python
# TRANSIT モードでは出発時刻を設定（未指定の場合は現在時刻）
if travel_mode == "TRANSIT":
    from datetime import datetime, timezone
    payload["departureTime"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

さらに、リクエストモデルに `departure_time` フィールドを追加し、ユーザーが出発時刻を指定できるようにする。

### 修正 3: レスポンス処理を TRANSIT 対応にする

TRANSIT のレスポンスには `transitDetails`（路線名、駅名、乗り換え情報）が含まれるため、`RouteInfo` モデルと `directions.py` のレスポンス処理を拡張する必要がある。

### 修正 4: エラーハンドリングの改善

空レスポンス時に原因を特定しやすいよう、ログ出力とエラーメッセージを改善する。

---

## 6. 推奨アクション

| 優先度 | 対応内容 | 対象ファイル | 新規 Issue |
|--------|----------|-------------|-----------|
| **高** | Field Mask の TRANSIT 対応 | `google_maps.py` | Issue #8 |
| **高** | `departureTime` のリクエスト追加 | `google_maps.py`, `request.py` | Issue #8 |
| **中** | レスポンスモデルの TRANSIT 対応 | `response.py`, `directions.py` | Issue #8 |
| **中** | フロントエンドの TRANSIT 詳細表示 | `RouteInfoCard.tsx` | Issue #9 |
| **低** | `transitPreferences` の対応 | `google_maps.py`, `request.py`, `RouteSearchForm.tsx` | Issue #9 |

---

## 7. 参考資料

- [Routes API v2 computeRoutes リファレンス](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes)
- [Get a transit route | Routes API](https://developers.google.com/maps/documentation/routes/transit-route)
- [TransitPreferences | Routes API](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TransitPreferences)
- [Choose fields to return | Routes API](https://developers.google.com/maps/documentation/routes/choose_fields)
- [Google Issue Tracker #35826181](https://issuetracker.google.com/issues/35826181)

# Issue: TRANSIT モード空レスポンス問題の調査

## 作成日: 2026-02-15

---

## 問題の概要

Google Routes API v2 で `travelMode: "TRANSIT"` を指定すると、HTTP 200 OK が返るにもかかわらず、レスポンスボディが空 `{}` になる。同じ条件で `travelMode: "DRIVE"` は正常に動作する。

## 環境

- **Python バージョン**: 3.9
- **API**: Google Routes API v2 (https://routes.googleapis.com/directions/v2:computeRoutes)
- **テスト経路**: 新宿 → 渋谷駅
- **テスト日時**: 2026-02-15T18:00:00Z

## 現象

### 再現手順

1. サーバーを起動: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. 以下のリクエストを送信:
```bash
curl -X POST "http://localhost:8000/api/v1/routes" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "新宿",
    "destination": "渋谷駅",
    "travel_mode": "TRANSIT",
    "departure_time": "2026-02-15T18:00:00"
  }'
```

### 期待される結果

経路情報を含む正常なレスポンス（DRIVE モードと同様）

### 実際の結果

```json
{
  "success": false,
  "route": null,
  "alternative_routes": [],
  "recommended_departure_time": null,
  "travel_mode": "TRANSIT",
  "error_message": "指定された条件でルートが見つかりませんでした"
}
```

## サーバーログ

### API リクエスト

```
Payload: {
  'origin': {'location': {'latLng': {'latitude': 35.69291279999999, 'longitude': 139.709008}}},
  'destination': {'location': {'latLng': {'latitude': 35.6580339, 'longitude': 139.7016358}}},
  'travelMode': 'TRANSIT',
  'computeAlternativeRoutes': False,
  'departureTime': '2026-02-15T18:00:00Z'
}

Headers: {
  'Content-Type': 'application/json',
  'X-Goog-Api-Key': 'AIzaSyBpkuPWuLP-rKJTdOxaEvB8thgFrfELv0E',
  'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline,routes.legs'
}
```

### API レスポンス

```
Status: 200
Result keys: []
Result: {}
```

**重要**: HTTP ステータスは 200 OK だが、レスポンスボディが完全に空

## 比較: DRIVE モードは正常動作

同じ経路で `travelMode: "DRIVE"` を指定すると、正常にデータが返される:

```json
{
  "success": true,
  "route": {
    "duration_seconds": 1363,
    "duration_text": "22分",
    "distance_meters": 4751,
    "distance_text": "4.8 km",
    "polyline": "ugzxEm{usY...",
    "start_location": {"lat": 35.6929064, "lng": 139.7088707},
    "end_location": {"lat": 35.6577583, "lng": 139.701783}
  }
}
```

## これまでに試したこと

### 1. Python 3.9 対応（修正完了）

**問題**: `FareInfo | None` 型ヒントが Python 3.9 で非サポート
**修正**: `from __future__ import annotations` を追加
**結果**: 型エラーは解消されたが、TRANSIT の問題は未解決

### 2. Field Mask の拡張（効果なし）

**試行 1**: TRANSIT 固有フィールドを追加
```python
field_mask_parts.extend([
    "routes.legs.steps.transitDetails",
    "routes.legs.steps.travelMode",
    "routes.legs.steps.staticDuration",
    "routes.legs.steps.distanceMeters",
    "routes.travelAdvisory.transitFare",
])
```
**結果**: 空レスポンス `{}`

**試行 2**: `routes.legs` の詳細フィールドを明示
```python
field_mask_parts = [
    "routes.distanceMeters",
    "routes.duration",
    "routes.polyline.encodedPolyline",
    "routes.legs.distanceMeters",
    "routes.legs.duration",
    "routes.legs.startLocation",
    "routes.legs.endLocation",
]
```
**結果**: 空レスポンス `{}`

**試行 3**: 最小限の Field Mask
```
'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline,routes.legs'
```
**結果**: 空レスポンス `{}`

### 3. departure_time の明示的指定（効果なし）

- デフォルトの現在時刻
- 未来の時刻（`2026-02-15T18:00:00Z`）

いずれも空レスポンス

## 調査すべき項目

### 優先度: 高

#### 1. Google Routes API v2 の TRANSIT モード公式仕様の確認

**調査内容:**
- [ ] TRANSIT モードで必須/推奨の Field Mask パターン
- [ ] TRANSIT モード固有のリクエストパラメータの制約
- [ ] `departureTime` の形式と有効範囲（過去/未来の制限）
- [ ] `arrivalTime` のサポート状況

**参考ドキュメント:**
- [Get a transit route | Routes API](https://developers.google.com/maps/documentation/routes/transit-route)
- [Choose fields to return | Routes API](https://developers.google.com/maps/documentation/routes/choose_fields)
- [computeRoutes API Reference](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRoutes)

#### 2. 地域・時刻制約の調査

**調査内容:**
- [ ] 東京エリアでの TRANSIT データの可用性
- [ ] 運行時刻外のリクエストでの挙動（深夜帯など）
- [ ] `departureTime` が未来すぎる場合の制限（現在時刻から何日先まで有効か）
- [ ] タイムゾーンの扱い（UTC vs JST）

**テスト:**
- [ ] 現在時刻（UTC）でのリクエスト
- [ ] JST で日中の時刻（例: `2026-02-15T09:00:00Z` = JST 18:00）
- [ ] 別の経路（例: 東京駅 → 新宿）

#### 3. API キーの権限確認

**調査内容:**
- [ ] Google Cloud Console で TRANSIT モードが有効になっているか
- [ ] Routes API v2 の課金設定
- [ ] API キーの制限設定（リファラー、IP アドレス、API 制限）

**確認手順:**
1. Google Cloud Console → APIs & Services → Credentials
2. 使用中の API キー (`AIzaSyBpkuPWuLP-rKJTdOxaEvB8thgFrfELv0E`) の詳細を確認
3. "API restrictions" で Routes API が有効か確認
4. "Billing" で TRANSIT モードの料金が発生しているか確認

### 優先度: 中

#### 4. Field Mask の検証

**調査内容:**
- [ ] すべてのフィールドを返す `*` ワイルドカードのテスト
- [ ] DRIVE モードで使用している Field Mask との比較
- [ ] ネストされたフィールドパスの正しい記法

**テスト:**
```python
# テスト 1: ワイルドカード
'X-Goog-FieldMask': '*'

# テスト 2: DRIVE モードと同じ Field Mask
'X-Goog-FieldMask': 'routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,routes.legs'

# テスト 3: 公式ドキュメントの例をそのまま使用
```

#### 5. レスポンスのエラー情報の確認

**調査内容:**
- [ ] 空レスポンス `{}` の中にエラー情報が含まれていないか
- [ ] HTTP ヘッダーにエラー情報がないか
- [ ] API がサイレントにフィルタリングしている可能性

**改善:**
```python
# google_maps.py の例外処理を強化
print(f"Response headers: {response.headers}")
print(f"Response text: {response.text}")
```

#### 6. 既知の問題・制限の調査

**調査内容:**
- [ ] Google Issue Tracker での TRANSIT モード関連の報告
- [ ] Stack Overflow での類似問題
- [ ] GitHub での Routes API v2 TRANSIT の実装例

**参考:**
- [Google Issue Tracker #35826181](https://issuetracker.google.com/issues/35826181) - 東京エリア TRANSIT `ZERO_RESULTS` 問題

### 優先度: 低

#### 7. 代替 API の検討

**調査内容:**
- [ ] Google Directions API (v1) での TRANSIT モード
- [ ] 他の経路検索 API との比較

## 仮説

### 仮説 1: Field Mask の仕様不適合（可能性: 高）

Routes API v2 の Field Mask は非常に厳密で、パスが完全に一致しないとフィルタリングされる可能性がある。TRANSIT モードでは、DRIVE モードと異なる構造のレスポンスが返されるため、適切な Field Mask が必要。

**検証方法:**
- ワイルドカード `*` を使用してすべてのフィールドを取得
- 公式ドキュメントの Field Mask 例を使用

### 仮説 2: API キーの権限不足（可能性: 中）

TRANSIT モードが API キーで有効化されていない、または課金設定が不足している可能性。

**検証方法:**
- Google Cloud Console で権限を確認
- Billing ログで TRANSIT リクエストが記録されているか確認

### 仮説 3: 地域・時刻の制約（可能性: 中）

東京エリアの TRANSIT データが利用できない、または指定した時刻が有効範囲外の可能性。

**検証方法:**
- 現在時刻（UTC）でのリクエスト
- 別の都市（例: ニューヨーク、サンフランシスコ）でのテスト

### 仮説 4: API のバグまたは仕様変更（可能性: 低〜中）

Routes API v2 が TRANSIT モードで空レスポンスを返すバグがある可能性。

**検証方法:**
- Google Issue Tracker で報告を検索
- API のバージョンやエンドポイントを確認

## 次のステップ

1. **優先度: 高** の調査項目から着手
2. Google Routes API v2 の公式ドキュメントで TRANSIT モードの Field Mask 例を確認
3. API キーの権限を Google Cloud Console で確認
4. ワイルドカード `*` を使用して全フィールドを取得し、実際のレスポンス構造を確認
5. 結果に応じて Field Mask を調整

## 関連ドキュメント

- [docs/investigation-issue-7-transit-empty-response.md](./investigation-issue-7-transit-empty-response.md) - 過去の調査報告
- [docs/proposed-issue-8-backend-transit-fix.md](./proposed-issue-8-backend-transit-fix.md) - バックエンド修正提案
- [docs/proposed-issue-9-frontend-transit-display.md](./proposed-issue-9-frontend-transit-display.md) - フロントエンド修正提案

## コミット履歴

- `681f674` - feat: TRANSIT モード対応 - Field Mask拡張・departureTime追加・乗り換え案内UI
- `262c175` - docs: Issue #7 TRANSIT モード空レスポンス問題の調査報告と修正 Issue 提案

**注**: 過去に修正を試みたが、問題が再発または未解決の状態

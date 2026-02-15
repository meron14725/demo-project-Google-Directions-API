# Proposed Issue #9: フロントエンド TRANSIT 詳細表示・transitPreferences 対応

## 概要

Issue #8 のバックエンド修正に伴い、フロントエンドで TRANSIT モード固有の情報（乗り換え情報、運賃、路線名など）を表示する機能を実装する。

## 背景

Issue #7 の調査で、TRANSIT モードには DRIVE モードにはない固有のレスポンスフィールドがあることが判明した。バックエンドが TRANSIT 詳細情報を返すようになった後、フロントエンドでもこれらの情報を適切に表示する必要がある。

## 対応内容

### 1. TRANSIT 詳細情報の表示（`RouteInfoCard.tsx`）

- 乗り換え情報の表示：
  - 各ステップ（徒歩 → 電車 → 徒歩 → バス → 徒歩 など）の一覧
  - 路線名・駅名・出発時刻・到着時刻
  - 乗り換え回数
- 運賃情報の表示（取得可能な場合）

### 2. `transitPreferences` の UI 対応（`RouteSearchForm.tsx`）

TRANSIT モード選択時に以下のオプションを追加表示する：

- **ルーティング設定**:
  - `LESS_WALKING` — 徒歩を減らす
  - `FEWER_TRANSFERS` — 乗り換えを減らす
- **交通手段フィルタ**:
  - `BUS` — バス
  - `SUBWAY` — 地下鉄
  - `TRAIN` — 電車
  - `LIGHT_RAIL` — ライトレール
  - `RAIL` — 鉄道全般

### 3. 出発時刻 / 到着時刻の入力 UI

- TRANSIT モード選択時に出発時刻の入力フィールドを表示
- 既存の `desired_arrival_time` との連携

### 4. TypeScript 型定義の更新（`types/index.ts`）

- TRANSIT 固有のレスポンス型を追加
- `transitPreferences` リクエスト型を追加

## 対象ファイル

- `frontend/src/components/Result/RouteInfoCard.tsx`
- `frontend/src/components/Form/RouteSearchForm.tsx`
- `frontend/src/types/index.ts`
- `frontend/src/hooks/useDirections.ts`
- `frontend/src/services/api.ts`

## 依存関係

- **Issue #8 の完了が前提** — バックエンドが TRANSIT 詳細情報を返すようになってから実装する

## 関連 Issue

- #7 Routes API v2: TRANSIT モードが空のレスポンスを返す問題（調査）
- #8 TRANSIT モード修正: Field Mask 拡張・departureTime 追加・レスポンスモデル対応
- #6 Phase 4: 交通手段比較機能

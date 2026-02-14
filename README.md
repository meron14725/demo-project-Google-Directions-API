# Google Directions API 技術検証プロジェクト

執事アプリのための技術検証プロジェクト。Google Routes APIを使用して、最短経路の計算と推奨出発時刻の提示を行います。

## 📋 概要

このプロジェクトは、ハッカソンで開発予定の「執事アプリ」の技術的実現可能性を検証するためのものです。

**執事アプリとは？**
- ユーザーの移動予定を把握
- リアルタイム交通情報を考慮
- 「○○分前にXXを出発すれば間に合います！」とリマインド

## 🛠 技術スタック

### バックエンド
- Python 3.11+
- FastAPI (非同期Webフレームワーク)
- Google Routes API
- httpx (非同期HTTPクライアント)

### フロントエンド
- React 18.3+
- TypeScript
- Vite
- Tailwind CSS
- axios

## 📁 プロジェクト構成

```
.
├── backend/               # FastAPIバックエンド
│   ├── app/
│   │   ├── main.py       # エントリーポイント
│   │   ├── config.py     # 環境変数管理
│   │   ├── api/          # エンドポイント
│   │   ├── services/     # Google Maps API統合
│   │   └── models/       # Pydanticモデル
│   ├── venv/             # Python仮想環境
│   └── requirements.txt
├── frontend/             # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/   # UIコンポーネント
│   │   ├── hooks/        # カスタムフック
│   │   ├── services/     # API通信
│   │   └── types/        # TypeScript型定義
│   └── package.json
└── 検証計画.md           # 詳細な実装計画書
```

## 🚀 セットアップ手順

### 1. Google Cloud Platform の設定

#### 1-1. プロジェクト作成
1. https://console.cloud.google.com/ にアクセス
2. 「プロジェクトを作成」をクリック
3. プロジェクト名を入力（例: `butler-app-demo`）

#### 1-2. 課金設定
1. 左メニュー「課金」→「請求先アカウントをリンク」
2. クレジットカード登録
3. **無料枠の確認**
   - Routes API (Pro): 毎月5,000リクエスト無料
   - Maps JavaScript API: 毎月10,000マップロード無料
   - Geocoding API: 毎月10,000リクエスト無料
4. 課金アラート設定（推奨：$20で通知）

#### 1-3. APIの有効化
以下の3つのAPIを有効化してください：
- **Routes API** （経路検索）
- **Maps JavaScript API** （地図表示）
- **Geocoding API** （住所→座標変換）

#### 1-4. APIキーの作成

**バックエンド用キー:**
1. 「APIとサービス」→「認証情報」→「APIキー」作成
2. キーを制限:
   - APIの制限: Routes API, Geocoding API

**フロントエンド用キー:**
1. 再度「APIキー」を作成
2. キーを制限:
   - アプリケーションの制限: HTTPリファラー (`localhost:5173/*`)
   - APIの制限: Maps JavaScript API

### 2. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成（既に作成済み）
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 依存パッケージのインストール（既にインストール済み）
pip install -r requirements.txt

# 環境変数ファイルの作成
cp ../.env.example .env
# .envファイルを編集し、GOOGLE_MAPS_API_KEYにバックエンド用キーを設定
```

**.env の設定例:**
```bash
GOOGLE_MAPS_API_KEY=AIzaSy... (バックエンド用キー)
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 3. フロントエンドのセットアップ

```bash
cd frontend

# 依存パッケージのインストール（既にインストール済み）
npm install

# 環境変数ファイルの作成
cp ../.env.example .env
# .envファイルを編集し、VITE_GOOGLE_MAPS_API_KEYにフロントエンド用キーを設定
```

**.env の設定例:**
```bash
VITE_GOOGLE_MAPS_API_KEY=AIzaSy... (フロントエンド用キー)
VITE_API_BASE_URL=http://localhost:8000
```

## ▶️ アプリケーションの起動

### バックエンドの起動

```bash
cd backend
source venv/bin/activate  # 仮想環境を有効化
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで http://localhost:8000/docs を開くと、自動生成されたAPIドキュメントが表示されます。

### フロントエンドの起動

```bash
cd frontend
npm run dev
```

ブラウザで http://localhost:5173 を開いてアプリケーションにアクセスします。

## 📝 使い方

1. **出発地**と**目的地**を入力（例: 「東京駅」「渋谷駅」）
2. **移動手段**を選択（車、徒歩、公共交通機関、自転車）
3. **到着希望時刻**を入力（オプション）
4. 「経路を検索」ボタンをクリック
5. 右側に結果が表示されます：
   - 所要時間
   - 距離
   - 推奨出発時刻（到着希望時刻を入力した場合）

## 🎯 検証項目

- ✅ 最短経路と所要時間の取得
- ✅ リアルタイムトラフィック情報の反映
- ✅ 推奨出発時刻の計算
- ⏳ 複数交通手段の比較（Phase 4で実装予定）
- ⏳ 代替ルートの取得（Phase 5で実装予定）

## 💰 料金について（2025年3月改定）

### 無料枠（SKUごと/月）

| API | 無料枠 | 超過後の料金 |
|-----|--------|------------|
| Routes API (Pro) | 5,000リクエスト | $8.00 / 1,000 |
| Maps JavaScript API | 10,000マップロード | $7.00 / 1,000 |
| Geocoding API | 10,000リクエスト | $5.00 / 1,000 |

### コスト試算

**開発・技術検証（月間数百リクエスト）:**
- すべて無料枠内 → **$0/月** ✅

**小規模運用（MAU 100人、1人あたり月20回検索）:**
- 月間リクエスト: 2,000回
- Routes API: 2,000リクエスト → 無料枠内 → **$0**
- Geocoding API: 4,000リクエスト → 無料枠内 → **$0**
- Maps JavaScript: 2,000ロード → 無料枠内 → **$0**
- **合計: $0/月** ✅

**中規模運用（MAU 1,000人、1人あたり月10回検索）:**
- 月間リクエスト: 10,000回
- Routes API: (10,000 - 5,000) × $8/1,000 = **$40**
- Geocoding API: (20,000 - 10,000) × $5/1,000 = **$50**
- Maps JavaScript: 10,000ロード → 無料枠内 → **$0**
- **合計: $90/月**

**重要:** 2025年3月1日以降、従来の「月額$200の一律クレジット」は廃止され、SKUごとの無料枠に変更されました。詳細は[検証計画.md](検証計画.md)を参照してください。

## 📚 詳細ドキュメント

- **検証計画.md** - 詳細な実装計画とフェーズ分け
- **APIドキュメント** - http://localhost:8000/docs （バックエンド起動時）

## 🔒 セキュリティ

- `.env`ファイルは`.gitignore`に含まれており、Gitにコミットされません
- APIキーは必ず制限設定を行ってください
- 本番環境では、さらに厳密なセキュリティ設定が必要です

## 📄 ライセンス

このプロジェクトは技術検証用です。

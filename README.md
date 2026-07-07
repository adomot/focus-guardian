# SHIBAKI（サボり絶対しばく君）

目標実現を支援する監視 AI エージェント。集中したい作業中のあなたを Web カメラで見守り、スマホいじり・居眠りなどの「悪習慣」を Gemini のマルチモーダル画像理解で検知して、あなたが選んだ方法（BGM / 言葉）で Alexa から作業に引き戻します。

DevOps × AI Agent Hackathon 2026 提出作品。

## なぜエージェントか

監視対象の「悪習慣」はユーザごとに自由入力で異なるため、事前学習した分類ラベルが存在しません。SHIBAKI は:

1. 自由入力の悪習慣を **Gemini が画像判定可能な検知条件に構造化**し（ADK エージェント）
2. カメラ画像を**継続的に自律判定**して、介入すべきタイミング（継続時間・不在との区別・再介入の抑制）を自分で決め
3. 介入後の画像で**復帰したかを評価・記録**する

という知覚 → 判断 → 行動のループを人間の指示なしに回し続けます。固定ロジックでは作れない、エージェントであることが必然のプロダクトです。

## アーキテクチャ

```mermaid
graph TB
    subgraph Browser[ブラウザ]
        UI[ヒアリングチャット / ダッシュボード]
        Cam[Webカメラ定期キャプチャ]
        FB[フォールバック音声再生]
    end
    subgraph CloudRun[Cloud Run]
        API[FastAPI]
        Flow[ヒアリング ステートマシン]
        SA[StructuringAgent ADK]
        JA[JudgeAgent ADK]
        Policy[InterventionPolicy]
        Speaker[SpeakerAdapter]
    end
    Gemini[Vertex AI Gemini 2.5 Flash Lite]
    TTS[Cloud Text to Speech]
    FS[(Firestore)]
    GCS[(Cloud Storage)]
    VM[Voice Monkey API]
    Echo[Amazon Echo]

    Cam -->|JPEG 60秒毎| API
    UI --> API
    API --> Flow --> SA --> Gemini
    Flow --> TTS --> GCS
    API --> JA --> Gemini
    JA --> Policy --> Speaker --> VM --> Echo
    Policy --> FS
    Flow --> FS
    Speaker -.失敗時.-> FB
```

- **画像はどこにも保存しません**。判定はリクエストスコープで完結し、Firestore に残るのは構造化された判定結果・介入履歴のみです
- カメラ入力（Web カメラ → Nest Cam）と出力デバイス（Alexa → Google Home）は設定変更のみで差し替え可能なアダプタ構成です

## 技術スタック

| 領域 | 技術 |
|---|---|
| AI エージェント | ADK (Agent Development Kit) v2.3 + Vertex AI Gemini 2.5 Flash Lite |
| 音声合成 | Cloud Text-to-Speech (日本語フレーズの MP3 事前生成) |
| 実行基盤 | Cloud Run (単一サービス、フロント同梱) |
| データ | Firestore / Cloud Storage |
| スピーカー連携 | Voice Monkey API v3 (Alexa) |
| バックエンド | Python 3.12 / FastAPI / uv |
| フロントエンド | TypeScript / React 18 / Vite |
| CI/CD | GitHub Actions (test → Cloud Run 自動デプロイ、WIF 認証) |

## 開発

```bash
# バックエンド (フェイクモード: GCP 不要)
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest -q        # テスト
uv run ruff check .     # lint

# フロントエンド
cd frontend
npm install
npm run dev             # http://localhost:5173 (API は :8000 にプロキシ)
```

実サービス接続は環境変数で切り替えます（`backend/app/config.py` 参照）:
`REPOSITORY_BACKEND=firestore` / `AGENTS_BACKEND=adk` / `ASSETS_BACKEND=gcs` / `SPEAKER_ADAPTER=voicemonkey`

## デプロイ

main ブランチへの push で GitHub Actions がテスト → Cloud Run デプロイ → ヘルスチェックまで自動実行します。初期セットアップは `scripts/setup_gcp.sh` と `HUMAN_TODO.md` を参照。

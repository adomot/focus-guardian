# 作業分担リスト（2026-07-05 更新）

## ✅ 完了済み

- コード実装一式（バックエンド・フロントエンド・テスト24件・CI/CD）
- 公開リポジトリ https://github.com/adomot/focus-guardian （CI グリーン）
- Docker イメージのビルド・起動検証（本番同等構成）
- gcloud CLI のインストール（`brew install google-cloud-sdk` 済み）
- BGM 3曲の自作生成（`assets/bgm/*.mp3`、ライセンスフリー）
- アーキテクチャ図 `docs/architecture.png`（Proto Pedia アップロード用）
- Proto Pedia 下書き `docs/protopedia-draft.md` / デモ動画台本 `docs/demo-video-script.md`
- ハッカソンエントリー / Proto Pedia アカウント（あなたが完了）

## 🙋 あなたにしかできない作業（上から順に）

### A. アカウント認証系（私は代行禁止）

1. **gcloud 認証**: このセッションで `! gcloud auth login` と `! gcloud auth application-default login` を実行（ブラウザで Google ログイン）
2. **GCP プロジェクト作成 + 課金有効化**: https://console.cloud.google.com/ でプロジェクト作成 → 課金アカウント紐付け（クーポン対象外だったので自費 or 新規無料トライアル。試算: 数百円/月）
3. **Voice Monkey**: https://voicemonkey.io に Amazon アカウントでログイン → Alexa アプリでスキル有効化 → Speaker デバイス作成 → **Alexa アプリでルーティン設定**（トリガー: Smart Home → Alexa Voice Monkey v3 → 作成した Speaker / アクション: open Voice Monkey + 実機 Echo 指定）→ https://app.voicemonkey.io/tokens でトークン発行
4. **GitHub Secrets 登録**: リポジトリ Settings > Secrets and variables > Actions（値は下記 B-1 のスクリプトが出力）

### B. 認証さえ済めば私がやれる作業（合図をください）

1. `./scripts/setup_gcp.sh <PROJECT_ID> adomot/focus-guardian` の実行（API 有効化・Firestore・バケット・WIF・シークレット作成）→ GitHub Secrets 用の値を出力
2. BGM のバケットアップロード（`gcloud storage cp assets/bgm/*.mp3 ...`）
3. Voice Monkey トークンの Secret Manager 登録（トークン文字列をもらえれば）
4. タスク 1.2 実機スパイク（ADK + Vertex Gemini の実行 / Cloud TTS 日本語生成 / Voice Monkey announce 疎通）
5. デプロイ実行（push）と、デプロイ URL でのブラウザ E2E 確認
6. gh CLI での GitHub Secrets 登録代行（`gh secret set`。値をもらえれば私が入れます）

### C. 提出まわり（締切 7/10 23:59）

1. **デモ動画の撮影・編集**（台本: `docs/demo-video-script.md`）→ YouTube/Vimeo にアップ（あなた）
2. **Proto Pedia 登録**（下書き: `docs/protopedia-draft.md`、図: `docs/architecture.png`）→ フォーム入力・公開はあなた（ログインが必要なため）
3. **最終応募フォーム**（Google Form）提出（あなた）

## 今すぐ動かして遊ぶ（ローカル・GCP不要）

http://localhost:8000 でフェイクモードのサーバが起動中です（判定は常に「集中」）。
止まっていたら: `cd backend && STATIC_DIR=../frontend/dist uv run uvicorn app.main:app --port 8000`

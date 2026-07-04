# リサーチと設計判断

## 概要
- **機能**: `focus-guardian-agent`
- **ディスカバリー範囲**: 新規機能（グリーンフィールド、フルディスカバリー実施）
- **主要な調査結果**:
  - ADK は 2026-05 に 2.0 が GA（最新 v2.3.0）。1.x 前提の記事が多く破壊的変更に注意。公式の Firestore SessionService は存在しない
  - Gemini は `gemini-2.5-flash-lite` + 画像リサイズ（長辺 ≤768px）で 1 判定 ≈ $0.0001。無料枠は送信画像が学習利用されるため Web カメラ用途では不可（有償枠 or Vertex AI 必須）
  - Voice Monkey は v3 API が現行（`api-v3.voicemonkey.io`）。Free プランは 200 リクエスト/月。日本語 TTS は公開ドキュメントに明記なく要実機確認 → 音声は自前生成 MP3 の URL 再生で回避可能

## リサーチログ

### ADK (Agent Development Kit) の現行仕様
- **コンテキスト**: エージェント中核に ADK を採用するための最新仕様確認
- **参照したソース**: https://pypi.org/project/google-adk/ / https://adk.dev/2.0/ / https://adk.dev/agents/llm-agents/ / https://adk.dev/deploy/cloud-run/ / https://github.com/google/adk-python
- **調査結果**:
  - 最新安定版 Python v2.3.0（2026-06-18）、Python >= 3.10。ドキュメントは `google.github.io/adk-docs` から `adk.dev` へ移行済み
  - v2.2.0 で `LlmAgent` のデフォルトモデルが `gemini-3-flash-preview` に変更（`gemini-2.5-flash` は 2026-10-16 シャットダウン予定 → モデルは明示指定する）
  - マルチエージェント: 制御ごと移譲は `sub_agents`、結果だけ欲しい場合は `AgentTool`。ワークフローは `SequentialAgent` 等
  - `output_schema`（Pydantic）で構造化出力可。ただし **tools との同時使用は特定モデルのみサポート**（Issue #701）。「ツール実行エージェントと整形専用エージェントを分離せよ」が公式ガイダンス
  - Cloud Run デプロイ: `get_fast_api_app()` が FastAPI インスタンスを返し独自ルートを追加できる（自前 API と同居可能）
  - SessionService は InMemory / VertexAi / Database の3種。**Firestore 用は公式に存在せず** `BaseSessionService` のカスタム実装が定石
  - Cloud Run + InMemorySessionService は再起動・スケールアウトでセッション消失、DB 接続失敗時に InMemory へサイレントフォールバックして他ユーザーのセッションが混ざった事故報告あり（Discussion #1148）
- **影響**: 判定エージェントは「output_schema のみ・ツールなし」の単発呼び出しとし、ADK セッション永続化に依存しない設計にする（後述の設計判断参照）。モデル名は設定で明示指定

### Gemini 画像理解による行動分類
- **コンテキスト**: 1分毎の定期判定を低コスト・低レイテンシで回すためのモデル・入力形式・料金の確認
- **参照したソース**: https://ai.google.dev/gemini-api/docs/models / https://ai.google.dev/gemini-api/docs/image-understanding / https://ai.google.dev/gemini-api/docs/tokens / https://ai.google.dev/gemini-api/docs/pricing / https://ai.google.dev/gemini-api/docs/structured-output / https://ai.google.dev/gemini-api/docs/terms
- **調査結果**:
  - 推奨モデルは `gemini-2.5-flash-lite`（最速・最安、画像入力 $0.10/M tok）。`gemini-2.0` 系は 2026-06-01 シャットダウン済み
  - 画像は inline base64 が最適（毎回異なる静止画のため Files API 不要）。**両辺 ≤384px なら 258 トークン固定**、768×768 タイル毎に 258 トークン加算 → 送信前リサイズでコスト固定化
  - コスト試算: 1 判定 ≈ $0.0001、1分毎 × 24h でも約 $0.13/日
  - 構造化出力は `response_schema` + **enum サポート**あり → `state: enum[focused, smartphone, sleeping, absent]` を強制可能。出力の Pydantic バリデーションは必須
  - 無料枠: flash-lite ≈ 15 RPM / 1,000 RPD（非公式値）で 24h 稼働には不足。**かつ無料枠は送信画像が Google のプロダクト改善に使用され人間レビューもあり得る** → 顔が写る本ユースケースでは不可
  - Vertex AI 経由（`genai.Client(vertexai=True)`）なら Cloud Run のサービスアカウントが ADC として機能し API キー管理不要、顧客データは学習に不使用
  - プロンプト: few-shot 2〜3 例推奨、曖昧ケース（離席 vs 画角外）の判定基準を明文化、確信度は自己申告（較正されないため閾値未満は unknown 扱いにする）
- **影響**: Vertex AI 経由 + `gemini-2.5-flash-lite` + クライアント側リサイズ + enum 構造化出力を採用。ハッカソン配布の $300 クレジットで賄える

### Voice Monkey (Alexa 出力)
- **コンテキスト**: サーバの REST 呼び出しで Echo に発話・音声再生させる手段の検証
- **参照したソース**: https://voicemonkey.io/docs/api / https://voicemonkey.io/docs/api/announcement.html / https://voicemonkey.io/docs/media.html / https://voicemonkey.io/pricing / https://voicemonkey.io/docs/getting-started/add-device.html
- **調査結果**:
  - 現行は **v3 API**（`https://api-v3.voicemonkey.io`）。v2 は非推奨。認証は単一トークン（`Authorization: Bearer` 推奨）
  - `/announce` で TTS（`speech`）と **MP3 URL 再生（`audio`）** の両方が可能。`background_audio` で BGM 重畳も可
  - Free プラン: **200 API リクエスト/月**、Speaker 5台。外部 HTTPS URL の音声再生は Free でも可（Media Library アップロードは有償のみ）
  - 音声クリップは ~240 秒目安 → 「BGM を流す」は数分のクリップ再生として設計（常時ストリーミングではない）
  - 日本マーケットプレイス対応。ただし **TTS の ja-JP 音声は公開ドキュメントに明記なし（要 Playground 実機確認）**
  - セットアップ: スキル有効化 + コンソールで Speaker デバイス作成 + **Echo 1台ごとに Alexa アプリでルーティン手動設定が必要**
  - 429（バーストスロットル / 月次クォータ超過）に指数バックオフ推奨。実行ログは Free で直近10件
  - 代替手段: Amazon 公式 API は存在せず、Cookie ベース非公式 API（alexa_media_player 等）は 2025-11 以降障害多発。**2026年時点で Voice Monkey が事実上の第一候補**
- **影響**: 日本語 TTS リスクを回避するため、言葉通知は Cloud Text-to-Speech で MP3 を事前生成し `audio` パラメータで URL 再生する方式を主経路にする。Voice Monkey 失敗時はブラウザ再生にフォールバック（要件 4.8）

## アーキテクチャパターン評価

| 選択肢 | 説明 | 強み | リスク / 制限 | 備考 |
|--------|------|------|---------------|------|
| 単一 Cloud Run サービス + ポート/アダプタ | FastAPI (ADK 同居) が API・静的フロント・エージェント実行を担い、カメラ/スピーカーを Adapter で抽象化 | 構成最小、デプロイ1本、6日で完成可能。要件の差し替え可能性(2.3, 4.9)を Adapter で満たす | 単一障害点。in-memory 状態はインスタンス数1が前提 | **採用** |
| フロント(Hosting) + API(Cloud Run) 分離 | Firebase Hosting + Cloud Run バックエンド | CDN 配信、責務分離 | CORS・デプロイ2系統で工数増。ハッカソン規模で利点薄い | 却下 |
| Pub/Sub + Cloud Scheduler による判定ループ分離 | フレーム受信と判定を非同期分離 | スケール耐性 | 画像の永続化が必要になり要件 7.1（画像非永続化）と衝突。レイテンシ増 | 却下 |

## 設計判断

### 判断: ADK エージェントの粒度と ADK セッション非依存
- **コンテキスト**: 判定・構造化・介入を ADK でどう分割するか。Cloud Run のステートレス性と ADK セッション永続化の問題
- **検討した代替案**:
  1. 全処理を単一 LlmAgent + tools（介入もツール呼び出しで LLM が決定）
  2. 判定 = output_schema 専用エージェント、介入判断 = 決定的ポリシーコード
- **選択したアプローチ**: 案2。`StructuringAgent`（悪習慣→検知条件、output_schema）と `JudgeAgent`（画像→状態分類、output_schema）は ADK LlmAgent の単発実行（毎回新規 InMemory セッション）。介入の発火判断（閾値・再介入抑制）は `InterventionPolicy` の決定的コードで行い、状態は Firestore のセッションドキュメントに置く
- **根拠**: output_schema + tools 併用はモデル依存の制約があり（ADK Issue #701）、公式も整形専用エージェント分離を推奨。介入の「1回だけ」ルール（4.4, 4.5）は決定性が必要でテスト容易性も高い。ADK セッションを会話状態に使わないため FirestoreSessionService のカスタム実装が不要になり、Cloud Run のセッション消失・混在リスクを構造的に排除
- **トレードオフ**: LLM が介入ツールを直接叩く派手さはないが、「判定の自律性は LLM、発火の確実性はコード」で信頼性を優先
- **フォローアップ**: ADK v2.3 の output_schema 挙動を実装初日に実機確認（schema 無視の報告 Issue #3969 があるため instruction にも形式を明記）

### 判断: ヒアリングは決定的ステートマシン + LLM は構造化のみ
- **コンテキスト**: 要件1は固定フロー（質問順序・選択肢が確定）であり、自由対話ではない
- **検討した代替案**:
  1. LlmAgent に固定フローを instruction で守らせる
  2. バックエンドの明示的ステートマシンがフローを制御し、自由入力の解釈（悪習慣→検知条件の構造化）のみ Gemini を使う
- **選択したアプローチ**: 案2。`HearingFlowService` が step enum（GOAL → HABIT → NOTIFY_TYPE → BGM_SELECT/PHRASE → MORE_HABITS → DONE）で遷移を制御し、HABIT 入力時に `StructuringAgent` を呼ぶ
- **根拠**: LLM にフロー遵守を任せると要件 1.10（想定外入力で同一質問を再提示）の保証が困難。ステートマシンなら受け入れ基準がそのままユニットテストになる
- **トレードオフ**: 「bot が全部 LLM」という見た目の派手さはないが、UX は要件の会話例と完全に一致する

### 判断: 判定トリガーはフレーム受信駆動（別スケジューラなし）
- **コンテキスト**: 「判定周期」(3.1) の実現方法。画像を永続化しない制約 (7.1)
- **検討した代替案**:
  1. Cloud Scheduler / バックグラウンドループが定期的に最新フレームを判定
  2. ブラウザのフレーム POST を判定トリガーとし、同一リクエスト内で 判定→介入→応答 を完結
- **選択したアプローチ**: 案2。ブラウザが設定間隔（デフォルト 60 秒）で POST し、サーバは `CameraSource.get_latest_frame()` 経由で画像を取得して判定、結果と介入指示を同期レスポンスで返す
- **根拠**: 画像がリクエストスコープを出ないため 7.1（非永続化）を構造的に保証。ブラウザフォールバック再生（4.8）もレスポンスで即座に指示できる。Cloud Run の min-instances 0 でもコールドスタートの影響が1リクエストに閉じる
- **トレードオフ**: ブラウザタブが閉じると監視が止まる（Web カメラ方式では本質的に同じ）。Nest Cam 移行時は `NestCamSource` + 内部スケジューラの追加になるが、`CameraSource` 抽象で判定パイプラインは無変更
- **フォローアップ**: Cloud Run は `max-instances=1` で運用（最新フレームの in-memory 参照は使わずリクエストスコープで完結するため必須ではないが、介入の重複発火防止を単純化）

### 判断: 言葉通知は Cloud Text-to-Speech で MP3 事前生成 + Voice Monkey の audio URL 再生
- **コンテキスト**: Voice Monkey の TTS は ja-JP 対応が公開ドキュメントで未確認（リスク）
- **検討した代替案**:
  1. Voice Monkey の `speech` パラメータ（Polly TTS）に日本語を渡す
  2. Google Cloud Text-to-Speech でフレーズの MP3 をヒアリング完了時に生成して GCS に保存し、介入時は `audio` に公開 URL を渡す
- **選択したアプローチ**: 案2 を主経路、案1 は実機確認が取れれば簡略化オプション
- **根拠**: ja-JP の不確実性を排除。さらに Cloud TTS はハッカソンの「Google Cloud AI 技術」リスト掲載技術であり要件アピールにもなる。介入時のレイテンシも事前生成で最小化
- **トレードオフ**: GCS バケット（公開読み取り）と生成ステップが増える
- **フォローアップ**: Voice Monkey Playground で ja-JP ボイスの有無を初日に確認

### 判断: Gemini 呼び出しは Vertex AI 経由（ADC）
- **コンテキスト**: 無料枠は画像が学習利用され顔が写る用途に不適。API キー管理も避けたい
- **選択したアプローチ**: `genai.Client(vertexai=True, project=..., location=...)` 相当を ADK のモデル設定で使用。Cloud Run のサービスアカウントの ADC で認証
- **根拠**: 学習不使用・キー管理不要・ハッカソン配布 $300 クレジットで賄える。要件 7.4（シークレット管理）の対象が Voice Monkey トークンのみに減る
- **トレードオフ**: ローカル開発時に `gcloud auth application-default login` が必要

## リスクと緩和策
- **Voice Monkey Free 200 リクエスト/月**: 介入時のみ呼び出す設計（フレーム毎ではない）ためデモ用途なら収まる見込みだが、開発中のテスト消費に注意。枯渇時は Hobby ($6.99/月) へ課金 or ブラウザフォールバックで審査継続可能
- **Voice Monkey は非公式サードパーティ SaaS**: 障害時はブラウザ再生フォールバック（要件 4.8）が常設の保険。デモ動画は事前収録で担保
- **ADK 2.x の情報鮮度**: 1.x 前提のサンプルが多い。実装は adk.dev の現行ドキュメントのみを正とし、初日に「output_schema 単発実行」の縦串を動かして検証する
- **Gemini 判定精度（誤検知）**: 確信度閾値（既定 0.7 未満は判定保留）+ 連続 N 回（既定 2 回）検知で介入発火。few-shot 例をプロンプトに含める
- **Cloud Run コールドスタート**: フレーム POST 間隔 60 秒に対しコールドスタート数秒は許容範囲。デモ時は min-instances=1 に引き上げ可能

## 参考文献
- [ADK 公式ドキュメント](https://adk.dev/) — エージェント実装・Cloud Run デプロイの正
- [google-adk PyPI](https://pypi.org/project/google-adk/) — バージョン確認
- [Gemini API: Image understanding](https://ai.google.dev/gemini-api/docs/image-understanding) — 画像入力仕様・トークン計算
- [Gemini API: Structured output](https://ai.google.dev/gemini-api/docs/structured-output) — enum 構造化出力
- [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms) — 無料枠/有償枠のデータ利用ポリシー
- [Voice Monkey API v3 Docs](https://voicemonkey.io/docs/api) — announce/trigger 仕様・認証・スロットル
- [Voice Monkey Pricing](https://voicemonkey.io/pricing) — プラン制限
- [Cloud Text-to-Speech](https://cloud.google.com/text-to-speech) — 日本語フレーズ MP3 生成

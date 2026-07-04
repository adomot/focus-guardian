# DevOps × AI Agent Hackathon 2026 — 要件まとめ

出典: https://findy.notion.site/devops-ai-agent-hackathon-2026（2026-07-04 取得）

## ⚠️ 最重要: 締切

- **作品提出締切: 2026/7/10（金）23:59** ← 残り約6日
- 参加登録も同日 7/10（金）23:59 まで（Findy Conference の申込ページからエントリー）
- 再提出は可能（最終応募のタイムスタンプが最新のものが審査対象）

## 概要

- 主催: Findy / メインスポンサー: グーグル・クラウド・ジャパン、Gold: Elasticsearch
- テーマ: Google Cloud の AI 技術を必須とした AI エージェントの「企画→開発→デプロイ→運用」一気通貫
- コンセプト: **つくる**（Google Cloud AI 中核の独創的エージェント）/ **まわす**（GitHub 連携・CI/CD で継続改善）/ **とどける**（Cloud Run 等へのデプロイで本番品質）
- 賞金総額 200万円 / 決勝: 8/19（水）Google 渋谷オフィスに選抜10チーム招待

## 参加要件

- 日本居住の18歳以上、個人・チームどちらも可
- 個人の私的活動としての参加（企業の業務・代表としての参加は不可）
- 公務員等、賞金受領に制限がある職務の人は参加不可

## 開発要件（技術要件）

### 必須①: Google Cloud アプリケーション実行プロダクト（1つ以上）

- App Engine / Google Compute Engine
- Google Kubernetes Engine (GKE)
- **Cloud Run** / Cloud Functions
- Cloud TPU / GPU

### 必須②: Google Cloud AI 技術（1つ以上）

- Gemini Enterprise Agent Platform（旧 Vertex AI）
- **Gemini API**（Agent Platform 経由推奨、直接利用も可）
- Gemma / Imagen / Agent Builder
- **ADK (Agents Development Kit)**
- Speech-to-Text / Text-to-Speech API
- Vision AI / Natural Language AI / Translation AI API

### 任意

- Flutter / Firebase / Veo / Elasticsearch（スポンサー、Elastic Agent Builder 活用特典あり）ほか自由

## 審査基準（5項目）

1. **AIエージェントが価値の中心か** — 自律的な判断・タスク実行があるか、"エージェントである必然性"
2. **課題へのアプローチ力** — 課題・背景・対象ユーザー・提供価値のストーリーの一貫性、妥当性、新規性
3. **ユーザビリティ** — 直観的に使える機能・デザイン
4. **実用性・体験価値** — 課題解決への実効性、突き抜けた体験価値は加点
5. **実装力** — 技術選定・構成の納得度、拡張性、実運用への配慮

## 提出物（3点必須）

1. **GitHub リポジトリ URL（公開リポジトリ）**
2. **デプロイ済みプロジェクトの URL**（動作確認できる状態を維持）
3. **Proto Pedia 登録作品の URL**（要アカウント作成）

最終応募は作品提出フォーム（Google Form）から。

### Proto Pedia 登録の必須項目

- 作品タイトル / 概要
- **動画**（YouTube か Vimeo の URL）
- **システム構成**（アーキテクチャ図のアップロード必須）
- 開発素材（使用ツール）
- タグ（`findy_hackathon` 必須）
- ストーリー（①解決したい課題と背景 ②想定ユーザー ③プロダクトの特徴）
- 画像（任意・最大5枚）/ メンバー登録・関連URL（任意）

## スケジュール

| フェーズ | 日程 |
|---|---|
| 参加登録 | 4/27 10:00 〜 **7/10 23:59** |
| 作品提出締切 | **7/10（金）23:59** |
| 一次審査（事務局） | 7/13〜7/17 |
| 二次審査（外部有識者） | 7/21〜7/24 |
| 結果発表・決勝進出10チーム告知 | 7/30（木） |
| 最終ピッチ | 8/19（水）Google 渋谷オフィス |
| アフターイベント | 9月予定（オンライン） |

## その他

- 参加申込者に Google Cloud クレジット $300 クーポン配布（先着・数量限定）
- 1人で複数作品の提出可
- チーム提出は代表者のみ Proto Pedia アカウントで可（最終応募フォームに全員の氏名記載必須）
- 知的財産権は参加者に帰属（主催者は運営・広報目的の掲載権を持つ）
- SNS ハッシュタグ: `#findy_hackathon`

## 作品づくりの実質的な必須構成（要件から逆算）

- Gemini API または ADK を中核にした**自律的に判断・実行する**エージェント
- **Cloud Run へのデプロイ**（審査期間中は稼働維持が必要）
- **GitHub 公開リポジトリ + CI/CD**（「まわす」コンセプト＝DevOps 実践が評価軸）
- アーキテクチャ図・デモ動画・課題/ユーザー/特徴のストーリーを提出物として用意

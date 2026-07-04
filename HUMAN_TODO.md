# あなたにやってもらう作業リスト

コードは全て実装済み。以下は**人間にしかできない作業**です。上から順に進めてください。
所要時間の目安: 合計 2〜3 時間（待ち時間除く）。

## 0. ハッカソン登録（締切 7/10 23:59・最優先）

- [ ] Findy Conference の申込ページからハッカソンにエントリー
- [ ] Google Cloud $300 クレジットクーポンを受け取る（先着・数量限定なので早めに）
- [ ] Proto Pedia アカウント作成 → https://protopedia.net/

## 1. GitHub リポジトリの公開

- [ ] 公開リポジトリを作成して push（コマンドは下記。リポジトリ名は任意、例: focus-guardian）

```bash
cd ~/company/hackathon-findy
gh repo create focus-guardian --public --source=. --push
```

※ 私（Claude）に「push していい」と言ってもらえれば代行します。

## 2. GCP セットアップ（$300 クレジット適用後）

- [ ] gcloud CLI をインストール: `brew install google-cloud-sdk`
- [ ] `gcloud auth login` と `gcloud auth application-default login`
- [ ] GCP プロジェクトを作成し、課金を有効化（クレジット適用）
- [ ] セットアップスクリプトを実行（API 有効化・Firestore・バケット・WIF・シークレットを一括作成）:

```bash
./scripts/setup_gcp.sh <PROJECT_ID> <GitHubユーザ名/リポジトリ名>
```

- [ ] スクリプト末尾に表示される 5 つの値を GitHub リポジトリの Settings > Secrets and variables > Actions > New repository secret に登録

## 3. Voice Monkey（Alexa 出力）

- [ ] https://voicemonkey.io で Login with Amazon → アカウント連携
- [ ] Alexa アプリで Voice Monkey スキルを有効化
- [ ] https://app.voicemonkey.io/speakers で Speaker デバイスを作成（名前例: focus-guardian）
- [ ] Alexa アプリでルーティンを作成: トリガー「Smart Home → Alexa Voice Monkey v3 → 作成した VM Speaker」、アクション「open Voice Monkey」+ 鳴らしたい Echo 実機を指定
- [ ] https://app.voicemonkey.io/tokens でトークンを発行し、シークレットに設定:

```bash
echo -n "<TOKEN>" | gcloud secrets versions add voicemonkey-token --data-file=-
```

- [ ] Speaker のデバイス ID を GitHub Secret `VOICEMONKEY_DEVICE` に登録
- [ ] （確認）API Playground https://voicemonkey.io/docs/api/playground で announce を1回試す

## 4. BGM 音源の用意

- [ ] フリー音源（例: DOVA-SYNDROME、甘茶の音楽工房など商用可のもの）から3曲を MP3 で入手し、以下の名前で `assets/bgm/` に置く:
  - `focus.mp3`（集中できるBGM）/ `nature.mp3`（自然音）/ `uptempo.mp3`（アップテンポ）
- [ ] バケットにアップロード:

```bash
gcloud storage cp assets/bgm/*.mp3 gs://<PROJECT_ID>-focus-guardian-assets/bgm/
```

## 5. 初回デプロイの確認

- [ ] 2〜4 が終わったら main に push（または GitHub Actions の Deploy を手動再実行）
- [ ] Actions の Deploy が緑になり、表示された URL でアプリが開くことを確認
- [ ] ここで私に「デプロイ URL で動作確認して」と言ってもらえれば、ブラウザで E2E 確認します

## 6. 提出物（締切 7/10 23:59）

- [ ] デモ動画の撮影（実演: ヒアリング → 監視 → スマホいじり → Echo から BGM）→ YouTube か Vimeo に限定公開でアップ
- [ ] Proto Pedia に作品登録: タイトル / 概要 / 動画 URL / システム構成図（構成図は私が生成します）/ タグ `findy_hackathon` / ストーリー（下書きは私が書きます）
- [ ] 最終応募フォーム（Google Form）から提出: GitHub URL + デプロイ URL + Proto Pedia URL

---

## 補足: ローカルで今すぐ動かす（GCP 不要・フェイクモード）

```bash
# ターミナル1
cd backend && uv run uvicorn app.main:app --reload --port 8000
# ターミナル2
cd frontend && npm run dev
# → http://localhost:5173 （判定はフェイク: 常に「集中」判定）
```

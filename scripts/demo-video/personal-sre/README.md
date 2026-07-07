# Personal SRE 紹介動画 (docs/personal-sre.mp4) 生成パイプライン

2分36秒・1280x720・ナレーション/SFX/BGM付き。全素材 AI 生成 + HTML アニメ録画で人手ゼロ。

## 構成

| セクション | 手法 |
|---|---|
| ① 課題提起 (実写風) | flux-dev 生成写真 + CSS Ken Burns/手ブレ + シネマ黒帯 (scene1.html) |
| ② 技術解説スライド | アーキテクチャ図の CSS アニメ (scene2.html) |
| ③ デモ: チャット設定 | チャット UI のタイピングアニメ (scene3a.html) |
| ③ デモ: 監視→警告 | 生成写真 + 監視 HUD/警告バナー/字幕オーバーレイ (scene3b.html) |
| ④ 汎用性 + エンドカード | インフォグラフィック + ヒーロー画像 (scene4.html) |

## 素材生成 (Replicate MCP 経由)

- 画像 8枚: `black-forest-labs/flux-dev` (16:9, seed 4649)。人物は顔が目立たない
  後ろ/横アングルを指定して画像間の人物非一貫性を隠す
- ナレーション/警告音声: `minimax/speech-02-turbo` voice_id **Japanese_CalmLady**
  (男性系 Japanese_* ボイス ID は存在せずエラー)。警告は pitch -3 / speed 0.92
- 注意: クレジット残高 $5 未満だと **6 predictions/分** に制限される。ジョブは
  10秒間隔で投入し、prediction id を控えて後からポーリングする

## ビルド手順

```bash
node gen-audio2.mjs        # BGM(パッド)・SFX を PCM 合成
node record-scenes.mjs     # 5シーンを Playwright で録画 (計約2.6分)
node record-one.mjs scene4 31   # 単一シーンの撮り直し
node build-final.mjs       # 実測尺からオフセット計算 → ffmpeg で合成
```

ナレーション mp3 (n1-n4, warn) は Replicate から取得して同ディレクトリに置く。
シーン内イベント時刻を変えたら build-final.mjs の `events` を合わせること
(録画開始→ページロードの遅延 LAG=0.4s を加算済み)。

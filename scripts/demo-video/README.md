# デモ動画 自動生成パイプライン

`docs/demo-auto.mp4` (60秒・960x720・BGM/SFX付き) を人手ゼロで再生成するためのスクリプト群。
Claude Code による全自動制作。実写を使う本命の台本は `docs/demo-video-script.md` を参照。

## 仕組み

1. **cam.html + record-cam.mjs** — CSS アニメの「作業中→スマホ→作業→居眠り→作業」30秒シーンを
   Playwright で録画し、偽 Web カメラ映像を作る
2. **record-demo.mjs** — Chromium を `--use-fake-device-for-media-stream` +
   `--use-file-for-fake-video-capture=cam.y4m` で起動し、ヒアリング〜セッション〜サマリーの
   一連フローを画面録画。`canvas.toBlob` をフックして JPEG 先頭に `HABIT:<id>:` マーカーを注入し、
   FakeJudgeAgent の検知を任意のタイミングで発火させる (カメラ映像の演技区間と同期済み)
3. **cards.mjs / captions.mjs** — タイトル・アウトロカードとテロップを HTML→PNG で生成
   (このマシンの ffmpeg は drawtext 無効ビルドのため overlay 合成を採用)
4. **gen-audio.mjs** — チップチューン BGM・検知アラート・完了ジングルを PCM 合成
5. **ffmpeg** — 連結・テロップ overlay・音声ミックスして H.264/AAC へ

## 再生成手順

```bash
# 前提: backend (fake モード, :8000) と frontend (:5173) を起動しておく
npm init -y && npm i playwright && npx playwright install chromium

node record-cam.mjs
ffmpeg -y -i cam-raw.webm -t 30 -r 15 -pix_fmt yuv420p cam.y4m
node record-demo.mjs        # marks.json にシーン時刻を出力
node cards.mjs && node captions.mjs && node gen-audio.mjs

ffmpeg -y \
 -loop 1 -framerate 25 -t 3.2 -i title.png \
 -i demo-raw.webm \
 -loop 1 -framerate 25 -t 4.5 -i outro.png \
 -i bgm.wav -i alert.wav -i jingle.wav \
 -loop 1 -t 52 -i cap1.png -loop 1 -t 52 -i cap2.png -loop 1 -t 52 -i cap3.png \
 -loop 1 -t 52 -i cap4.png -loop 1 -t 52 -i cap5.png -loop 1 -t 52 -i cap6.png \
 -filter_complex_script filter.txt \
 -map '[v]' -map '[a]' -t 60.7 -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p \
 -c:a aac -b:a 160k -movflags +faststart demo.mp4
```

## ハマりどころ

- **overlay は `shortest=1` なしだと長い方の入力まで出力を引き延ばす**。
  テロップ PNG の `-t` は本編 (52.96s) より短くすること (無限ループにすると
  エンコードが終わらない)
- 録画テイクを変えたら `marks.json` を見て `filter.txt` のテロップ表示区間と
  SFX の `adelay` (mark 時刻 + タイトル 3.2s) を合わせ直す
- 介入発火は「同一悪習慣を 2 連続判定」が条件。マーカーは 2 判定分 (interval=3s なら
  6 秒以上) 維持する

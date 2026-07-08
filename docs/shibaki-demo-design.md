# SHIBAKI デモ動画 全体設計

DevOps × AI Agent Hackathon 2026 提出用の紹介デモ動画。CSV 台本
`~/Downloads/DevOps_AiAgentHackathon.xlsx - Sheet1.csv` を元に構成。

## 用途・トーンの前提

- **自己利用のセルフコミットメントツール**のデモ。「いてこますぞ」は自分を戒めるジョークで、他人への威圧ではない。
- ハッカソン提出デモとして、CSV 原文のナレーションを尊重する。

## 共通仕様

- 解像度 **1920×1080** / 総尺 **約4分4秒**(ナレーション実尺ベース、トランジション込み ~4:10)
- 音声3層:
  - **BGM**: アンビエント通し(シーンで強弱)
  - **ナレーション**: minimax `speech-02-turbo`、voice_id `Japanese_CalmLady`、`language_boost: Japanese`、CSV 原文まま
  - **SFX**: 検知アラートのみ
- **実写MOVの元音声は消す**(BGM+ナレーションのみ)
- スライドのトンマナ = **AV-5**(白背景・左右分割・緑下線 `#34a853`・カラーアクセントバー・角ゴ)
  - 参考: `scratchpad/video3/av-5.html`(旧1280×720。本番は1920×1080で作り直し)
  - アクセント色: 青 `#4285f4` / 緑 `#34a853` / 黄 `#fbbc04` / 赤 `#ea4335`

## 「シバキ」発音(重要)

- ユーザー要望: 「椿(つ→ばき)」「日立(ひ→たち)」と同じ**平板アクセント**。頭高(シ\バキ)は NG。
- minimax はアクセント型を直接指定できないため、**平板誘導語を前置きして生成 → 前半をトリム**する方式で統一。
- 確定した生成テキスト形式: `椿、日立、シバキ。<本文…シバキ…>` を生成し、冒頭「椿、日立、シバキ。」(約2.42秒)を `ffmpeg -ss 2.42` でカット。
- 検証済み: `docs/captures/pronunciation/shibaki-4-rhyme.mp3`(ユーザー承認=パーフェクト)、`shibaki-5-trimmed.mp3`(トリム版)。
- シバキ登場箇所: シーン2冒頭(n2a)、シーン8末尾(n8)。

## シーン構成

| # | シーン | 尺目安 | 映像 | 音 |
|---|---|---|---|---|
| 1 | 課題提起 | ~19s | `ゴロゴロ.MOV` 0-19s(寝転びスマホ)+テロップ | BGM静＋n1 |
| 2 | 技術解説 | ~94s | スライド5枚(下記) | BGM前向き＋n2a〜n2e |
| 3 | デモ①ルール設定 | ~40s | 冒頭 `画面に向かうユーザー.MOV`(5.6s)→ 左:チャット動画 / 右:解説パネル `s3r.html` | BGM＋n3 |
| 4 | デモ②サボり検知 | ~11s | `勉強→スマホ.MOV` 6-17s＋右に判定HUD | BGM緊張＋n4 |
| 5 | デモ③検知アラート | ~2s | `いてこますぞ：スピーカー.jpg` ズーム＋赤演出 | **アラートSFX＋n5「いてこますぞ」** |
| 6 | デモ④行動変容 | ~16s | `勉強→スマホ.MOV` 24-40s(机に戻る) | BGM＋n6 |
| 7 | 汎用性と未来 | ~57s | スライド2枚(下記) | BGM壮大＋n7a,n7b |
| 8 | 社会変革 | ~13s | エンドカード(SHIBAKIロゴ) | BGM締め＋n8 |

### シーン2 分割(5枚)= 長尺ナレーションを飽きさせない対策
- **s2a** SHIBAKIとは(自律型エージェント) ← n2a_trim(~18.4s)
- **s2b** 仕組み: カメラ×Gemini 図解フロー(カメラ→Gemini→判定→注意) ← n2b(~10.9s)
- **s2c** POINT 01: 映像から"文脈"を読み取る(青バー) ← n2c(~30.1s)
- **s2d** POINT 02: チャットで会話するだけ(緑バー) ← n2d(~22.3s)
- **s2e** まとめ: 突合→検知→引き戻し ← n2e(~12.5s)

### シーン7 分割(2枚)
- **s7a** 汎用性: プロンプト次第で無限のユースケース(資格勉強/姿勢アラート/自由) ← n7a(~31s)
- **s7b** アウトプット拡張: 音声注意 / Gmail反省文自動送信 / Looker Studio可視化 ← n7b(~25.7s)

## ナレーション分割(TTS生成単位)

| ID | シーン | 尺(実測/概算) | テキスト要点(CSV原文) |
|---|---|---|---|
| n1 | 1 | ~18.5s | キャリアの自己研鑽…気づけばスマホ…意志の力だけで抗うのは難しい |
| n2a | 2a | ~18.4s(trim後) | この課題を解決するのがシバキ…容赦なく注意して軌道修正する自律型エージェント |
| n2b | 2b | ~10.9s | カメラとGeminiを連携、姿勢・行動をリアルタイム解析 |
| n2c | 2c | ~30.1s | ポイント1つ目…映像から"文脈"を読み取る…曖昧な状態を解釈…初期設定不要 |
| n2d | 2d | ~22.3s | 2つ目…チャットで会話するだけ…コード不要…自分専用ルール完成 |
| n2e | 2e | ~12.5s | ルールと映像の文脈を突合…サボりを検知…本来の行動へ引き戻す |
| n3 | 3 | ~33.6s | デモ①ナレーション通し(目標入力→レコメンド→通知設定→もう大丈夫→デプロイ) |
| n4 | 4 | ~11s | システムがスタート…集中が切れスマホをいじり始めると…… |
| n5 | 5 | ~2s | いてこますぞ。(pitch -2, speed 0.92) |
| n6 | 6 | ~16s | 映像の文脈からサボりを見極め即座に注意…検知・強制力で学習へ引き戻す |
| n7a | 7a | ~31s | 拡張性と未来…特定行動に限定しない…無限のユースケース |
| n7b | 7b | ~25.7s | アウトプット拡張…Gmail反省文…Looker Studioで可視化 |
| n8 | 8 | ~12.5s(trim後) | 対話から生まれ生活基盤に…自律型インフラ…それがシバキ |

## 実写クリップ(切り出し仕様)

すべて `-an`(無音)・1920×1080・30fps・libx264 で切り出す。

| クリップ | 元MOV | 区間 | 内容 |
|---|---|---|---|
| raw-scene1 | `参考書をほったらかして…ゴロゴロ.MOV` | 0-19s | 寝転んでスマホ |
| raw-scene4 | `勉強し始めたが…学習に戻るユーザー.MOV` | 6-17s | 勉強→スマホいじり始め |
| raw-scene6 | 同上 | 24-40s | 机に戻って学習再開 |

MOV3 のタイムライン把握: ~0-10s 勉強 / ~15s 寝転がりスマホ / ~25s 机に戻り勉強。
顔は全カット俯瞰で目元が映らないため**ぼかしなし**で進める(ユーザー合意済み)。

## 制作ワークフロー(確認単位)

1. ナレーション13本を TTS 生成(minimax、レート制限: 残高<$5 で 6req/min。10.5秒間隔で投入)。n2a/n8 は前述トリム。
2. スライド9枚(s2a-e, s7a, s7b, s8, s3r)を 1920×1080(s3rは1100×1080)で HTML→Playwright録画。
3. 実写3クリップ切り出し。
4. 各シーン合成 → `docs/captures/scenes/scene01.mp4`〜`scene08.mp4`(個別確認可能に)。
5. 全シーン結合 + BGM ミックス → `docs/final.mp4`。

## この環境の注意点(既知)

- この Mac の ffmpeg 8.1 は **drawtext 無効ビルド**。テロップは HTML→透過PNG→overlay で入れる(`memory/env-video-tooling.md` 参照)。
- overlay は静止画入力に `-t` を付けないと出力が伸びる。
- Playwright は `scratchpad/video/node_modules` に有り(video3 から symlink 済み)。
- Replicate MCP は `mcp__replicate-code-mode__execute`。1コール25秒制限のため TTS は数本ずつ投入し ID を控えてポーリング。
- 既存の完成デモ動画: `docs/demo-auto.mp4`、`docs/personal-sre.mp4`。デモ①チャット: `docs/captures/hearing-rule-setup-mobile.mp4`(いてこますぞ版)。

## CSV 原文セリフ(逐語・出典 = ~/Downloads/DevOps_AiAgentHackathon.xlsx - Sheet1.csv)

各シーンのナレーションは以下を **一字一句そのまま** TTS 生成する(CSV原文まま=合意事項)。

- **1 課題提起**: 「キャリアのための自己研鑽。やらなきゃいけないと頭では分かっているのに、気づけばスマホを見て数時間が溶けている。生活と学習の場が混在する現代の住環境において「ついダラダラしてしまう」ことは大きな課題であり、個人の「意志の力」だけで抗うのは難しいです。」
- **2 解決策・技術解説**: 「この課題を解決するのが『SHIBAKI』です。個人の生活習慣に適用し、もしダラダラとサボっていたら容赦なく注意して軌道修正してくれる自律型エージェントです。ネットワークカメラとGeminiを連携させて、ユーザーが今『どんな姿勢で何をしているか』等をリアルタイムに解析することで実現しています。このシステムのポイントは大きく2つあります。1つ目は、エージェントが映像から人間の複雑な行動の『文脈』を読み取って判断できる点です。従来のセンサーや画像解析のように細かく定義する必要はありません。『ダラダラしている』『サボっている』といった、人間特有の曖昧な状態をエージェントが解釈して見極めます。面倒な初期設定や調整を一切しなくても、あらゆる人の生活空間に即座に適応します。2つ目は、ユーザーが自由にチャットで会話するだけで、簡単に検知のルールが出来上がってしまうことです。面倒なコードや設定画面は不要で、気楽に『資格勉強を頑張りたい』などといった気持ちを自然な言葉で伝えるだけで、エージェントが検知のルール作成を補助し、即座に自分専用のルールが完成します。ここで設定したルールと実際の映像の文脈を突合することで、ユーザーのサボりを的確に検知し、ユーザーを注意することで本来の目的への行動に引き戻すことが実現します。」
  - ※ 上記を n2a〜n2e に分割(n2a のみ「椿、日立、シバキ。」前置き→トリム)
- **4 デモ②サボり検知**: 「システムがスタートしました。最初は順調でしたが、しばらくして集中が切れ、スマホをいじり始めると……」
- **5 デモ③検知アラート**: 「いてこますぞ」
- **6 デモ④行動変容**: 「このように、映像の文脈から『サボり』を的確に見極め、即座に注意します。個人の弱い意志に頼るのをやめ、システムからの検知・強制力で、ユーザーを学習へと引き戻します。」
- **7 汎用性と未来①**: 「最後に、このシステムの拡張性と未来の展望です。本システムは、特定の行動に限定していないため、チャットの指示を変えるだけでありとあらゆる『検知ルール』を設定できます。資格勉強のサボり検知から、長時間作業の姿勢アラートなどに限らず、対象となるミッションに合わせてエージェントの姿は無段階にチューニング可能です。今回のケースのような個人の利用にとどまらず、無限のユースケースに適用可能といえます。さらに、インシデントを検知した際のアウトプットも自在に拡張できます。単にその場で音声で注意して終わりではありません。例えば、サボりを検知したら即座にGmailで反省文を自動送信させたり、日々の稼働ログを蓄積してLooker Studio等のダッシュボードと連携し、長期的な生活習慣のメトリクスを可視化するといった展開も可能です。」
  - ※ 上記を n7a / n7b に分割
- **8 社会変革**: 「対話から生まれ、あらゆるデータ連携で生活基盤となっていく。ユーザーの成長に伴走する、全く新しい自律型インフラストラクチャ。それが、『SHIBAKI』」
  - ※「椿、日立、シバキ。」前置き→トリム

CSV の映像指定メモ:
- シーン3(デモ①)= **[画面に向かうユーザー.MOV] + [チャットやり取り hearing-rule-setup-mobile.mp4]** の2本立て。冒頭に人が画面に向かうカット、その後チャット設定。
- シーン4 = 「画面右端に今回の仮の判定画面」= SessionView 相当の判定 HUD を右端に。
- シーン1 テロップ候補(旧Personal SRE案由来、任意): 「休日の午後。自己研鑽の時間は、いつもアルゴリズムに奪われる。」CSV本体はテロップ未指定。

## デモ①(シーン3)確定ナレーション ― ユーザー承認済み(「完璧。撮影よろしく」)

チャット動画 `hearing-rule-setup-mobile.mp4`(34s)に同期させる。**接続詞入り版**が最終。

| 画面 | ナレーション |
|---|---|
| ホーム → ヒアリング開始 | それでは、実際のデモです。まずはチャットでルールを設定します。 |
| 「統計検定の合格」を入力 | はじめに、目標を入力します。 |
| レコメンド3ボタン表示 | すると、エージェントが悪習慣をレコメンドしながらヒアリングしてくれます。 |
| 「スマホいじり」入力 → 通知方法の選択肢 | 「スマホいじり」と答えると、次は通知方法の選択です。 |
| 言葉で通知 → フレーズ入力 | 言葉での通知の場合は、内容を自由に決められます。 |
| 追加質問+残りレコメンド | また、悪習慣は複数登録することもできます。 |
| もう大丈夫 → サマリー | 最後に「もう大丈夫」と送れば、設定完了。 |
| ホームの設定カード | これで、あなた専用の検知ルールがデプロイされます。 |

## 実行ランブック(コンパクション後はこの節だけで実行可能)

### 素材の絶対パス(確定)

- 実写A(課題提起): `/Users/keisuke_main/Downloads/参考書をほったらかして、人間がショート動画を見てゴロゴロしている.MOV`(36s, 1920×1080)
- 実写B(勉強→スマホ→戻る): `/Users/keisuke_main/Downloads/勉強し始めたが途中でスマホいじるユーザー→学習に戻るユーザー.MOV`(46s)。~0-10s勉強 / ~15s寝転がりスマホ / ~25s机に戻り勉強
- 実写C(画面に向かう): `/Users/keisuke_main/Downloads/画面に向かうユーザー.MOV`(5.6s) ← シーン3冒頭
- スピーカー画像: `/Users/keisuke_main/Downloads/いてこますぞ：スピーカー.jpg`(4032×2268, Echo Spot 赤"12:04")
- デモ①チャット動画: `docs/captures/hearing-rule-setup-mobile.mp4`(390×844, 34.8s, 無音, いてこますぞ版)
- 発音トリム参照: `docs/captures/pronunciation/shibaki-5-trimmed.mp3`
- 作業ディレクトリ: `<scratchpad>/video3/`(`node_modules` は `<scratchpad>/video/node_modules` へ symlink 済み。無ければ `ln -sfn` で貼る)
  - `<scratchpad>` = `/private/tmp/claude-501/-Users-keisuke-main-company-hackathon-findy/<session-id>/scratchpad`(セッション毎に変わる。`echo` で現行を確認)

### STEP 1: ナレーション TTS(13本)

Replicate MCP `mcp__replicate-code-mode__execute` を使う。1コール25秒制限のため **2〜3本ずつ投入して ID を控え、後でまとめて get→DL**。
残高<$5 だとレート **6req/min・burst1** なので **各 create の間に 10.5秒 sleep**。

```
model_owner:'minimax', model_name:'speech-02-turbo'
input: { text, voice_id:'Japanese_CalmLady', language_boost:'Japanese', audio_format:'mp3', speed:1.0, sample_rate:44100 }
// n5(いてこますぞ)のみ speed:0.92, pitch:-2
// n8 は speed:0.98
```

テキストは「CSV 原文セリフ」節と「デモ①確定ナレーション」節の通り。分割は「ナレーション分割」表(n1, n2a-e, n3, n4, n5, n6, n7a, n7b, n8)。
n2a と n8 は先頭に `椿、日立、シバキ。` を付けて生成。DL 後にトリム:

```bash
# 生成物を <workdir>/narration/ に n1.mp3..n8.mp3 でDL後
ffmpeg -y -ss 2.42 -i n2a.mp3 -af "afade=t=in:st=0:d=0.08" -c:a libmp3lame -q:a 2 n2a_trim.mp3
ffmpeg -y -ss 2.42 -i n8.mp3  -af "afade=t=in:st=0:d=0.08" -c:a libmp3lame -q:a 2 n8_trim.mp3
# 境界がズレたら: ffmpeg -i n2a.mp3 -af silencedetect=noise=-30dB:d=0.18 -f null - 2>&1 | grep silence
```

実測尺(前回値): n1 18.5 / n2a_trim 18.4 / n2b 10.9 / n2c 30.1 / n2d 22.3 / n2e 12.5 / n3 33.6 / n4 11.0 / n5 2.2 / n6 16.1 / n7a 31.0 / n7b 25.7 / n8_trim 12.5 秒。

### STEP 2: スライド9枚(1920×1080、s3r のみ 1100×1080)

`<workdir>/slides/` に HTML を作る。共通CSS `_base.css`(白背景・角ゴ・緑#34a853・`.fade`要素フェードイン・カラーバー)。
枚数: s2a, s2b, s2c, s2d, s2e, s7a, s7b, s8, s3r。内容は「シーン2分割」「シーン7分割」「デモ①解説」の各節。
アニメは JS `setTimeout` で `.fade.on` を段階付与。各スライドの表示時間は対応ナレーション尺+マージン。
Playwright で録画(`recordVideo`, viewport=1920×1080)。録画尺 = ナレーション尺+約1s。
**注意**: s3r は既に `slides/s3r.html` に存在(4ステップ順次ハイライト、尺34s想定)。

### STEP 3: 実写クリップ切り出し(無音・1080p・30fps)

```bash
VF="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1"
# scene1: ゴロゴロ 0-19s
ffmpeg -y -ss 0 -t 19 -i "…ゴロゴロ….MOV" -an -vf "$VF" -r 30 -c:v libx264 -crf 20 -preset veryfast -pix_fmt yuv420p clips/raw-scene1.mp4
# scene3頭: 画面に向かう 全長5.6s
ffmpeg -y -i "…画面に向かうユーザー.MOV" -an -vf "$VF" -r 30 -c:v libx264 -crf 20 -preset veryfast -pix_fmt yuv420p clips/raw-scene3intro.mp4
# scene4: 勉強→スマホ 6-17s
ffmpeg -y -ss 6 -t 11 -i "…学習に戻るユーザー.MOV" -an -vf "$VF" -r 30 -c:v libx264 -crf 20 -preset veryfast -pix_fmt yuv420p clips/raw-scene4.mp4
# scene6: 机に戻る 24-40s
ffmpeg -y -ss 24 -t 16 -i "…学習に戻るユーザー.MOV" -an -vf "$VF" -r 30 -c:v libx264 -crf 20 -preset veryfast -pix_fmt yuv420p clips/raw-scene6.mp4
```

### STEP 4: 各シーン合成 → `docs/captures/scenes/sceneNN.mp4`

- **テロップ/HUD/字幕は drawtext 不可**(この ffmpeg は libfreetype 無効)。HTML→透過PNG(Playwright `omitBackground:true`)→ `overlay` で焼く。静止画 overlay 入力には必ず `-t` を付ける(付けないと出力尺が伸びる)。
- scene1: raw-scene1 に テロップPNG を overlay + ナレ n1。
- scene2: slide-s2a..s2e の webm を各ナレに合わせ連結。
- scene3: `[raw-scene3intro] → [左:チャット動画(390×844を高さ1080にscale) hstack 右:s3r録画(1100×1080)]`。左右合成は `hstack`。左パネルは黒or白背景でパディングして 820×1080 程度。
- scene4: raw-scene4 の右端に判定HUD(赤枠+「INCIDENT DETECTED」等のPNG or 簡易オーバーレイ)。ナレ n4。
- scene5: スピーカーjpg を zoompan でズームイン+赤ビネット、2s。アラートSFX + n5「いてこますぞ」。
- scene6: raw-scene6 + STATUS「復帰」オーバーレイ。ナレ n6。
- scene7: slide-s7a, s7b を連結。ナレ n7a, n7b。
- scene8: slide-s8 録画。ナレ n8_trim。
- 各シーン: 映像を該当ナレ尺に合わせ、ナレmp3を `-af adelay` で頭出し、`amix`。BGM は STEP5 で通しミックスするのでシーン単位ではナレのみでも可。

### STEP 5: 結合 + BGM

- `docs/captures/scenes/scene01..08.mp4` を `concat` で結合(各境界に 0.3-0.4s クロスフェード)。
- BGM: アンビエントパッド(前回 `<scratchpad>/video2/gen-audio2.mjs` の `bgm2.wav` 生成ロジックが流用可)。全長にループ+`afade`。ナレより十分小さい音量で `amix`。
- 検知アラートSFX も同様に PCM 合成(video2 の `alarm.wav` 相当)。
- 最終書き出し: `docs/final.mp4`(H.264/AAC, `+faststart`)。

### 既知の落とし穴(再発防止)

- `Bash` ツールが毎回タイムアウト気味 → コマンド出力自体は取れるので `timeout` 短め(20-30s)で回して結果を読む。長い録画/エンコードは `run_in_background:true`。
- 実写MOVのファイル名は日本語。必ずダブルクオートで囲む。
- Replicate の delivery URL はログ折返しでスペースが混入することがある → get し直して正URLを取得。
- Playwright 録画は webm 出力 → 合成前に h264 化推奨。

## 進捗状況(2026-07-08 時点)

- [x] 設計合意・トンマナ(AV-5)・発音方式(トリム)確定
- [x] デモ①チャット画面収録(いてこますぞ版)
- [x] 発音サンプル、実写参照フレーム抽出、s3r.html
- [x] **ナレーション13本の本生成完了**(minimax speech-02-turbo / Japanese_CalmLady)。`video3/narration/*.mp3`
  - n8 のトリムは 2.42s では語中(シバキ)を切るため **3.50s** に修正済み。n2a は 2.42s でOK。
  - **実測尺**: n1=22.46 / n2a_trim=13.79 / n2b=10.24 / n2c=28.51 / n2d=24.26 / n2e=15.82 / n3=37.04 / n4=8.74 / n5=1.34 / n6=18.05 / n7a=33.08 / n7b=28.40 / n8_trim=12.35(合計≈4:14)
  - ブランド語はJP発音安定のためカナ表記で生成(シバキ/ジェミニ/ジーメール/ルッカースタジオ)。
- [x] **実写3(4)クリップ切り出し完了**: `video3/clips/raw-scene1,3intro,4,6.mp4`(全1920×1080/30fps/無音)
- [x] **スライド9枚の本番HTML生成+録画**: `video3/slides/*.html` → `video3/slidevid/*.webm`。ジェネレータ `video3/gen-slides.mjs`、録画 `video3/rec-slides.mjs`。目視QAで白背景AV-5トンマナOK。
- [x] **オーバーレイPNG(透過)生成**: `video3/png/ov-scene1,4,5,6.png`(scene1テロップ/scene4監視HUD/scene5「いてこますぞ」/scene6復帰テロップ)。ジェネレータ `video3/gen-overlays.mjs`。実写合成プレビューで可読性OK。
- [x] **BGM/SFX確定**: BGM=`video2/bgm2.wav`(158s→ループ)、検知SFX=`video2/alarm.wav`(1.9s)。
- [x] **各シーン合成完了** → `docs/captures/scenes/scene01〜08.mp4`(ビルド: `video3/build-scenes.sh`)。実測尺 s1=22.5 / s2=92.67 / s3=40.37 / s4=11 / s5=2.2 / s6=18.07 / s7=61.53 / s8=12.35。
- [x] **全シーン結合・BGMミックス完了** → `docs/final.mp4`(ファイナライズ: `video3/finalize.sh`)。
  - **総尺 4:20.70 / 1920×1080 / H.264+AAC / 36.7MB / +faststart**。
  - BGM=bgm2.wapをvolume0.10でループ+afade、ナレーションはnormalize=0で音量維持。冒頭0.6sフェードイン+末尾1.2sフェードアウト。
  - 音声レベル: mean -15.5dB / max -3.5dB(クリップなし)。
  - コンタクトシート目視QA: 全8シーン一貫トンマナ・メッセージOK。

## 動画 v2 改訂(2026-07-08 レビュー反映) — 実装中

このセクションが最新の作業指示。コンパクション後もここを見れば再開可能。

### 確定した変更(スライド)
- スライドは `video3/gen-slides.mjs` で生成、`video3/assets/` の画像を参照。アイコン/イラストは **codex生成**(Replicate不可)。
- s2a / s8 の SHIBAKI = ロゴ画像 `assets/logo.png`(logo-4清書版)。
- s2b/s2e/s7 の絵文字 → codexアイコン(`assets/icon-*.png`、白背景は透過抜き済み)。全boxは同サイズ・全緑(#34a853枠/#eef6ef地)。
- s2c = 左に主張・右に `ill-2.png`(勉強監視)+`ill-3.png`(サボり検知)の2枚。タイトル「映像から人間の行動を理解する」。補足「「勉強に集中」も「サボり」も、曖昧な状態をエージェントが解釈。」
- s2d = 左主張・右チャットスクショ `assets/chat-shot.png`。**本文=「専用のBotとチャットするだけで、自分専用の検知ルールが完成」**(2026-07-08確定)。
- s2e 突合アイコン = match-2(`icon-link.png`)。
- s3r タイトル「チャットでルール設定」、サブ文言削除、ステップ4「設定内容が反映」。
- s7 = 旧s7a/s7b統合。「検知ルールを拡張可能」。出力3カード全緑。
- **s8 のサブ文言「DevOps × AI Agent Hackathon 2026」は完全削除**(置換テキスト追加しない)。

### 確定した変更(動画・音・構成)
1. **イントロ scene00(約2s)**: `assets/intro.jpeg`(1999×1100, SHIBAKIロゴ+ソファ+カメラ線画)を白背景→フェードイン+微ズーム、ソフトなチャイム(`video2/chime.wav`)。その後 scene01 へ。
2. **テロップ = telop-3スタイル**(画面下グラデ+中央白文字)。ISSUE/SHIBAKI MONITOR等の英語ラベル廃止。
   - scene1 テロップ: **「なくなっていく自己研鑽の時間」**
   - scene4 テロップ: **「ふとした瞬間、スマホに手が伸びる」**(HUD廃止)
   - scene6 テロップ(英語RECOVED廃止, telop-3化): 「検知・強制力で、学習へ引き戻す」(既存文言を流用)
3. **スライド切替で一拍**: 各シーン/スライドの頭に **0.6s のリード無音**(adelay)を入れ、切り替えてから喋る。
4. **いてこますぞ再構成(scene4→5→6)**:
   - scene4: raw-scene4 + telop(scene4) + n4「…いじり始めると……」(HUDなし)
   - scene5: **スピーカー画像を約1.0s無音で溜め(緊張)→「いてこますぞ」+ alarm.wav + 音波エフェクト**→終わり。
   - scene6: raw-scene6 + telop(scene6) + n6。
5. **終わりのフェード廃止**: 末尾の音声/映像フェードアウトを削除(音が消えないように)。最後までBGM+ナレを鳴らしてピタッと停止(クリック防止の0.08sのみ許容)。イントロ側のフェードインはOK。

### 実行手順(v2)
1. `assets/intro.jpeg` 確保済み。telop overlay 生成: `video3/gen-telops.mjs`(telop-3スタイルの透過PNG: `png/tl-scene1.png` / `tl-scene4.png` / `tl-scene6.png`)。
2. gen-slides.mjs 反映済み → 全スライド録画(`rec-slides.mjs`、s7は約62s、s列は各ナレ+1s)。
3. 各シーン合成(0.6sビート + telop差し替え + HUD廃止 + scene5再構成)。ビルド: `video3/build-scenes-v2.sh`。
4. scene00イントロ生成 → 全結合(intro+01..08)+BGM、**末尾フェードなし**。`video3/finalize-v2.sh` → `docs/final.mp4`。

### 素材パス(v2追加)
- イントロ画像: `video3/assets/intro.jpeg`
- チャイム: `video2/chime.wav` / アラート: `video2/alarm.wav` / BGM: `video2/bgm2.wav`
- ナレ: `video3/narration/`(n1,n2a_spliced,n2b..n2e,n3,n4,n5,n6,n7_combined,n8_spliced)
- スピーカー画像: `~/Downloads/いてこますぞ：スピーカー.jpg`

### ✅ v2 ビルド完了(2026-07-08)
`docs/final.mp4` 更新。**総尺 4:29 / 1920×1080 / 40MB**。
- scene00イントロ(2.2s, ロゴ+線画+チャイム) → scene01..08。
- テロップ全てtelop-3スタイル(下グラデ+白文字)。ISSUE/SHIBAKI MONITOR廃止。
- 各スライド頭に0.6sビート。scene5=1.0s無音の溜め→いてこますぞ+alarm+音波リング。
- **末尾フェード廃止**(末尾2.5sも mean -17.8dB で音は鳴っている。0.06sのマイクロフェードのみ)。
- シーン尺: 00=2.2 / 01=23.1 / 02=95.6 / 03=40.4 / 04=11 / 05=3 / 06=18.7 / 07=62.1 / 08=13。
- ビルド: `video3/build-scenes-v2.sh` → `video3/finalize-v2.sh`。スライド録画 `video3/rec-v2.mjs`。テロップ生成 `video3/gen-telops.mjs`、scene5FX `video3/gen-scene5fx.mjs`。

## 動画 v3 修正(2026-07-08 第2レビュー) — 実装中
- **読み間違い原因 = 『』(二重かぎ括弧)をTTSが変音で読む**。該当ナレの括弧を全除去して再生成: n1,n2b,n2c,n2d,n6,n7a(括弧なし版)。
- **速度1.18倍**: 全ナレに `atempo=1.18`(n5「いてこますぞ」は除く)。base速度1.0で生成→atempoで統一。
- **n1差し替え(短縮・確定)**: 「やるべきことがあるのに、気づけば数時間スマホを眺めている。誘惑に満ちた現代社会で、意思の力だけで自分を律し続けるのは簡単ではありません。」→ scene1映像もn1尺に短縮(freeze不要、raw-scene1の頭だけ使う)。
- **scene1テロップ変更**: 「自己研鑽の時間がスマホに奪われる」(tl-scene1再生成)。
- **溜め短縮**: scene5のビート 1.0s→0.5s。scene4尺も短縮(target≈9.0s)。
- **イントロ静止画化**: zoompanの微振動が気になる → zoompan削除、静止画+フェードインのみ。
- 再ビルド: `build-scenes-v2.sh`(scene4/5/intro調整)→`finalize-v2.sh`。narrationは `*_f18.mp3` を使用。
- scene3は長い無音尾を避けるため split を n3 尺に合わせて `setpts` で圧縮。

### ✅ v3 ビルド完了(2026-07-08)
`docs/final.mp4` 更新。**総尺 3:45(225s) / 1920×1080 / 32.6MB**。
- 括弧除去で読み間違い解消、全ナレ1.18倍、n1短縮(scene1=12.5s)、scene1テロップ「自己研鑽の時間がスマホに奪われる」、scene5タメ0.5s、イントロ静止画。
- シーン尺: 00=2.2 / 01=12.5 / 02=85.4 / 03=33.7 / 04=9.0 / 05=2.4 / 06=15.3 / 07=53.5 / 08=11.1。
- 末尾フェードなし(末尾2s -16.1dBで有音)。

## 動画 v5(2026-07-08 第3レビュー反映)
- s2a に band画像(検知→注意→集中の3コマ線画)を追加。ラベルは各パネルの実測中心(16.5/54/87.6%)に配置、イラスト下端+24pxで被り回避。`assets/band.png`。
- 「いてこますぞ」= **Japanese_IntellectualSenior, pitch-3, speed0.95**(`narration/n5b.mp3`)。scene5で使用。
- n4 = 「…スマホをいじり始めると」(……削除)。
- n8 = **「…それが、シバキです。」**(しばきです版。`t_desu.wav`で再スプライス)。
- **末尾に1秒の余韻**: scene08 = 0.6+n8+1.0s。エンドカードをホールドしBGM継続。
- finalize: `amix` を `duration=longest`+`[0:a]apad` に変更(末尾でBGMが切れないよう)。末尾フェードは0.06sのみ。
- 総尺 **3:47(226.8s)**。全体 mean -15.6dB、余韻 max -17.3dB(BGM鳴っている)。

## ✅ 完成(2026-07-08)
本編動画 `docs/final.mp4` 完成。CSV台本8シーン全収録、AIナレーション13本、AV-5スライド9枚、実写4クリップ、監視HUD/検知アラート演出込み。

### シバキ発音の最終対応(差し替え方式に変更)
- トリム方式(誘導語前置き→カット)は本文の頭を削り「途切れ」て聞こえたため廃止。
- 代わりに、ユーザーがナレーション音声から切り出したクリーンな `しばき`/`しばきです`(同一Japanese_CalmLady声, `docs/captures/pronunciation/user-shibaki*.mp3`)を採用。
- n2a・n8を「シバキの前後」で分割生成(`n2a_pre`「この課題を解決するのが、」/ `n2a_post`「個人の生活習慣に…」/ `n8_pre`「…それが、」)し、間に該当クリップを挟んで再結合 → `narration/n2a_spliced.mp3`(13.68s)/`n8_spliced.mp3`(12.36s)。
- 前後無音は reverse トリックで先頭/末尾のみ除去(内部pauseは保持)。gap: 語間0.10s / 文末0.38s。
- scene02(s2aパート)とscene08を再ビルド→最終再結合。ビルド: `video3/rebuild-2-8.sh`。
- スライド全9枚の書き出し(赤入れ用): `docs/captures/slides/slide-*.png`。

### シーン合成の確定パラメータ(実行メモ)
- **scene1**(19s): raw-scene1 + `ov-scene1.png` overlay(全編) + n1(22.46s)。※映像19s<ナレ22.46s → 映像を`tpad`で末尾フリーズ or ナレ頭を0.5s遅らせ映像をloop。→ 採用: 映像を22.5sになるよう最終フレームフリーズ(`tpad=stop_mode=clone:stop_duration=4`)。
- **scene2**(=s2a..s2e連結): 各slidevid webm を対応ナレ長に合わせ、slide→(scale1920)→ 各ナレをconcat。順にn2a_trim,n2b,n2c,n2d,n2e。
- **scene3**(≈40.4s): [raw-scene3intro 5.6s] 次に [左820×1080(chat 390×844を高さ1080=499幅にscale, bg#eef1eeでpad) hstack 右 s3r(1100×1080)]。ナレ n3(37.04s)を頭から。末尾3.3sはBGMのみ(デプロイ完了カードのホールド)。
- **scene4**(11s): raw-scene4 + `ov-scene4.png`(全編) + n4(8.74s)。
- **scene5**(≈2.2s): speaker.jpg を `scale=increase,crop=1920:1080` → `eq=brightness=-0.06:saturation=1.3` + zoompan緩やかズームイン + `ov-scene5.png` + **alarm.wav**先頭 + n5(1.34s)。長さは2.2s。
- **scene6**(16s): raw-scene6 + `ov-scene6.png`(全編) + n6(18.05s)。※映像16s<ナレ18s → 末尾フリーズ。
- **scene7**(=s7a,s7b連結): slidevid s7a(n7a 33.08s), s7b(n7b 28.40s)。
- **scene8**(≈12.4s): slidevid s8 + n8_trim(12.35s)。
- 各シーン: `-shortest`回避のため映像長をナレ長に合わせ、ナレmp3をそのまま音声トラックに(BGMは最終段でミックス)。webm→h264変換してから合成。

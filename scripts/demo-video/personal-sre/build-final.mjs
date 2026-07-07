import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const dir = dirname(fileURLToPath(import.meta.url))
const probe = (f) =>
  Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', join(dir, f)]).toString().trim())

const scenes = ['scene1.webm', 'scene2.webm', 'scene3a.webm', 'scene3b.webm', 'scene4.webm']
const d = scenes.map(probe)
const start = [0]
for (let i = 1; i < d.length; i++) start[i] = start[i - 1] + d[i - 1]
const total = start[4] + d[4]
const LAG = 0.4 // 録画開始からページロードまでのおおよその遅延

// [s1,s2,s3a,s3b,s4] 各シーン内相対時刻 → 絶対ms
const at = (scene, rel) => Math.round((start[scene] + LAG + rel) * 1000)
const events = {
  n1: at(0, 1.5),
  n2: at(1, 1.6),
  n3: at(2, 0.8),
  send: at(2, 5.6),
  recv: at(2, 10.2),
  blip: at(3, 10.8),
  alarm: at(3, 13.0),
  warn: at(3, 17.2),
  chime: at(3, 31.0),
  n4: at(4, 1.6),
}
console.log('durations', d.map((x) => x.toFixed(2)).join(' '), 'total', total.toFixed(2))
console.log(JSON.stringify(events))

// 入力: 0-4 シーン動画, 5 bgm, 6-9 n1-n4, 10 warn, 11 send, 12 recv, 13 blip, 14 alarm, 15 chime
const vparts = scenes.map((_, i) => `[${i}:v]fps=25,format=yuv420p[v${i}]`).join(';\n')
const filter = `${vparts};
[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0,fade=t=in:st=0:d=0.5,fade=t=out:st=${(total - 1.2).toFixed(2)}:d=1.2[v];
[5:a]atrim=0:${total.toFixed(2)},afade=t=in:st=0:d=1.5,afade=t=out:st=${(total - 3.5).toFixed(2)}:d=3.5[bgm];
[6:a]adelay=${events.n1}[an1];
[7:a]adelay=${events.n2}[an2];
[8:a]adelay=${events.n3}[an3];
[9:a]adelay=${events.n4}[an4];
[10:a]adelay=${events.warn}[awarn];
[11:a]adelay=${events.send}[asend];
[12:a]adelay=${events.recv}[arecv];
[13:a]adelay=${events.blip}[ablip];
[14:a]adelay=${events.alarm}[aalarm];
[15:a]adelay=${events.chime}[achime];
[bgm][an1][an2][an3][an4][awarn][asend][arecv][ablip][aalarm][achime]amix=inputs=11:normalize=0:duration=first[a]
`
writeFileSync(join(dir, 'filter2.txt'), filter)

const args = [
  '-y', '-v', 'warning', '-stats',
  ...scenes.flatMap((s) => ['-i', join(dir, s)]),
  '-i', join(dir, 'bgm2.wav'),
  '-i', join(dir, 'n1.mp3'), '-i', join(dir, 'n2.mp3'), '-i', join(dir, 'n3.mp3'), '-i', join(dir, 'n4.mp3'),
  '-i', join(dir, 'warn.mp3'),
  '-i', join(dir, 'send.wav'), '-i', join(dir, 'recv.wav'), '-i', join(dir, 'blip.wav'),
  '-i', join(dir, 'alarm.wav'), '-i', join(dir, 'chime.wav'),
  '-filter_complex_script', join(dir, 'filter2.txt'),
  '-map', '[v]', '-map', '[a]', '-t', total.toFixed(2),
  '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
  join(dir, 'personal-sre.mp4'),
]
execFileSync('ffmpeg', args, { stdio: 'inherit' })
console.log('built personal-sre.mp4')

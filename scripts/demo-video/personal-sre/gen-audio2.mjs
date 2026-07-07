import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const dir = dirname(fileURLToPath(import.meta.url))
const SR = 44100

const writeWav = (path, samples) => {
  const pcm = new Int16Array(samples.length)
  for (let i = 0; i < samples.length; i++) {
    pcm[i] = Math.max(-1, Math.min(1, samples[i])) * 32767
  }
  const data = Buffer.from(pcm.buffer)
  const h = Buffer.alloc(44)
  h.write('RIFF', 0); h.writeUInt32LE(36 + data.length, 4); h.write('WAVEfmt ', 8)
  h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(1, 22)
  h.writeUInt32LE(SR, 24); h.writeUInt32LE(SR * 2, 28); h.writeUInt16LE(2, 32); h.writeUInt16LE(16, 34)
  h.write('data', 36); h.writeUInt32LE(data.length, 40)
  writeFileSync(path, Buffer.concat([h, data]))
}

const NOTE = (name) => {
  const table = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }
  const m = name.match(/^([A-G])(#?)(\d)$/)
  const st = table[m[1]] + (m[2] ? 1 : 0) + (Number(m[3]) + 1) * 12
  return 440 * Math.pow(2, (st - 69) / 12)
}

// --- 環境パッド BGM: Am → F → C → G を8秒/コードでゆっくり回す ---
const CHORDS = [
  ['A2', 'E3', 'A3', 'C4', 'E4'],
  ['F2', 'C3', 'F3', 'A3', 'C4'],
  ['C3', 'G3', 'C4', 'E4', 'G4'],
  ['G2', 'D3', 'G3', 'B3', 'D4'],
]
const CHORD_SEC = 8
const TOTAL = 158
const bgm = new Float64Array(TOTAL * SR)
for (let ci = 0; ci * CHORD_SEC < TOTAL; ci++) {
  const chord = CHORDS[ci % CHORDS.length]
  const start = ci * CHORD_SEC * SR
  const len = Math.min(CHORD_SEC * SR, bgm.length - start)
  for (const name of chord) {
    const f = NOTE(name)
    const detune = f * 1.003
    for (let i = 0; i < len; i++) {
      const t = i / SR
      const attack = Math.min(1, t / 2.2)
      const release = Math.min(1, (len - i) / SR / 2.2)
      const env = attack * release
      bgm[start + i] +=
        (Math.sin(2 * Math.PI * f * t) + 0.6 * Math.sin(2 * Math.PI * detune * t)) * 0.016 * env
    }
  }
}
writeWav(join(dir, 'bgm2.wav'), bgm)

const tone = (len, fn) => {
  const out = new Float64Array(Math.round(len * SR))
  for (let i = 0; i < out.length; i++) out[i] = fn(i / SR, i / out.length)
  return out
}
const sq = (f, t) => (Math.sin(2 * Math.PI * f * t) > 0 ? 1 : -1)

// チャット送信/受信ポップ
writeWav(join(dir, 'send.wav'), tone(0.16, (t, p) => Math.sin(2 * Math.PI * (620 + 300 * p) * t) * 0.22 * Math.exp(-9 * p)))
writeWav(join(dir, 'recv.wav'), tone(0.2, (t, p) => Math.sin(2 * Math.PI * (980 - 240 * p) * t) * 0.2 * Math.exp(-7 * p)))

// 解析開始ブリップ
writeWav(join(dir, 'blip.wav'), tone(0.3, (t, p) => Math.sin(2 * Math.PI * (440 + 660 * p) * t) * 0.18 * Math.exp(-5 * p)))

// 警告アラーム: 高-低 2音 ×2回
const alarm = new Float64Array(Math.round(1.9 * SR))
for (const [start, f] of [[0, 932], [0.4, 622], [0.9, 932], [1.3, 622]]) {
  const s = Math.round(start * SR)
  const len = Math.round(0.36 * SR)
  for (let i = 0; i < len && s + i < alarm.length; i++) {
    const p = i / len
    alarm[s + i] += sq(f, i / SR) * 0.14 * Math.min(1, p * 14) * Math.exp(-2.4 * p)
  }
}
writeWav(join(dir, 'alarm.wav'), alarm)

// 復帰チャイム
const chime = new Float64Array(Math.round(1.4 * SR))
;['C5', 'E5', 'G5'].forEach((n, k) => {
  const s = Math.round(k * 0.15 * SR)
  const len = Math.round(0.8 * SR)
  const f = NOTE(n)
  for (let i = 0; i < len && s + i < chime.length; i++) {
    const p = i / len
    chime[s + i] += Math.sin(2 * Math.PI * f * (i / SR)) * 0.14 * Math.exp(-4 * p)
  }
})
writeWav(join(dir, 'chime.wav'), chime)

console.log('audio2 done')

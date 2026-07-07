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
  const header = Buffer.alloc(44)
  header.write('RIFF', 0)
  header.writeUInt32LE(36 + data.length, 4)
  header.write('WAVEfmt ', 8)
  header.writeUInt32LE(16, 16)
  header.writeUInt16LE(1, 20)
  header.writeUInt16LE(1, 22)
  header.writeUInt32LE(SR, 24)
  header.writeUInt32LE(SR * 2, 28)
  header.writeUInt16LE(2, 32)
  header.writeUInt16LE(16, 34)
  header.write('data', 36)
  header.writeUInt32LE(data.length, 40)
  writeFileSync(path, Buffer.concat([header, data]))
}

const NOTE = (name) => {
  const table = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 }
  const m = name.match(/^([A-G])(#?)(\d)$/)
  const semitone = table[m[1]] + (m[2] ? 1 : 0) + (Number(m[3]) + 1) * 12
  return 440 * Math.pow(2, (semitone - 69) / 12)
}

const square = (phase) => (phase % 1 < 0.5 ? 1 : -1)
const triangle = (phase) => 4 * Math.abs(((phase + 0.25) % 1) - 0.5) - 1

// (音名 or null, 拍数) を並べてトラックを合成する
const renderTrack = (notes, beatSec, wave, gain, decay) => {
  const total = notes.reduce((s, [, b]) => s + b, 0)
  const out = new Float64Array(Math.round(total * beatSec * SR))
  let cursor = 0
  for (const [name, beats] of notes) {
    const len = Math.round(beats * beatSec * SR)
    if (name) {
      const freq = NOTE(name)
      for (let i = 0; i < len; i++) {
        const t = i / SR
        const env = Math.exp(-decay * (i / len))
        out[cursor + i] = wave(freq * t) * gain * env
      }
    }
    cursor += len
  }
  return out
}

// --- BGM: 120BPM 8ビートのゆるいチップチューン (8秒ループ) ---
const beat = 0.25 // 8分音符 = 0.25s
const melodyLoop = [
  ['C5', 1], ['E5', 1], ['G5', 1], ['E5', 1], ['A5', 2], ['G5', 2],
  ['B4', 1], ['D5', 1], ['G5', 1], ['D5', 1], ['G5', 4],
  ['A4', 1], ['C5', 1], ['E5', 1], ['C5', 1], ['F5', 2], ['E5', 2],
  ['F5', 1], ['E5', 1], ['D5', 1], ['B4', 1], ['C5', 4],
]
const bassLoop = [
  ['C3', 2], ['G3', 2], ['C3', 2], ['G3', 2],
  ['G2', 2], ['D3', 2], ['G2', 2], ['D3', 2],
  ['A2', 2], ['E3', 2], ['A2', 2], ['E3', 2],
  ['F2', 2], ['C3', 2], ['F2', 2], ['G3', 2],
]
const melody = renderTrack(melodyLoop, beat, square, 0.055, 2.2)
const bass = renderTrack(bassLoop, beat, triangle, 0.075, 0.8)
const loopLen = Math.max(melody.length, bass.length)

const TOTAL_SEC = 64
const bgm = new Float64Array(TOTAL_SEC * SR)
for (let i = 0; i < bgm.length; i++) {
  const j = i % loopLen
  bgm[i] = (melody[j] ?? 0) + (bass[j] ?? 0)
}
writeWav(join(dir, 'bgm.wav'), bgm)

// --- 検知アラート: ピコン! (2音上昇) ---
const alert = new Float64Array(Math.round(0.5 * SR))
for (const [start, freq] of [[0, 880], [0.14, 1318.5]]) {
  const s = Math.round(start * SR)
  const len = Math.round(0.22 * SR)
  for (let i = 0; i < len && s + i < alert.length; i++) {
    const env = Math.exp(-6 * (i / len))
    alert[s + i] += square((freq * i) / SR) * 0.16 * env
  }
}
writeWav(join(dir, 'alert.wav'), alert)

// --- サマリー用ジングル: ドミソド↑ ---
const jingle = new Float64Array(Math.round(1.1 * SR))
;['C5', 'E5', 'G5', 'C6'].forEach((n, k) => {
  const s = Math.round(k * 0.13 * SR)
  const len = Math.round((k === 3 ? 0.6 : 0.16) * SR)
  const freq = NOTE(n)
  for (let i = 0; i < len && s + i < jingle.length; i++) {
    const env = Math.exp(-3.5 * (i / len))
    jingle[s + i] += square((freq * i) / SR) * 0.13 * env
  }
})
writeWav(join(dir, 'jingle.wav'), jingle)

console.log('audio done')

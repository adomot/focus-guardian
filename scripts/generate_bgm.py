# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "lameenc"]
# ///
"""BGM 3曲を合成して assets/bgm/ に MP3 で出力する。

フリー音源のライセンス確認・ダウンロードを避け、自前生成でゼロライセンスにする。
Voice Monkey のクリップ再生上限 (~240秒) に収まる 90 秒ループ。
"""

from pathlib import Path

import lameenc
import numpy as np

SR = 44100
OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "bgm"

rng = np.random.default_rng(seed=20260710)


def note(freq: float, duration: float, harmonics: list[float]) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    wave = sum(
        amp * np.sin(2 * np.pi * freq * (i + 1) * t) for i, amp in enumerate(harmonics)
    )
    envelope = np.minimum(1.0, np.minimum(t / 0.8, (duration - t) / 0.8))
    return wave * envelope


def chord(freqs: list[float], duration: float) -> np.ndarray:
    harmonics = [0.5, 0.2, 0.08, 0.03]
    return sum(note(f, duration, harmonics) for f in freqs) / len(freqs)


def focus_track() -> np.ndarray:
    """ゆったりしたパッドのコード進行 (Am - F - C - G)"""
    a, f, c, g, e, d = 220.0, 174.61, 261.63, 196.0, 164.81, 146.83
    progression = [
        [a, c, e * 2 / 2],
        [f, a, c],
        [c, e, g],
        [g, d * 2 / 2, g / 2 * 3],
    ]
    bar = 5.6
    body = np.concatenate([chord(freqs, bar) for freqs in progression])
    track = np.tile(body, 4)
    shimmer = 0.02 * np.sin(2 * np.pi * 0.1 * np.arange(len(track)) / SR)
    return track * (1.0 + shimmer)


def nature_track() -> np.ndarray:
    """雨音風 (フィルタ付きノイズ + ランダムな雫)"""
    duration = 90.0
    n = int(SR * duration)
    noise = rng.standard_normal(n)
    kernel = np.exp(-np.arange(200) / 40.0)
    rain = np.convolve(noise, kernel, mode="same")
    rain /= np.max(np.abs(rain))
    rain *= 0.35
    for _ in range(180):  # 雫
        pos = rng.integers(0, n - SR // 4)
        freq = rng.uniform(800, 2400)
        length = int(SR * 0.12)
        t = np.arange(length) / SR
        drop = 0.12 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 35)
        rain[pos : pos + length] += drop
    return rain


def uptempo_track() -> np.ndarray:
    """120BPM のキック + ハイハット + ベースアルペジオ"""
    bpm, bars = 120, 44
    beat = 60.0 / bpm
    n = int(SR * beat * 4 * bars)
    track = np.zeros(n)

    kick_len = int(SR * 0.15)
    t_k = np.arange(kick_len) / SR
    kick = 0.8 * np.sin(2 * np.pi * (60 + 80 * np.exp(-t_k * 30)) * t_k) * np.exp(-t_k * 18)
    hat_len = int(SR * 0.05)
    hat = 0.12 * rng.standard_normal(hat_len) * np.exp(-np.arange(hat_len) / (SR * 0.01))

    bass_notes = [110.0, 110.0, 130.81, 98.0]
    for bar in range(bars):
        bar_start = int(SR * beat * 4 * bar)
        for b in range(4):
            pos = bar_start + int(SR * beat * b)
            track[pos : pos + kick_len] += kick[: n - pos] if pos + kick_len > n else kick
            hpos = pos + int(SR * beat / 2)
            if hpos + hat_len < n:
                track[hpos : hpos + hat_len] += hat
        freq = bass_notes[bar % 4]
        for step in range(8):
            pos = bar_start + int(SR * beat / 2 * step)
            length = int(SR * beat / 2 * 0.9)
            if pos + length >= n:
                break
            t_b = np.arange(length) / SR
            mult = 1 if step % 2 == 0 else 2
            bass = 0.25 * np.sin(2 * np.pi * freq * mult * t_b) * np.exp(-t_b * 6)
            track[pos : pos + length] += bass
    return track


def to_mp3(samples: np.ndarray, path: Path) -> None:
    samples = samples / (np.max(np.abs(samples)) + 1e-9) * 0.85
    pcm = (samples * 32767).astype(np.int16)
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(128)
    encoder.set_in_sample_rate(SR)
    encoder.set_channels(1)
    encoder.set_quality(2)
    data = encoder.encode(pcm.tobytes()) + encoder.flush()
    path.write_bytes(data)
    print(f"{path.name}: {len(data) / 1024:.0f} KB, {len(samples) / SR:.0f}s")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    to_mp3(focus_track(), OUT_DIR / "focus.mp3")
    to_mp3(nature_track(), OUT_DIR / "nature.mp3")
    to_mp3(uptempo_track(), OUT_DIR / "uptempo.mp3")

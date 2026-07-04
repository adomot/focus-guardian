let audioContext: AudioContext | null = null

export function unlockAudio(): void {
  try {
    if (!audioContext) {
      audioContext = new AudioContext()
    }
    if (audioContext.state === 'suspended') {
      audioContext.resume().catch((error: unknown) => {
        console.warn('AudioContext の再開に失敗しました', error)
      })
    }
  } catch (error: unknown) {
    console.warn('AudioContext を初期化できませんでした', error)
  }
}

export function playInterventionAudio(url: string): void {
  const audio = new Audio(url)
  audio.play().catch((error: unknown) => {
    console.warn('介入音声の再生に失敗しました', error)
  })
}

let bgmAudio: HTMLAudioElement | null = null

export function startLoopingBgm(url: string): void {
  if (bgmAudio && !bgmAudio.paused && bgmAudio.src === url) {
    return
  }
  stopLoopingBgm()
  bgmAudio = new Audio(url)
  bgmAudio.loop = true
  bgmAudio.play().catch((error: unknown) => {
    console.warn('BGM の再生に失敗しました', error)
    bgmAudio = null
  })
}

export function stopLoopingBgm(): void {
  if (bgmAudio) {
    bgmAudio.pause()
    bgmAudio = null
  }
}

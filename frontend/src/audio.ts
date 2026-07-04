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

export const CAPTURE_INTERVAL_MS = 60_000

const MAX_LONG_EDGE_PX = 768
const JPEG_QUALITY = 0.8

export function resolveCaptureIntervalMs(search: string): number {
  const raw = new URLSearchParams(search).get('interval')
  if (!raw) {
    return CAPTURE_INTERVAL_MS
  }
  const seconds = Number(raw)
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return CAPTURE_INTERVAL_MS
  }
  return Math.round(seconds * 1000)
}

export function captureFrame(video: HTMLVideoElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const { videoWidth, videoHeight } = video
    if (videoWidth === 0 || videoHeight === 0) {
      reject(new Error('カメラ映像がまだ利用できません'))
      return
    }
    const scale = Math.min(1, MAX_LONG_EDGE_PX / Math.max(videoWidth, videoHeight))
    const width = Math.round(videoWidth * scale)
    const height = Math.round(videoHeight * scale)
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) {
      reject(new Error('canvas コンテキストを取得できません'))
      return
    }
    context.drawImage(video, 0, 0, width, height)
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob)
        } else {
          reject(new Error('JPEG への変換に失敗しました'))
        }
      },
      'image/jpeg',
      JPEG_QUALITY,
    )
  })
}

import { useEffect, useRef, useState } from 'react'
import { ApiError, createSession, fetchLatestConfig } from '../api'
import { unlockAudio } from '../audio'
import type { FocusConfig, SessionState } from '../types'

interface HomeViewProps {
  onStartHearing: () => void
  onSessionStart: (session: SessionState, stream: MediaStream) => void
}

export function HomeView({ onStartHearing, onSessionStart }: HomeViewProps) {
  const [config, setConfig] = useState<FocusConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [cameraDenied, setCameraDenied] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const [playingHabitId, setPlayingHabitId] = useState<string | null>(null)
  const previewAudioRef = useRef<HTMLAudioElement | null>(null)

  const stopPreview = () => {
    previewAudioRef.current?.pause()
    previewAudioRef.current = null
    setPlayingHabitId(null)
  }

  const togglePreview = (habitId: string, audioUrl: string) => {
    if (playingHabitId === habitId) {
      stopPreview()
      return
    }
    stopPreview()
    unlockAudio()
    const audio = new Audio(audioUrl)
    audio.onended = () => {
      if (previewAudioRef.current === audio) {
        stopPreview()
      }
    }
    audio.play().catch((error: unknown) => {
      console.warn('試聴の再生に失敗しました', error)
      stopPreview()
    })
    previewAudioRef.current = audio
    setPlayingHabitId(habitId)
  }

  useEffect(() => stopPreview, [])

  useEffect(() => {
    let cancelled = false
    fetchLatestConfig()
      .then((latest) => {
        if (!cancelled) {
          setConfig(latest)
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        if (error instanceof ApiError && error.status === 404) {
          setConfig(null)
        } else {
          setLoadError(error instanceof Error ? error.message : '設定の取得に失敗しました')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  const handleStartSession = async () => {
    if (!config) {
      return
    }
    setStarting(true)
    setCameraDenied(false)
    setStartError(null)
    unlockAudio()

    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true })
    } catch (error: unknown) {
      console.warn('カメラの取得に失敗しました', error)
      setCameraDenied(true)
      setStarting(false)
      return
    }

    try {
      const session = await createSession(config.config_id)
      onSessionStart(session, stream)
    } catch (error: unknown) {
      stream.getTracks().forEach((track) => track.stop())
      setStartError(error instanceof Error ? error.message : 'セッションを開始できませんでした')
      setStarting(false)
    }
  }

  if (loading) {
    return (
      <div className="view home-view">
        <p className="muted">読み込み中...</p>
      </div>
    )
  }

  return (
    <div className="view home-view">
      <header className="app-header">
        <h1>サボり絶対しばく君</h1>
      </header>

      {loadError && <div className="banner banner-error">{loadError}</div>}

      {config ? (
        <section className="card">
          <h2>現在の設定</h2>
          <dl className="config-goal">
            <dt>目標</dt>
            <dd>{config.goal}</dd>
          </dl>
          <h3>やめたい悪習慣</h3>
          <ul className="habit-list">
            {config.habits.map((habit) => (
              <li key={habit.habit_id}>
                <span className="habit-label">{habit.label}</span>
                <span className="habit-method">
                  {habit.method === 'bgm' ? 'BGM' : `音声「${habit.phrase ?? ''}」`}
                </span>
                <button
                  type="button"
                  className="btn btn-ghost btn-small btn-preview"
                  onClick={() => togglePreview(habit.habit_id, habit.audio_url)}
                >
                  {playingHabitId === habit.habit_id ? '⏹ 停止' : '▶ 試聴'}
                </button>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="btn btn-primary btn-large"
            onClick={handleStartSession}
            disabled={starting}
          >
            {starting ? '開始準備中...' : 'セッションを開始する'}
          </button>
          <button type="button" className="btn btn-ghost" onClick={onStartHearing}>
            設定をやり直す（ヒアリング）
          </button>
        </section>
      ) : (
        <section className="card">
          <h2>ようこそ</h2>
          <p>
            まずはヒアリングで、あなたの目標とやめたい悪習慣を教えてください。
            {'\n'}設定が終わると集中セッションを開始できます。
          </p>
          <button type="button" className="btn btn-primary btn-large" onClick={onStartHearing}>
            ヒアリングを始める
          </button>
        </section>
      )}

      {cameraDenied && (
        <div className="banner banner-error">
          <p className="banner-title">カメラへのアクセスが許可されていません</p>
          <p>Focus Guardian はカメラ映像で集中状態を判定するため、カメラの許可が必要です。</p>
          <ol className="recovery-steps">
            <li>ブラウザのアドレスバー左側のカメラ（または鍵）アイコンをクリック</li>
            <li>「カメラ」を「許可」に変更</li>
            <li>ページを再読み込みして、もう一度「セッションを開始する」を押す</li>
          </ol>
        </div>
      )}

      {startError && <div className="banner banner-error">{startError}</div>}
    </div>
  )
}

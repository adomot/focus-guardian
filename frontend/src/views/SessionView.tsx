import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, endSession, postFrame } from '../api'
import { playInterventionAudio } from '../audio'
import { captureFrame, resolveCaptureIntervalMs } from '../capture'
import type { Judgment, JudgmentState, SessionState, SessionSummary } from '../types'

interface StateMeta {
  emoji: string
  className: string
  label: (judgment: Judgment) => string
}

const STATE_META: Record<JudgmentState, StateMeta> = {
  focused: {
    emoji: '🟢',
    className: 'state-focused',
    label: () => '集中中',
  },
  habit: {
    emoji: '🔴',
    className: 'state-habit',
    label: (judgment) => `サボり検知: ${judgment.reason ?? '理由不明'}`,
  },
  absent: {
    emoji: '⚪',
    className: 'state-absent',
    label: () => '不在',
  },
  error: {
    emoji: '🟡',
    className: 'state-error',
    label: () => '判定エラー',
  },
}

const CONNECTION_FAILURE_THRESHOLD = 3

function formatElapsed(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const mm = String(minutes).padStart(2, '0')
  const ss = String(seconds).padStart(2, '0')
  return hours > 0 ? `${hours}:${mm}:${ss}` : `${mm}:${ss}`
}

interface SessionViewProps {
  session: SessionState
  stream: MediaStream
  onEnded: (summary: SessionSummary) => void
  onAborted: (message: string) => void
}

export function SessionView({ session, stream, onEnded, onAborted }: SessionViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const failureCountRef = useRef(0)
  const endingRef = useRef(false)
  const startTimeRef = useRef(Date.now())

  const [latestJudgment, setLatestJudgment] = useState<Judgment | null>(null)
  const [interventionCount, setInterventionCount] = useState(0)
  const [connectionLost, setConnectionLost] = useState(false)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [ending, setEnding] = useState(false)

  const finishSession = useCallback(async () => {
    if (endingRef.current) {
      return
    }
    endingRef.current = true
    setEnding(true)
    stream.getTracks().forEach((track) => track.stop())
    try {
      const summary = await endSession(session.session_id)
      onEnded(summary)
    } catch (error: unknown) {
      console.warn('セッション終了処理に失敗しました', error)
      onAborted(
        error instanceof Error ? error.message : 'セッションの終了処理に失敗しました',
      )
    }
  }, [onAborted, onEnded, session.session_id, stream])

  useEffect(() => {
    const timerId = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
    return () => window.clearInterval(timerId)
  }, [])

  useEffect(() => {
    const video = videoRef.current
    if (!video) {
      return
    }
    video.srcObject = stream
    video.play().catch((error: unknown) => {
      console.warn('プレビューの再生に失敗しました', error)
    })

    let cancelled = false
    let inFlight = false
    let intervalId: number | undefined

    const sendFrame = async () => {
      if (cancelled || inFlight || endingRef.current) {
        return
      }
      inFlight = true
      try {
        const blob = await captureFrame(video)
        const result = await postFrame(session.session_id, blob)
        if (cancelled) {
          return
        }
        failureCountRef.current = 0
        setConnectionLost(false)
        setLatestJudgment(result.judgment)
        if (result.intervention) {
          setInterventionCount((count) => count + 1)
          if (result.intervention.delivered_by === 'browser') {
            playInterventionAudio(result.intervention.audio_url)
          }
        }
      } catch (error: unknown) {
        if (cancelled) {
          return
        }
        if (error instanceof ApiError) {
          if (error.status === 409) {
            void finishSession()
            return
          }
          if (error.status === 429 || error.status < 500) {
            return
          }
        }
        failureCountRef.current += 1
        if (failureCountRef.current >= CONNECTION_FAILURE_THRESHOLD) {
          setConnectionLost(true)
        }
      } finally {
        inFlight = false
      }
    }

    const startLoop = () => {
      if (cancelled) {
        return
      }
      void sendFrame()
      intervalId = window.setInterval(() => {
        void sendFrame()
      }, resolveCaptureIntervalMs(window.location.search))
    }

    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      startLoop()
    } else {
      video.addEventListener('loadeddata', startLoop, { once: true })
    }

    return () => {
      cancelled = true
      video.removeEventListener('loadeddata', startLoop)
      if (intervalId !== undefined) {
        window.clearInterval(intervalId)
      }
    }
  }, [finishSession, session.session_id, stream])

  const meta = latestJudgment ? STATE_META[latestJudgment.state] : null

  return (
    <div className="view session-view">
      <header className="view-header">
        <h1>集中セッション</h1>
        <div className="recording-indicator">
          <span className="recording-dot" />
          監視中
        </div>
      </header>

      {connectionLost && (
        <div className="banner banner-error">
          サーバに接続できません。接続が回復すると自動的に再開します。
        </div>
      )}

      <section className={`status-panel ${meta ? meta.className : 'state-pending'}`}>
        {meta && latestJudgment ? (
          <>
            <div className="status-emoji">{meta.emoji}</div>
            <div className="status-label">{meta.label(latestJudgment)}</div>
          </>
        ) : (
          <>
            <div className="status-emoji">⏳</div>
            <div className="status-label">最初の判定を待っています...</div>
          </>
        )}
      </section>

      <section className="metrics-row">
        <div className="metric-card">
          <div className="metric-value">{formatElapsed(elapsedSeconds)}</div>
          <div className="metric-label">経過時間</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{interventionCount}</div>
          <div className="metric-label">介入回数</div>
        </div>
      </section>

      {latestJudgment?.reason && (
        <section className="card reason-card">
          <h3>直近の判定</h3>
          <p>{latestJudgment.reason}</p>
        </section>
      )}

      <div className="video-wrap">
        <video ref={videoRef} className="camera-preview" muted playsInline />
      </div>

      <button
        type="button"
        className="btn btn-danger btn-large"
        onClick={() => void finishSession()}
        disabled={ending}
      >
        {ending ? '終了処理中...' : 'セッションを終了する'}
      </button>
    </div>
  )
}

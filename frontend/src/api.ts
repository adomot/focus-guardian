import type {
  FocusConfig,
  FrameResult,
  HearingReply,
  HearingTurn,
  SessionState,
  SessionSummary,
} from './types'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

interface ErrorEnvelope {
  error?: {
    code?: string
    message?: string
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    let code = 'unknown_error'
    let message = `サーバエラー (HTTP ${res.status})`
    try {
      const body = (await res.json()) as ErrorEnvelope
      if (body.error) {
        code = body.error.code ?? code
        message = body.error.message ?? message
      }
    } catch {
      // エンベロープが読めない場合は既定メッセージを使う
    }
    throw new ApiError(res.status, code, message)
  }
  return (await res.json()) as T
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function startHearing(): Promise<HearingTurn> {
  return postJson<HearingTurn>('/api/hearing', {})
}

export function replyHearing(hearingId: string, reply: HearingReply): Promise<HearingTurn> {
  return postJson<HearingTurn>(`/api/hearing/${hearingId}/reply`, reply)
}

export function fetchLatestConfig(): Promise<FocusConfig> {
  return request<FocusConfig>('/api/configs/latest')
}

export function createSession(configId?: string): Promise<SessionState> {
  return postJson<SessionState>('/api/sessions', configId ? { config_id: configId } : {})
}

export function postFrame(sessionId: string, image: Blob): Promise<FrameResult> {
  const form = new FormData()
  form.append('image', image, 'frame.jpg')
  return request<FrameResult>(`/api/sessions/${sessionId}/frames`, {
    method: 'POST',
    body: form,
  })
}

export function endSession(sessionId: string): Promise<SessionSummary> {
  return request<SessionSummary>(`/api/sessions/${sessionId}/end`, { method: 'POST' })
}

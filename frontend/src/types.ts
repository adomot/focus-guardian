export type InputMode = 'free_text' | 'choices'
export type InterventionMethod = 'bgm' | 'speech'
export type JudgmentState = 'focused' | 'habit' | 'absent' | 'error'
export type DeliveredBy = 'speaker' | 'browser'

export interface HearingChoice {
  choice_id: string
  label: string
}

export interface HearingTurn {
  hearing_id: string
  bot_message: string
  input_mode: InputMode
  choices: HearingChoice[] | null
  done: boolean
  config_id: string | null
}

export interface HearingReply {
  text: string | null
  choice_id: string | null
}

export interface HabitConfig {
  habit_id: string
  label: string
  method: InterventionMethod
  phrase: string | null
  audio_url: string
}

export interface FocusConfig {
  config_id: string
  goal: string
  habits: HabitConfig[]
}

export interface SessionCounters {
  frames: number
  focused: number
  habit_detected: number
  interventions: number
}

export interface SessionState {
  session_id: string
  config_id: string
  status: string
  started_at: string
  counters: SessionCounters
}

export interface Judgment {
  ts: string
  state: JudgmentState
  habit_id: string | null
  confidence: number | null
  reason: string | null
  error: string | null
}

export interface Intervention {
  intervention_id: string
  habit_id: string | null
  method: InterventionMethod
  audio_url: string
  delivered_by: DeliveredBy
}

export interface FrameResult {
  judgment: Judgment
  intervention: Intervention | null
}

export interface SessionSummary {
  session_id: string
  goal: string
  started_at: string
  ended_at: string
  focused_minutes: number
  frames: number
  habit_detected: number
  interventions: number
  returned_count: number
  habit_breakdown: Record<string, number>
}

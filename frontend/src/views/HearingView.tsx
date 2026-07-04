import { useEffect, useRef, useState } from 'react'
import { replyHearing, startHearing } from '../api'
import type { HearingChoice, HearingTurn } from '../types'
import botAvatar from '../assets/bot-avatar.png'
import { PersonIcon } from '../icons'

const BOT_REPLY_DELAY_MS = 200

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

interface ChatMessage {
  id: number
  role: 'bot' | 'user'
  text: string
}

interface HearingViewProps {
  onBackHome: () => void
}

export function HearingView({ onBackHome }: HearingViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [turn, setTurn] = useState<HearingTurn | null>(null)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const startedRef = useRef(false)
  const messageIdRef = useRef(0)
  const scrollRef = useRef<HTMLDivElement>(null)

  const appendMessage = (role: 'bot' | 'user', text: string) => {
    messageIdRef.current += 1
    const message: ChatMessage = { id: messageIdRef.current, role, text }
    setMessages((prev) => [...prev, message])
  }

  useEffect(() => {
    if (startedRef.current) {
      return
    }
    startedRef.current = true
    setSending(true)
    startHearing()
      .then(async (first) => {
        await wait(BOT_REPLY_DELAY_MS)
        appendMessage('bot', first.bot_message)
        setTurn(first)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'ヒアリングを開始できませんでした')
      })
      .finally(() => setSending(false))
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const send = async (displayText: string, text: string | null, choiceId: string | null) => {
    if (!turn || sending) {
      return
    }
    appendMessage('user', displayText)
    setSending(true)
    setError(null)
    try {
      const next = await replyHearing(turn.hearing_id, { text, choice_id: choiceId })
      await wait(BOT_REPLY_DELAY_MS)
      appendMessage('bot', next.bot_message)
      setTurn(next)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '送信に失敗しました。もう一度お試しください。')
    } finally {
      setSending(false)
    }
  }

  const handleSendText = () => {
    const text = inputText.trim()
    if (!text) {
      return
    }
    setInputText('')
    void send(text, text, null)
  }

  const handleChoice = (choice: HearingChoice) => {
    void send(choice.label, null, choice.choice_id)
  }

  const showFreeText = turn !== null && !turn.done && turn.input_mode === 'free_text'
  const choices = turn !== null && !turn.done ? (turn.choices ?? []) : []

  return (
    <div className="view hearing-view">
      <header className="view-header">
        <h1>ヒアリング</h1>
        <button type="button" className="btn btn-ghost btn-small" onClick={onBackHome}>
          ホームへ
        </button>
      </header>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((message) => (
          <div key={message.id} className={`bubble-row bubble-row-${message.role}`}>
            {message.role === 'bot' && (
              <img className="chat-avatar" src={botAvatar} alt="Focus Guardian" />
            )}
            <div className={`bubble bubble-${message.role}`}>{message.text}</div>
            {message.role === 'user' && (
              <div className="chat-avatar chat-avatar-user">
                <PersonIcon size={17} />
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div className="bubble-row bubble-row-bot">
            <img className="chat-avatar" src={botAvatar} alt="" />
            <div className="bubble bubble-bot bubble-typing">...</div>
          </div>
        )}
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="chat-input-area">
        {choices.length > 0 && (
          <div className="choice-buttons">
            {choices.map((choice) => (
              <button
                key={choice.choice_id}
                type="button"
                className="btn btn-choice"
                onClick={() => handleChoice(choice)}
                disabled={sending}
              >
                {choice.label}
              </button>
            ))}
          </div>
        )}
        {showFreeText && (
          <div className="free-text-row">
            <input
              type="text"
              className="chat-input"
              value={inputText}
              placeholder="メッセージを入力"
              onChange={(event) => setInputText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
                  handleSendText()
                }
              }}
              disabled={sending}
            />
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSendText}
              disabled={sending || inputText.trim() === ''}
            >
              送信
            </button>
          </div>
        )}
        {turn?.done && (
          <button type="button" className="btn btn-primary btn-large" onClick={onBackHome}>
            設定完了！ホームに戻る
          </button>
        )}
      </div>
    </div>
  )
}

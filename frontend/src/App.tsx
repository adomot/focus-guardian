import { useState } from 'react'
import { HomeView } from './views/HomeView'
import { HearingView } from './views/HearingView'
import { SessionView } from './views/SessionView'
import { SummaryView } from './views/SummaryView'
import type { SessionState, SessionSummary } from './types'
import './App.css'

type View =
  | { name: 'home' }
  | { name: 'hearing' }
  | { name: 'session'; session: SessionState; stream: MediaStream }
  | { name: 'summary'; summary: SessionSummary }

function App() {
  const [view, setView] = useState<View>({ name: 'home' })
  const [notice, setNotice] = useState<string | null>(null)

  const goHome = () => {
    setNotice(null)
    setView({ name: 'home' })
  }

  return (
    <div className="app">
      {notice && view.name === 'home' && <div className="banner banner-error">{notice}</div>}
      {view.name === 'home' && (
        <HomeView
          onStartHearing={() => {
            setNotice(null)
            setView({ name: 'hearing' })
          }}
          onSessionStart={(session, stream) => {
            setNotice(null)
            setView({ name: 'session', session, stream })
          }}
        />
      )}
      {view.name === 'hearing' && <HearingView onBackHome={goHome} />}
      {view.name === 'session' && (
        <SessionView
          session={view.session}
          stream={view.stream}
          onEnded={(summary) => setView({ name: 'summary', summary })}
          onAborted={(message) => {
            setNotice(message)
            setView({ name: 'home' })
          }}
        />
      )}
      {view.name === 'summary' && <SummaryView summary={view.summary} onBackHome={goHome} />}
    </div>
  )
}

export default App

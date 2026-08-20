import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

export default function ChatWindow({ getToken, chatId, onBack }) {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef(null)

  useEffect(() => {
    setLoading(true)
    api.listMessages(getToken, chatId).then((msgs) => {
      setMessages(msgs)
      setLoading(false)
    })
  }, [chatId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    const content = draft.trim()
    if (!content || sending) return

    // Optimistic render of the user's message
    setMessages((prev) => [...prev, { id: `temp-${Date.now()}`, role: 'user', content }])
    setDraft('')
    setSending(true)
    try {
      const assistantMessage = await api.sendMessage(getToken, chatId, content)
      setMessages((prev) => [...prev, assistantMessage])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="h-12 shrink-0 border-b border-line flex items-center px-4 gap-3">
        <button onClick={onBack} className="text-sm text-muted hover:text-ink">
          ← Back
        </button>
        <span className="text-sm font-medium">Chat</span>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-3">
        {loading && <p className="text-sm text-muted">Loading…</p>}
        {!loading && messages.length === 0 && (
          <p className="text-sm text-muted">Ask something about the documents in this folder.</p>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[70%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                m.role === 'user' ? 'bg-ink text-white' : 'bg-ink/5 text-ink'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {sending && <p className="text-xs text-muted">Assistant is typing…</p>}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 border-t border-line p-4 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message…"
          className="flex-1 border border-line rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <button
          onClick={handleSend}
          disabled={sending || !draft.trim()}
          className="px-4 py-2 rounded-md bg-ink text-white text-sm font-medium disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  )
}

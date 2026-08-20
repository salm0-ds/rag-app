import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function FolderView({ getToken, folderId, onSelectChat }) {
  const [documents, setDocuments] = useState([])
  const [chats, setChats] = useState([])
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([api.listDocuments(getToken, folderId), api.listChats(getToken, folderId)]).then(
      ([docs, chatList]) => {
        if (cancelled) return
        setDocuments(docs)
        setChats(chatList)
        setLoading(false)
      }
    )
    return () => {
      cancelled = true
    }
  }, [folderId])

  async function handleUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const doc = await api.uploadDocument(getToken, folderId, file)
      setDocuments((prev) => [...prev, doc])
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function handleDeleteDoc(id) {
    await api.deleteDocument(getToken, id)
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }

  async function handleNewChat() {
    const title = prompt('Chat title', 'New chat') || 'New chat'
    const chat = await api.createChat(getToken, folderId, title)
    setChats((prev) => [...prev, chat])
    onSelectChat(chat.id)
  }

  async function handleDeleteChat(id) {
    if (!confirm('Delete this chat?')) return
    await api.deleteChat(getToken, id)
    setChats((prev) => prev.filter((c) => c.id !== id))
  }

  if (loading) return <div className="p-6 text-sm text-muted">Loading…</div>

  return (
    <div className="h-full overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* Documents */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">Documents</h2>
          <label className="text-sm text-accent hover:underline cursor-pointer">
            {uploading ? 'Uploading…' : '+ Upload'}
            <input type="file" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
        </div>

        {documents.length === 0 && <p className="text-sm text-muted">No documents yet.</p>}

        <ul className="space-y-1">
          {documents.map((doc) => (
            <li
              key={doc.id}
              className="group flex items-center justify-between text-sm border border-line rounded-md px-3 py-2"
            >
              <span className="truncate">{doc.filename}</span>
              <div className="flex items-center gap-3">
                {doc.status && <span className="text-xs text-muted">{doc.status}</span>}
                <button
                  onClick={() => handleDeleteDoc(doc.id)}
                  className="hidden group-hover:inline text-muted"
                  aria-label="Delete document"
                >
                  ✕
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* Chats */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">Chats</h2>
          <button onClick={handleNewChat} className="text-sm text-accent hover:underline">
            + New chat
          </button>
        </div>

        {chats.length === 0 && <p className="text-sm text-muted">No chats yet.</p>}

        <ul className="space-y-1">
          {chats.map((chat) => (
            <li
              key={chat.id}
              className="group flex items-center justify-between text-sm border border-line rounded-md px-3 py-2 cursor-pointer hover:bg-ink/5"
              onClick={() => onSelectChat(chat.id)}
            >
              <span className="truncate">{chat.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDeleteChat(chat.id)
                }}
                className="hidden group-hover:inline text-muted"
                aria-label="Delete chat"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

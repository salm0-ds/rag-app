import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function Sidebar({ getToken, selectedFolderId, onSelectFolder }) {
  const [folders, setFolders] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [draftName, setDraftName] = useState('')

  useEffect(() => {
    refresh()
  }, [])

  async function refresh() {
    setLoading(true)
    try {
      setFolders(await api.listFolders(getToken))
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate() {
    const name = prompt('Folder name')
    if (!name) return
    const folder = await api.createFolder(getToken, name)
    setFolders((prev) => [...prev, folder])
  }

  function startRename(folder) {
    setEditingId(folder.id)
    setDraftName(folder.name)
  }

  async function commitRename(id) {
    if (!draftName.trim()) return setEditingId(null)
    const updated = await api.renameFolder(getToken, id, draftName.trim())
    setFolders((prev) => prev.map((f) => (f.id === id ? updated : f)))
    setEditingId(null)
  }

  async function handleDelete(id) {
    if (!confirm('Delete this folder and everything in it?')) return
    await api.deleteFolder(getToken, id)
    setFolders((prev) => prev.filter((f) => f.id !== id))
    if (selectedFolderId === id) onSelectFolder(null)
  }

  return (
    <aside className="w-64 shrink-0 border-r border-line flex flex-col">
      <div className="h-14 flex items-center justify-between px-4 border-b border-line">
        <span className="font-semibold text-sm">Folders</span>
        <button
          onClick={handleCreate}
          className="text-sm text-accent hover:underline"
          aria-label="Create folder"
        >
          + New
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {loading && <p className="px-4 py-2 text-sm text-muted">Loading…</p>}
        {!loading && folders.length === 0 && (
          <p className="px-4 py-2 text-sm text-muted">No folders yet.</p>
        )}

        {folders.map((folder) => (
          <div
            key={folder.id}
            className={`group flex items-center justify-between px-4 py-2 cursor-pointer text-sm ${
              selectedFolderId === folder.id ? 'bg-ink/5 font-medium' : 'hover:bg-ink/5'
            }`}
          >
            {editingId === folder.id ? (
              <input
                autoFocus
                value={draftName}
                onChange={(e) => setDraftName(e.target.value)}
                onBlur={() => commitRename(folder.id)}
                onKeyDown={(e) => e.key === 'Enter' && commitRename(folder.id)}
                className="flex-1 border border-line rounded px-1 py-0.5 text-sm mr-2"
              />
            ) : (
              <span className="truncate flex-1" onClick={() => onSelectFolder(folder.id)}>
                {folder.name}
              </span>
            )}

            <div className="hidden group-hover:flex gap-2 ml-2 text-muted">
              <button onClick={() => startRename(folder)} aria-label="Rename folder">
                ✎
              </button>
              <button onClick={() => handleDelete(folder.id)} aria-label="Delete folder">
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </aside>
  )
}

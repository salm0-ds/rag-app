const BASE_URL = import.meta.env.VITE_API_BASE_URL

/**
 * Every call needs a `getToken` function — pass in Clerk's `useAuth().getToken`.
 * Handles both JSON bodies and multipart file uploads.
 */
async function request(getToken, path, { method = 'GET', body, isFormData = false } = {}) {
  const token = await getToken()

  const headers = { Authorization: `Bearer ${token}` }
  if (!isFormData) headers['Content-Type'] = 'application/json'

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${method} ${path} failed (${res.status}): ${text}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Folders
  listFolders: (getToken) => request(getToken, '/folders'),
  createFolder: (getToken, name) => request(getToken, '/folders', { method: 'POST', body: { name } }),
  renameFolder: (getToken, id, name) => request(getToken, `/folders/${id}`, { method: 'PATCH', body: { name } }),
  deleteFolder: (getToken, id) => request(getToken, `/folders/${id}`, { method: 'DELETE' }),

  // Documents
  listDocuments: (getToken, folderId) => request(getToken, `/folders/${folderId}/documents`),
  uploadDocument: (getToken, folderId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(getToken, `/folders/${folderId}/documents`, { method: 'POST', body: form, isFormData: true })
  },
  deleteDocument: (getToken, id) => request(getToken, `/documents/${id}`, { method: 'DELETE' }),

  // Chats
  listChats: (getToken, folderId) => request(getToken, `/folders/${folderId}/chats`),
  createChat: (getToken, folderId, title) =>
    request(getToken, `/folders/${folderId}/chats`, { method: 'POST', body: { title } }),
  deleteChat: (getToken, id) => request(getToken, `/chats/${id}`, { method: 'DELETE' }),

  // Messages
  listMessages: (getToken, chatId) => request(getToken, `/chats/${chatId}/messages`),
  sendMessage: (getToken, chatId, content) =>
    request(getToken, `/chats/${chatId}/messages`, { method: 'POST', body: { content } }),
}

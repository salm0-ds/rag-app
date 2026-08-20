# RAG Console — Frontend

Minimal Vite + React SPA for your multi-tenant RAG backend. Clerk handles auth,
plain `fetch` + `useState` handle everything else — no Redux/Zustand/React Query,
on purpose, so the whole data flow stays traceable in ~6 files.

## Setup

```bash
npm install
cp .env.example .env   # fill in your Clerk publishable key + API base URL
npm run dev
```

## File map (8 files total)

```
src/
  main.jsx              # wraps App in <ClerkProvider>
  App.jsx                # signed-in/out gate + owns selectedFolderId/selectedChatId
  api.js                  # one fetch wrapper, attaches Clerk JWT to every call
  index.css                # tailwind + base styles
  components/
    Sidebar.jsx             # folder list: create/rename/delete
    FolderView.jsx           # documents (upload/list) + chats (list/create) for a folder
    ChatWindow.jsx            # message history + input for one chat
```

## How state flows

`App.jsx` is the only place that holds `selectedFolderId` and `selectedChatId`.
Everything else is a dumb child that receives IDs as props and fetches its own
slice of data with `useEffect`. Selecting a folder always clears the open chat —
that's the one rule enforced at the top level, mirroring the DB hierarchy
(`folder → documents / chats → messages`).

## Backend contract this frontend assumes

Adjust paths in `src/api.js` if your FastAPI routes differ.

| Method | Path                              | Body                  | Returns          |
|--------|------------------------------------|------------------------|-------------------|
| GET    | `/folders`                          | —                       | `Folder[]`         |
| POST   | `/folders`                          | `{ name }`               | `Folder`            |
| PATCH  | `/folders/{id}`                      | `{ name }`               | `Folder`            |
| DELETE | `/folders/{id}`                      | —                       | 204               |
| GET    | `/folders/{folder_id}/documents`      | —                       | `Document[]`        |
| POST   | `/folders/{folder_id}/documents`      | multipart `file`         | `Document`           |
| DELETE | `/documents/{id}`                    | —                       | 204               |
| GET    | `/folders/{folder_id}/chats`          | —                       | `Chat[]`             |
| POST   | `/folders/{folder_id}/chats`          | `{ title }`               | `Chat`                |
| DELETE | `/chats/{id}`                        | —                       | 204               |
| GET    | `/chats/{chat_id}/messages`           | —                       | `Message[]`           |
| POST   | `/chats/{chat_id}/messages`           | `{ content }`             | `Message` (assistant)   |

Every request carries `Authorization: Bearer <clerk_jwt>`. On your FastAPI side,
verify that JWT (Clerk's Python SDK or a JWKS check) and derive `user_id` from
it server-side — the frontend never sends `user_id` directly, which is what
keeps tenant isolation honest.

Expected shapes (adjust field names to match your Pydantic models):

```ts
Folder   { id, name }
Document { id, filename, status }
Chat     { id, title }
Message  { id, role: "user" | "assistant", content }
```

## Notes

- No router — folder/chat selection is just React state, since the whole app
  is one screen. Add `react-router` only if you need shareable URLs later.
- Auth token is fetched fresh on every request (`getToken()` from Clerk),
  so you don't need to think about refresh logic.
- File upload uses native `<input type="file">` + `FormData`, no upload library.

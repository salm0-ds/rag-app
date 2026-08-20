import { useState } from 'react'
import { SignedIn, SignedOut, SignInButton, UserButton, useAuth } from '@clerk/clerk-react'
import Sidebar from './components/Sidebar.jsx'
import FolderView from './components/FolderView.jsx'
import ChatWindow from './components/ChatWindow.jsx'

export default function App() {
  return (
    <>
      <SignedOut>
        <SignInScreen />
      </SignedOut>
      <SignedIn>
        <Dashboard />
      </SignedIn>
    </>
  )
}

function SignInScreen() {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">RAG Console</h1>
        <p className="text-muted mt-1">Sign in to access your folders and documents.</p>
      </div>
      <SignInButton mode="modal">
        <button className="px-4 py-2 rounded-md bg-ink text-white text-sm font-medium hover:opacity-90">
          Sign in
        </button>
      </SignInButton>
    </div>
  )
}

function Dashboard() {
  const { getToken } = useAuth()
  const [selectedFolderId, setSelectedFolderId] = useState(null)
  const [selectedChatId, setSelectedChatId] = useState(null)

  function selectFolder(id) {
    setSelectedFolderId(id)
    setSelectedChatId(null) // switching folders always clears the open chat
  }

  return (
    <div className="h-full flex">
      <Sidebar
        getToken={getToken}
        selectedFolderId={selectedFolderId}
        onSelectFolder={selectFolder}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 border-b border-line flex items-center justify-between px-6">
          <span className="text-sm text-muted">RAG Console</span>
          <UserButton afterSignOutUrl="/" />
        </header>

        <main className="flex-1 min-h-0">
          {!selectedFolderId && (
            <div className="h-full flex items-center justify-center text-muted text-sm">
              Select or create a folder to get started.
            </div>
          )}

          {selectedFolderId && !selectedChatId && (
            <FolderView
              getToken={getToken}
              folderId={selectedFolderId}
              onSelectChat={setSelectedChatId}
            />
          )}

          {selectedFolderId && selectedChatId && (
            <ChatWindow
              getToken={getToken}
              chatId={selectedChatId}
              onBack={() => setSelectedChatId(null)}
            />
          )}
        </main>
      </div>
    </div>
  )
}

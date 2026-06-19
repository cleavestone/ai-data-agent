import { useChat } from './hooks/useChat'
import { Header } from './components/Header'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'

export default function App() {
  const { messages, loading, submit, clearMessages, bottomRef } = useChat()

  return (
    <div className="h-screen flex flex-col bg-bg text-text overflow-hidden">
      <Header onNewChat={messages.length > 0 ? clearMessages : undefined} />
      <MessageList
        messages={messages}
        bottomRef={bottomRef}
        onSelectExample={submit}
      />
      <ChatInput onSubmit={submit} loading={loading} />
    </div>
  )
}

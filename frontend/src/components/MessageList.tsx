import type { RefObject } from 'react'
import type { Message } from '../types/chat'
import { MessageGroup } from './MessageGroup'
import { EmptyState } from './EmptyState'

interface MessageListProps {
  messages: Message[]
  bottomRef: RefObject<HTMLDivElement>
  onSelectExample: (question: string) => void
}

export function MessageList({ messages, bottomRef, onSelectExample }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto">
        <EmptyState onSelect={onSelectExample} />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {messages.map(msg => (
          <MessageGroup key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}

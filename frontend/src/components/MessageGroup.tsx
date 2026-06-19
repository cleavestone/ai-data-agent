import type { Message } from '../types/chat'
import { ThinkingCard } from './ThinkingCard'
import { ResponseCard } from './ResponseCard'

interface MessageGroupProps {
  message: Message
}

export function MessageGroup({ message }: MessageGroupProps) {
  return (
    <div className="space-y-3 animate-fadeUp">
      {/* User bubble — right aligned */}
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-accent-dim border border-accent/30 text-text text-sm leading-relaxed">
          {message.question}
        </div>
      </div>

      {/* AI response */}
      {message.type === 'thinking' && <ThinkingCard />}

      {message.type === 'answer' && message.response && (
        <ResponseCard response={message.response} />
      )}

      {message.type === 'error' && (
        <div className="rounded-xl bg-surface border border-error/30 p-4 text-error text-sm">
          {message.errorMessage ?? 'Something went wrong. Please try again.'}
        </div>
      )}
    </div>
  )
}

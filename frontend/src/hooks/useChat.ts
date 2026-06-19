import { useState, useCallback, useRef, useEffect } from 'react'
import { sendQuestion } from '../api/client'
import type { Message } from '../types/chat'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 50)
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const submit = useCallback(
    async (question: string) => {
      if (loading || !question.trim()) return

      const id = crypto.randomUUID()

      setMessages(prev => [
        ...prev,
        { id, type: 'thinking', question },
      ])
      setLoading(true)

      try {
        const response = await sendQuestion(question)

        setMessages(prev =>
          prev.map(msg =>
            msg.id === id
              ? response.success
                ? { id, type: 'answer', question, response }
                : { id, type: 'error', question, errorMessage: response.error ?? response.answer }
              : msg
          )
        )
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Request failed. Please try again.'

        setMessages(prev =>
          prev.map(msg =>
            msg.id === id ? { id, type: 'error', question, errorMessage } : msg
          )
        )
      } finally {
        setLoading(false)
      }
    },
    [loading]
  )

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, loading, submit, clearMessages, bottomRef }
}

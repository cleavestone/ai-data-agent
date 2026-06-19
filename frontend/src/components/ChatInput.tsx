import { useRef, useCallback, type KeyboardEvent } from 'react'

interface ChatInputProps {
  onSubmit: (question: string) => void
  loading: boolean
}

export function ChatInput({ onSubmit, loading }: ChatInputProps) {
  const ref = useRef<HTMLTextAreaElement>(null)

  const resize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`
  }, [])

  const submit = useCallback(() => {
    const val = ref.current?.value.trim() ?? ''
    if (!val || loading) return
    onSubmit(val)
    if (ref.current) {
      ref.current.value = ''
      resize()
    }
  }, [loading, onSubmit, resize])

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-border bg-surface px-4 py-4 shrink-0">
      <div className="max-w-3xl mx-auto space-y-2">
        <div
          className={`flex items-end gap-3 rounded-xl border bg-surface2 px-4 py-3 transition-all duration-300 ${
            loading
              ? 'border-accent animate-pulseGlow'
              : 'border-border focus-within:border-accent/50'
          }`}
        >
          <textarea
            ref={ref}
            rows={1}
            placeholder="Ask anything about your data…"
            disabled={loading}
            onInput={resize}
            onKeyDown={onKeyDown}
            className="flex-1 resize-none bg-transparent text-text text-sm placeholder:text-muted
                       outline-none disabled:opacity-50 leading-relaxed"
            style={{ minHeight: '24px', maxHeight: '96px' }}
          />

          <button
            onClick={submit}
            disabled={loading}
            aria-label="Send"
            className="shrink-0 w-8 h-8 flex items-center justify-center rounded-lg bg-accent
                       text-white hover:bg-accent/80 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
          >
            {/* Send / arrow icon */}
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        <p className="text-center text-muted text-[11px]">
          Enter to send · Shift + Enter for new line
        </p>
      </div>
    </div>
  )
}

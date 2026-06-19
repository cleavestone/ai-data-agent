import { useEffect, useState } from 'react'
import { getHealth } from '../api/client'
import type { HealthResponse } from '../types/chat'

interface HeaderProps {
  onNewChat?: () => void
}

type HealthStatus = HealthResponse['status'] | 'checking'

const DOT_CLASS: Record<HealthStatus, string> = {
  checking:  'bg-warning animate-pulse',
  healthy:   'bg-success',
  degraded:  'bg-warning',
  unhealthy: 'bg-error',
}

const STATUS_TEXT: Record<HealthStatus, string> = {
  checking:  'Checking...',
  healthy:   'All systems operational',
  degraded:  'Degraded',
  unhealthy: 'Offline',
}

export function Header({ onNewChat }: HeaderProps) {
  const [status, setStatus] = useState<HealthStatus>('checking')

  const check = async () => {
    try {
      const data = await getHealth()
      setStatus(data.status)
    } catch {
      setStatus('unhealthy')
    }
  }

  useEffect(() => {
    void check()
    const id = setInterval(() => void check(), 30_000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface shrink-0">
      <div className="font-mono text-xl font-bold tracking-tight select-none">
        <span className="text-text">Data</span>
        <span className="text-accent">Agent</span>
      </div>

      <div className="flex items-center gap-4">
        {onNewChat && (
          <button
            onClick={onNewChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border
                       text-xs text-muted hover:text-text hover:border-accent/50
                       transition-all duration-150 font-mono"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New chat
          </button>
        )}
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full shrink-0 ${DOT_CLASS[status]}`} />
          <span className="font-mono text-xs text-muted">{STATUS_TEXT[status]}</span>
        </div>
      </div>
    </header>
  )
}

import { useState, type ReactNode } from 'react'
import type { ChatResponse } from '../types/chat'
import { Visualisation } from './visualisations'
import { formatExecutionTime } from '../lib/formatters'

interface ResponseCardProps {
  response: ChatResponse
}

const VIZ_LABELS: Record<string, string> = {
  table:      'Table',
  bar_chart:  'Bar Chart',
  line_chart: 'Line Chart',
  stat_card:  'Stat',
  text_only:  'Text',
}

function renderInline(line: string): ReactNode[] {
  return line.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i} className="text-text font-semibold">{part.slice(2, -2)}</strong>
      : <span key={i}>{part}</span>
  )
}

function MarkdownAnswer({ text }: { text: string }) {
  const lines = text.split('\n')
  return (
    <div className="text-text text-sm space-y-1" style={{ lineHeight: 1.7 }}>
      {lines.map((line, i) => {
        if (!line.trim()) return <br key={i} />
        const isNumbered = /^\d+\./.test(line.trim())
        return (
          <p key={i} className={isNumbered ? 'pl-2' : ''}>
            {renderInline(line)}
          </p>
        )
      })}
    </div>
  )
}

function SqlPanel({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="border-t border-border/50 pt-2">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-1.5 text-[11px] text-muted hover:text-dim transition-colors font-mono select-none"
      >
        <svg
          width="10" height="10" viewBox="0 0 10 10" fill="currentColor"
          style={{ transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s' }}
        >
          <polygon points="2,1 8,5 2,9" />
        </svg>
        {open ? 'Hide SQL' : 'View SQL'}
      </button>

      {open && (
        <div className="mt-2 relative group">
          <pre className="text-[11px] font-mono text-dim bg-bg border border-border/60 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {sql}
          </pre>
          <button
            onClick={copy}
            className="absolute top-2 right-2 px-2 py-1 rounded text-[10px] font-mono
                       bg-surface2 border border-border text-muted hover:text-text
                       hover:border-accent/40 transition-all opacity-0 group-hover:opacity-100"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      )}
    </div>
  )
}

export function ResponseCard({ response }: ResponseCardProps) {
  const hasData = response.row_count > 0 && response.columns.length > 0
  const hasSql = Boolean(response.sql_executed?.trim())

  return (
    <div className="rounded-xl bg-surface border border-border p-4 space-y-3">
      <MarkdownAnswer text={response.answer} />

      {hasData && (
        <>
          <div className="flex items-center gap-3 text-xs text-muted border-t border-border pt-3 flex-wrap">
            <span>{response.row_count.toLocaleString()} rows</span>
            <span className="text-border">·</span>
            {response.cached ? (
              <span className="text-accent font-mono">⚡ cached</span>
            ) : (
              <span>{formatExecutionTime(response.execution_time_ms)}</span>
            )}
            <span className="text-border">·</span>
            <span className="px-1.5 py-0.5 rounded bg-surface2 border border-border font-mono text-[10px] text-dim">
              {VIZ_LABELS[response.visualisation] ?? response.visualisation}
            </span>
          </div>

          <div className="pt-1">
            <Visualisation response={response} />
          </div>
        </>
      )}

      {hasSql && <SqlPanel sql={response.sql_executed} />}
    </div>
  )
}

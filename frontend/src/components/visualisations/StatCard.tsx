import { formatValue } from '../../lib/formatters'

interface StatCardProps {
  columns: string[]
  rows: Record<string, unknown>[]
}

export function StatCard({ columns, rows }: StatCardProps) {
  const col = columns[0]
  const value = rows[0]?.[col]

  return (
    <div className="py-4">
      <div className="font-mono text-4xl font-bold text-accent">
        {formatValue(value)}
      </div>
      <div className="text-xs text-muted uppercase tracking-widest mt-2">
        {col?.replace(/_/g, ' ')}
      </div>
    </div>
  )
}

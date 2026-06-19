export function isNumeric(value: unknown): value is number {
  return typeof value === 'number' && !isNaN(value)
}

export function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'

  if (typeof value === 'number') {
    return Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
  }

  if (typeof value === 'string') {
    // Full ISO datetime
    if (/^\d{4}-\d{2}-\d{2}T/.test(value)) {
      return new Date(value).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    }
    // Date only
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    }
    // YYYY-MM monthly format
    if (/^\d{4}-\d{2}$/.test(value)) {
      const [year, month] = value.split('-').map(Number)
      return new Date(year, month - 1).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
      })
    }
  }

  return String(value)
}

export function formatExecutionTime(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

export function formatCompactNumber(value: unknown): string {
  if (typeof value !== 'number') return String(value ?? '')
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toLocaleString(undefined, { maximumFractionDigits: 1 })
}

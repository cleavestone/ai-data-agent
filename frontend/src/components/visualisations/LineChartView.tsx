import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatValue, formatCompactNumber, isNumeric } from '../../lib/formatters'

const COLORS = ['#4F8EF7', '#10B981', '#F59E0B', '#EF4444', '#7B5EA7']
const TIME_PATTERNS = ['month', 'week', 'day', 'date', 'year', 'period', 'time']

interface LineChartViewProps {
  columns: string[]
  rows: Record<string, unknown>[]
}

function formatTimeLabel(val: unknown): string {
  if (typeof val !== 'string') return String(val ?? '')
  if (/^\d{4}-\d{2}-\d{2}T/.test(val) || /^\d{4}-\d{2}-\d{2}$/.test(val)) {
    return new Date(val).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
  }
  if (/^\d{4}-\d{2}$/.test(val)) {
    const [year, month] = val.split('-').map(Number)
    return new Date(year, month - 1).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
  }
  return val
}

export function LineChartView({ columns, rows }: LineChartViewProps) {
  const timeCol =
    columns.find(c => TIME_PATTERNS.some(p => c.toLowerCase().includes(p))) ?? columns[0]
  const numericCols = columns.filter(c => c !== timeCol && isNumeric(rows[0]?.[c]))

  if (!numericCols.length) return null

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2A3560" vertical={false} />
        <XAxis
          dataKey={timeCol}
          tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'Inter' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={formatTimeLabel}
        />
        <YAxis
          tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={formatCompactNumber}
        />
        <Tooltip
          contentStyle={{
            background: '#1A2340',
            border: '1px solid #2A3560',
            borderRadius: 8,
            color: '#E8F0FF',
            fontSize: 12,
          }}
          formatter={(value: number | string) => [formatValue(value), '']}
          labelFormatter={formatTimeLabel}
        />
        {numericCols.map((col, i) => (
          <Line
            key={col}
            type="monotone"
            dataKey={col}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3, fill: COLORS[i % COLORS.length], strokeWidth: 0 }}
            activeDot={{ r: 5, fill: COLORS[i % COLORS.length], strokeWidth: 0 }}
            name={col.replace(/_/g, ' ')}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

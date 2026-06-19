import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { formatValue, formatCompactNumber, isNumeric } from '../../lib/formatters'

const COLORS = ['#4F8EF7', '#7B5EA7', '#10B981', '#F59E0B', '#EF4444', '#06B6D4']

interface BarChartViewProps {
  columns: string[]
  rows: Record<string, unknown>[]
}

export function BarChartView({ columns, rows }: BarChartViewProps) {
  const categoryCol = columns.find(c => !isNumeric(rows[0]?.[c])) ?? columns[0]
  const numericCols = columns.filter(c => c !== categoryCol && isNumeric(rows[0]?.[c]))

  if (!numericCols.length) return null

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={rows} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2A3560" vertical={false} />
        <XAxis
          dataKey={categoryCol}
          tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'Inter' }}
          axisLine={false}
          tickLine={false}
          interval={0}
          angle={rows.length > 6 ? -30 : 0}
          textAnchor={rows.length > 6 ? 'end' : 'middle'}
          height={rows.length > 6 ? 48 : 24}
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
          cursor={{ fill: 'rgba(79, 142, 247, 0.08)' }}
          formatter={(value: number | string) => [formatValue(value), '']}
        />
        {numericCols.map((col, i) => (
          <Bar
            key={col}
            dataKey={col}
            fill={COLORS[i % COLORS.length]}
            radius={[4, 4, 0, 0]}
            name={col.replace(/_/g, ' ')}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

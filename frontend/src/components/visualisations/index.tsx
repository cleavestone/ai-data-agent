import type { ChatResponse } from '../../types/chat'
import { StatCard } from './StatCard'
import { DataTable } from './DataTable'
import { BarChartView } from './BarChartView'
import { LineChartView } from './LineChartView'

interface VisualisationProps {
  response: ChatResponse
}

export function Visualisation({ response }: VisualisationProps) {
  const { visualisation, columns, rows } = response

  if (!rows.length || !columns.length) return null

  switch (visualisation) {
    case 'stat_card':
      return <StatCard columns={columns} rows={rows} />
    case 'bar_chart':
      return <BarChartView columns={columns} rows={rows} />
    case 'line_chart':
      return <LineChartView columns={columns} rows={rows} />
    case 'table':
      return <DataTable columns={columns} rows={rows} />
    default:
      return null
  }
}

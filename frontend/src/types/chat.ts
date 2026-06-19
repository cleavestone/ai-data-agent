export interface ChatRequest {
  question: string
}

export type VisualisationType =
  | 'table'
  | 'bar_chart'
  | 'line_chart'
  | 'stat_card'
  | 'text_only'

export interface ChatResponse {
  success: boolean
  answer: string
  visualisation: VisualisationType
  columns: string[]
  rows: Record<string, unknown>[]
  row_count: number
  cached: boolean
  execution_time_ms: number
  sql_executed: string
  error: string | null
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  postgres_admin: boolean
  postgres_readonly: boolean
  redis: boolean
  version: string
}

export type MessageType = 'thinking' | 'answer' | 'error'

export interface Message {
  id: string
  type: MessageType
  question: string
  response?: ChatResponse
  errorMessage?: string
}

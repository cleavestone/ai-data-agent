import axios from 'axios'
import type { ChatResponse, HealthResponse } from '../types/chat'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export async function sendQuestion(question: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/api/v1/chat', { question })
  return data
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/api/v1/health')
  return data
}

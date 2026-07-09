import api from './client'
import type { URLAnalytics } from '../types'

export async function getAnalytics(shortCode: string): Promise<URLAnalytics> {
  const { data } = await api.get<URLAnalytics>(`/api/v1/analytics/${shortCode}`)
  return data
}

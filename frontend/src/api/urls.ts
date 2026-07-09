import api from './client'
import type { URLItem, URLCreatePayload } from '../types'

export async function shortenURL(payload: URLCreatePayload): Promise<URLItem> {
  const { data } = await api.post<URLItem>('/api/v1/urls/', payload)
  return data
}

export async function listURLs(): Promise<URLItem[]> {
  const { data } = await api.get<URLItem[]>('/api/v1/urls/')
  return data
}

export async function deleteURL(shortCode: string): Promise<void> {
  await api.delete(`/api/v1/urls/${shortCode}`)
}

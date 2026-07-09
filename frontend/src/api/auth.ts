import api from './client'
import type { User, TokenResponse } from '../types'

export async function signup(email: string, password: string): Promise<User> {
  const { data } = await api.post<User>('/api/v1/auth/signup', { email, password })
  return data
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  const { data } = await api.post<TokenResponse>('/api/v1/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

import { apiClient } from './client'

export interface LoginPayload {
  username: string
  password: string
  remember_me?: boolean
}

export interface User {
  id: number
  username: string
  is_active: boolean
  is_admin: boolean
}

export async function login(payload: LoginPayload) {
  const { data } = await apiClient.post<{ access_token: string; token_type: string }>('/auth/login', payload)
  return data
}

export async function getMe() {
  const { data } = await apiClient.get<User>('/auth/me')
  return data
}


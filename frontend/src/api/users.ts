import { apiClient } from './client'

export interface ManagedUser {
  id: number
  username: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface UserListResponse {
  items: ManagedUser[]
  total: number
  page: number
  page_size: number
}

export async function fetchUsers(params: { page: number; pageSize: number; keyword?: string; isActive?: boolean | '' }) {
  const { data } = await apiClient.get<UserListResponse>('/users', {
    params: {
      page: params.page,
      page_size: params.pageSize,
      keyword: params.keyword || undefined,
      is_active: params.isActive === '' ? undefined : params.isActive
    }
  })
  return data
}

export async function createUser(payload: { username: string; password: string }) {
  const { data } = await apiClient.post<ManagedUser>('/users', payload)
  return data
}

export async function updateUser(userId: number, payload: { username?: string; password?: string }) {
  const { data } = await apiClient.put<ManagedUser>(`/users/${userId}`, payload)
  return data
}

export async function updateUserStatus(userId: number, isActive: boolean) {
  const { data } = await apiClient.patch<ManagedUser>(`/users/${userId}/status`, { is_active: isActive })
  return data
}

export async function deleteUser(userId: number) {
  await apiClient.delete(`/users/${userId}`)
}

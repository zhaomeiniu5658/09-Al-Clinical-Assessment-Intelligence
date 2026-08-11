import { apiClient } from './client'

export interface KnowledgeEntry {
  id: number
  title: string
  category: string
  summary: string | null
  content: string
  attachment_name: string | null
  attachment_mime_type: string | null
  attachment_size: number | null
  created_by_id: number
  created_by_username: string
  created_at: string
  updated_at: string
}

export interface KnowledgeListResponse {
  items: KnowledgeEntry[]
  total: number
  page: number
  page_size: number
}

export interface KnowledgeCategory {
  id: number
  name: string
  created_at: string
}

export interface KnowledgeExternalApiSettings {
  is_enabled: boolean
  key_configured: boolean
  api_key_prefix: string | null
  api_key: string | null
  updated_at: string | null
}

export async function fetchKnowledge(params: { page: number; pageSize: number; keyword?: string; category?: string }) {
  const { data } = await apiClient.get<KnowledgeListResponse>('/knowledge', {
    params: { page: params.page, page_size: params.pageSize, keyword: params.keyword || undefined, category: params.category || undefined }
  })
  return data
}

export async function fetchKnowledgeEntry(entryId: number) {
  const { data } = await apiClient.get<KnowledgeEntry>(`/knowledge/${entryId}`)
  return data
}

export async function createKnowledgeEntry(payload: FormData) {
  const { data } = await apiClient.post<KnowledgeEntry>('/knowledge', payload)
  return data
}

export async function updateKnowledgeEntry(entryId: number, payload: FormData) {
  const { data } = await apiClient.put<KnowledgeEntry>(`/knowledge/${entryId}`, payload)
  return data
}

export async function deleteKnowledgeEntry(entryId: number) {
  await apiClient.delete(`/knowledge/${entryId}`)
}

export async function fetchKnowledgeCategories() {
  const { data } = await apiClient.get<KnowledgeCategory[]>('/knowledge/categories')
  return data
}

export async function createKnowledgeCategory(name: string) {
  const { data } = await apiClient.post<KnowledgeCategory>('/knowledge/categories', { name })
  return data
}

export async function deleteKnowledgeCategory(categoryId: number) {
  await apiClient.delete(`/knowledge/categories/${categoryId}`)
}

export async function fetchKnowledgeExternalApiSettings() {
  const { data } = await apiClient.get<KnowledgeExternalApiSettings>('/knowledge/external-api')
  return data
}

export async function updateKnowledgeExternalApiSettings(payload: { is_enabled: boolean; regenerate_key?: boolean }) {
  const { data } = await apiClient.put<KnowledgeExternalApiSettings>('/knowledge/external-api', payload)
  return data
}

export async function downloadKnowledgeAttachment(entryId: number) {
  const { data } = await apiClient.get<Blob>(`/knowledge/${entryId}/attachment`, { responseType: 'blob' })
  return data
}

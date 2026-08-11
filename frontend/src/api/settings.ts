import { apiClient } from './client'
import type { XfyunAsrSettings, XfyunAsrSettingsUpdate } from '../types/settings'

export async function fetchXfyunAsrSettings() {
  const { data } = await apiClient.get<XfyunAsrSettings>('/settings/xfyun-asr')
  return data
}

export async function updateXfyunAsrSettings(payload: XfyunAsrSettingsUpdate) {
  const { data } = await apiClient.put<XfyunAsrSettings>('/settings/xfyun-asr', payload)
  return data
}

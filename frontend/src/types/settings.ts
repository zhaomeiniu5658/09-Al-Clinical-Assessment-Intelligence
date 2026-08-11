export interface XfyunAsrSettings {
  model_name: string
  app_id: string
  web_api: string
  hotwords: string | null
  api_secret_configured: boolean
  api_key_configured: boolean
  updated_at: string | null
}

export interface XfyunAsrSettingsUpdate {
  model_name: string
  app_id: string
  api_secret?: string
  api_key?: string
  web_api: string
  hotwords?: string
}

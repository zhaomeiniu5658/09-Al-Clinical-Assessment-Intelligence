export type ScaleType = 'HAMD' | 'HAMA' | 'PHQ-9'
export type TaskStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
export type TaskStage = 'ASR' | 'QC'
export type ReviewStatus = 'UNREVIEWED' | 'REVIEWED'

export interface QcResult {
  id: number
  doctor_score: number | null
  ai_score: number | null
  scoring_basis: string | null
  evidence_analysis: string | null
  error_reason: string | null
  optimization_suggestion: string | null
  item_results: QcItemResult[] | null
}

export interface QcItemResult {
  hamd_item: string
  doctor_score: number | null
  ai_score: number | null
  ai_scoring_basis: string | null
  difference?: number | null
  review_score?: number | null
  review_opinion?: string | null
}

export interface ReviewRecord {
  id: number
  reviewed_score: number
  review_reason: string
  review_comment: string | null
  reviewed_at: string
}

export interface TaskListItem {
  id: number
  scale_type: ScaleType
  audio_original_name: string
  audio_mime_type: string | null
  audio_size: number
  status: TaskStatus
  stage: TaskStage | null
  review_status: ReviewStatus
  error_message: string | null
  asr_text: string | null
  doctor_score: number | null
  ai_score: number | null
  created_at: string
  updated_at: string
}

export interface TaskDetail extends TaskListItem {
  qc_result: QcResult | null
  review_record: ReviewRecord | null
}

export interface TaskListResponse {
  items: TaskListItem[]
  total: number
  page: number
  page_size: number
}

import { apiClient } from './client'
import type { ScaleType, TaskStage, TaskStatus, ReviewStatus } from '../types/task'

export interface DashboardRecentTask {
  id: number
  scale_type: ScaleType
  audio_original_name: string
  status: TaskStatus
  stage: TaskStage | null
  review_status: ReviewStatus
  ai_score: number | null
  created_at: string
}

export interface DashboardOverview {
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  reviewed_tasks: number
  recent_tasks: DashboardRecentTask[]
}

export async function fetchDashboardOverview() {
  const { data } = await apiClient.get<DashboardOverview>('/dashboard/overview')
  return data
}

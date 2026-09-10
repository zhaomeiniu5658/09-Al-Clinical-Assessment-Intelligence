import { apiClient } from './client'
import type { ScaleType, TaskDetail, TaskListResponse } from '../types/task'

export async function fetchTasks(page = 1, pageSize = 10) {
  const { data } = await apiClient.get<TaskListResponse>('/tasks', {
    params: { page, page_size: pageSize }
  })
  return data
}

export async function fetchTask(taskId: number) {
  const { data } = await apiClient.get<TaskDetail>(`/tasks/${taskId}`)
  return data
}

export async function createTask(scaleType: ScaleType, audioFile: File, doctorTestFile: File) {
  const form = new FormData()
  form.append('scale_type', scaleType)
  form.append('audio_file', audioFile)
  form.append('doctor_test_file', doctorTestFile)
  const { data } = await apiClient.post<TaskDetail>('/tasks', form)
  return data
}

export async function retryTask(taskId: number) {
  const { data } = await apiClient.post<TaskDetail>(`/tasks/${taskId}/retry`)
  return data
}

export async function reviewTask(taskId: number, payload: {
  reviewed_score: number
  review_reason: string
  review_comment?: string
}) {
  const { data } = await apiClient.post<TaskDetail>(`/tasks/${taskId}/review`, payload)
  return data
}


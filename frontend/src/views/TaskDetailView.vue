<template>
  <AppShell title="任务详情" :subtitle="task ? `任务编号 ${formatTaskCode(task)}` : '查看临床评估任务的质控结果'">
    <div class="detail-page">
      <RouterLink class="back-link" to="/"><el-icon><ArrowLeft /></el-icon>返回任务列表</RouterLink>

      <el-skeleton v-if="loading" :rows="12" animated />
      <el-result v-else-if="loadError" icon="error" title="任务详情加载失败" sub-title="请返回列表后重试" />

      <template v-else-if="task">
        <section class="summary-grid">
          <article class="overview-card detail-card">
            <div class="section-heading"><el-icon><DocumentChecked /></el-icon><h2>任务概览</h2></div>
            <div class="overview-items">
              <div><span>任务编号</span><strong>{{ formatTaskCode(task) }}</strong></div>
              <div><span>量表类型</span><strong>{{ task.scale_type }}</strong></div>
              <div><span>原始音频</span><strong class="file-name">{{ task.audio_original_name }}</strong></div>
              <div><span>创建时间</span><strong>{{ formatTime(task.created_at) }}</strong></div>
              <div><span>任务状态</span><b class="status-badge" :class="statusClass(task.status)">{{ taskStatusText(task.status, task.stage) }}</b></div>
              <div><span>审核状态</span><b class="review-badge" :class="task.review_status === 'REVIEWED' ? 'reviewed' : 'unreviewed'">{{ task.review_status === 'REVIEWED' ? '已审核' : '待审核' }}</b></div>
            </div>
          </article>

          <article class="score-card detail-card">
            <span class="eyebrow">AI 质控得分</span>
            <div class="score-number">{{ formatScore(task.ai_score) }}</div>
            <span v-if="task.ai_score !== null" class="score-badge" :class="scoreClass(task.ai_score)">{{ scoreText(task.ai_score) }}</span>
            <span v-else class="score-muted">等待质控结果</span>
            <div class="score-split"><div><span>医生评分</span><b>{{ formatScore(task.doctor_score) }}</b></div><div><span>AI评分</span><b>{{ formatScore(task.ai_score) }}</b></div></div>
          </article>
        </section>

        <section class="detail-card audio-card">
          <div class="section-heading"><el-icon><Headset /></el-icon><h2>录音分析</h2><span class="section-caption">{{ formatBytes(task.audio_size) }}</span></div>
          <div class="audio-content">
            <div class="audio-file"><span class="audio-icon"><el-icon><Microphone /></el-icon></span><div><strong>{{ task.audio_original_name }}</strong><span>{{ task.audio_mime_type || '音频文件' }}</span></div></div>
            <audio v-if="audioUrl" :src="audioUrl" controls></audio>
            <span v-else class="audio-unavailable">音频加载后可播放</span>
          </div>
        </section>

        <section class="detail-card result-card">
          <div class="section-heading"><el-icon><DataAnalysis /></el-icon><h2>AI 质控分析</h2></div>
          <div v-if="task.qc_result" class="result-grid">
            <article><h3>评分依据</h3><p>{{ task.qc_result.scoring_basis || '暂无评分依据' }}</p></article>
            <article><h3>证据分析</h3><p>{{ task.qc_result.evidence_analysis || '暂无证据分析' }}</p></article>
            <article><h3>错误原因</h3><p>{{ task.qc_result.error_reason || '暂无错误原因' }}</p></article>
            <article><h3>优化建议</h3><p>{{ task.qc_result.optimization_suggestion || '暂无优化建议' }}</p></article>
          </div>
          <el-empty v-else description="任务完成后将在这里展示 AI 质控分析" :image-size="78" />
        </section>

        <section class="detail-card review-card">
          <div class="section-heading"><el-icon><Checked /></el-icon><h2>人工审核</h2><span v-if="task.review_status === 'REVIEWED'" class="review-badge reviewed">已审核</span></div>
          <template v-if="task.review_status === 'REVIEWED' && task.review_record">
            <div class="review-record"><div><span>复核评分</span><b>{{ task.review_record.reviewed_score }}</b></div><div><span>复核时间</span><b>{{ formatTime(task.review_record.reviewed_at) }}</b></div><div><span>复核原因</span><p>{{ task.review_record.review_reason }}</p></div><div><span>审核意见</span><p>{{ task.review_record.review_comment || '未填写' }}</p></div></div>
          </template>
          <template v-else>
            <el-alert v-if="!task.qc_result" title="AI 质控完成后可进行人工审核" type="info" :closable="false" show-icon />
            <el-form v-else ref="reviewFormRef" class="review-form" :model="reviewForm" :rules="reviewRules" label-position="top">
              <el-form-item label="人工复核评分" prop="reviewed_score"><el-input-number v-model="reviewForm.reviewed_score" :min="0" :max="100" :precision="1" /></el-form-item>
              <el-form-item label="复核原因" prop="review_reason"><el-input v-model="reviewForm.review_reason" type="textarea" :rows="3" placeholder="请填写复核原因" /></el-form-item>
              <el-form-item label="审核意见"><el-input v-model="reviewForm.review_comment" type="textarea" :rows="3" placeholder="可选填写" /></el-form-item>
              <div class="review-actions"><el-button type="primary" :loading="reviewing" @click="submitReview">提交审核</el-button></div>
            </el-form>
          </template>
        </section>
      </template>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { ArrowLeft, Checked, DataAnalysis, DocumentChecked, Headset, Microphone } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '../api/client'
import { fetchTask, reviewTask } from '../api/tasks'
import AppShell from '../components/AppShell.vue'
import type { TaskDetail, TaskStage, TaskStatus } from '../types/task'

const route = useRoute()
const task = ref<TaskDetail | null>(null)
const loading = ref(true)
const loadError = ref(false)
const reviewing = ref(false)
const audioUrl = ref('')
const reviewFormRef = ref<FormInstance>()
const reviewForm = reactive({ reviewed_score: 0, review_reason: '', review_comment: '' })
const reviewRules: FormRules = { reviewed_score: [{ required: true, message: '请输入人工复核评分', trigger: 'blur' }], review_reason: [{ required: true, message: '请填写复核原因', trigger: 'blur' }] }

async function loadTask() {
  loading.value = true
  loadError.value = false
  try {
    const taskId = Number(route.params.id)
    if (!Number.isInteger(taskId) || taskId < 1) throw new Error('Invalid task id')
    task.value = await fetchTask(taskId)
    reviewForm.reviewed_score = task.value.review_record?.reviewed_score ?? task.value.qc_result?.ai_score ?? 0
    reviewForm.review_reason = task.value.review_record?.review_reason ?? ''
    reviewForm.review_comment = task.value.review_record?.review_comment ?? ''
    loadAudio(taskId)
  } catch { loadError.value = true }
  finally { loading.value = false }
}
async function loadAudio(taskId: number) {
  try { const response = await apiClient.get(`/tasks/${taskId}/audio`, { responseType: 'blob' }); audioUrl.value = URL.createObjectURL(response.data) } catch { audioUrl.value = '' }
}
async function submitReview() {
  if (!task.value) return
  await reviewFormRef.value?.validate()
  reviewing.value = true
  try {
    task.value = await reviewTask(task.value.id, { reviewed_score: reviewForm.reviewed_score, review_reason: reviewForm.review_reason, review_comment: reviewForm.review_comment || undefined })
    ElMessage.success('审核已提交')
  } finally { reviewing.value = false }
}
function taskStatusText(status: TaskStatus, stage: TaskStage | null) { if (status === 'RUNNING' && stage === 'ASR') return '转录中'; if (status === 'RUNNING' && stage === 'QC') return '质控中'; return { PENDING: '待处理', RUNNING: '处理中', COMPLETED: '已完成', FAILED: '异常' }[status] }
function statusClass(status: TaskStatus) { return { PENDING: 'pending', RUNNING: 'processing', COMPLETED: 'success', FAILED: 'danger' }[status] }
function scoreClass(score: number) { return score >= 90 ? 'excellent' : score >= 75 ? 'good' : score >= 60 ? 'average' : 'poor' }
function scoreText(score: number) { return score >= 90 ? '优秀' : score >= 75 ? '良好' : score >= 60 ? '一般' : '较差' }
function formatTaskCode(value: TaskDetail) { return `QC${new Date(value.created_at).toISOString().slice(0, 10).replace(/-/g, '')}${String(value.id).padStart(3, '0')}` }
function formatScore(score: number | null) { return score === null || score === undefined ? '-' : String(score) }
function formatTime(value: string) { return new Date(value).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-') }
function formatBytes(size: number) { if (size < 1024) return `${size} B`; if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`; return `${(size / 1024 / 1024).toFixed(1)} MB` }
onMounted(loadTask)
onBeforeUnmount(() => { if (audioUrl.value) URL.revokeObjectURL(audioUrl.value) })
</script>

<style scoped>
.detail-page { max-width: 1240px; margin: 0 auto; }.back-link { display: inline-flex; align-items: center; gap: 7px; margin: 3px 0 18px; color: #64748b; font-size: 14px; text-decoration: none; }.back-link:hover { color: #5b5ce2; }.detail-card { border: 1px solid #e8ebf2; border-radius: 8px; background: #fff; box-shadow: 0 3px 13px rgba(15, 23, 42, .035); }.summary-grid { display: grid; grid-template-columns: minmax(0, 1fr) 290px; gap: 18px; }.overview-card { padding: 24px 26px; }.score-card { display: flex; align-items: center; flex-direction: column; justify-content: center; padding: 22px; text-align: center; }.section-heading { display: flex; align-items: center; gap: 8px; color: #46546a; }.section-heading :deep(.el-icon) { color: #6366f1; font-size: 19px; }.section-heading h2 { margin: 0; color: #374151; font-size: 16px; }.section-caption { margin-left: auto; color: #9aa4b4; font-size: 12px; }.overview-items { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 25px 20px; margin-top: 24px; }.overview-items span, .score-split span, .review-record span { display: block; color: #98a1b1; font-size: 12px; }.overview-items strong { display: block; margin-top: 7px; overflow: hidden; color: #374151; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }.overview-items b { display: inline-flex; margin-top: 7px; }.eyebrow { color: #7c8798; font-size: 12px; }.score-number { margin: 6px 0 8px; color: #5b5ce2; font-size: 48px; font-weight: 700; line-height: 1; }.score-muted { color: #9ca3af; font-size: 12px; }.score-split { display: flex; width: 100%; justify-content: space-around; gap: 18px; margin-top: 17px; padding-top: 15px; border-top: 1px solid #eef1f5; }.score-split b { display: block; margin-top: 4px; color: #374151; font-size: 17px; }.audio-card, .result-card, .review-card { margin-top: 18px; padding: 23px 26px; }.audio-content { display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-top: 18px; padding: 14px 16px; border: 1px solid #edf0f5; border-radius: 8px; background: #fafbff; }.audio-file { display: flex; min-width: 0; align-items: center; gap: 12px; }.audio-icon { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 8px; background: #eef0ff; color: #6366f1; }.audio-file strong, .audio-file span { display: block; }.audio-file strong { overflow: hidden; max-width: 430px; color: #374151; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }.audio-file div > span { margin-top: 4px; color: #8b95a5; font-size: 12px; }.audio-content audio { width: min(360px, 42%); height: 34px; }.audio-unavailable { color: #98a1b1; font-size: 13px; white-space: nowrap; }.result-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 18px; }.result-grid article { min-height: 126px; padding: 16px; border: 1px solid #edf0f5; border-radius: 8px; background: #fafbff; }.result-grid h3 { margin: 0 0 9px; color: #4c5b72; font-size: 14px; }.result-grid p { margin: 0; color: #68758b; font-size: 13px; line-height: 1.75; white-space: pre-wrap; }.review-form { max-width: 680px; margin-top: 18px; }.review-form :deep(.el-form-item__label) { color: #4c5b72; }.review-actions { display: flex; justify-content: flex-end; margin-top: 6px; }.review-record { display: grid; grid-template-columns: 180px 1fr; gap: 20px; margin-top: 20px; }.review-record > div { min-width: 0; padding: 14px 16px; border-radius: 8px; background: #fafbff; }.review-record b, .review-record p { display: block; margin: 7px 0 0; color: #46546a; font-size: 14px; line-height: 1.6; }.review-record > div:nth-child(n+3) { grid-column: span 1; }.status-badge, .review-badge, .score-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 56px; padding: 4px 9px; border-radius: 6px; font-size: 12px; font-weight: 500; }.status-badge.success, .review-badge.reviewed { background: #ecfdf5; color: #10b981; }.status-badge.processing { background: #eff6ff; color: #3b82f6; }.status-badge.pending, .review-badge.unreviewed { background: #fffbeb; color: #d97706; }.status-badge.danger { background: #fef2f2; color: #dc2626; }.score-badge.excellent { background: #ecfdf5; color: #10b981; }.score-badge.good { background: #eff6ff; color: #3b82f6; }.score-badge.average { background: #fffbeb; color: #f59e0b; }.score-badge.poor { background: #fef2f2; color: #ef4444; }
@media (max-width: 860px) { .summary-grid { grid-template-columns: 1fr; }.overview-items { grid-template-columns: repeat(2, minmax(0, 1fr)); }.audio-content { align-items: flex-start; flex-direction: column; }.audio-content audio { width: 100%; }.review-record { grid-template-columns: 1fr 1fr; } }
@media (max-width: 580px) { .overview-card, .audio-card, .result-card, .review-card { padding: 18px; }.overview-items, .result-grid, .review-record { grid-template-columns: 1fr; }.review-record > div:nth-child(n+3) { grid-column: auto; }.audio-file strong { max-width: 210px; } }
</style>

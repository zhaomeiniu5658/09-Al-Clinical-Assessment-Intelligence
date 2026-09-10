<template>
  <AppShell title="质控任务列表" subtitle="对临床评估任务进行智能质控与管理">
    <section class="filter-panel" aria-label="任务筛选">
      <el-form class="filter-form" label-position="top" @submit.prevent="applyFilters">
        <el-form-item label="任务编号">
          <el-input v-model="filters.taskCode" placeholder="请输入任务编号" clearable :prefix-icon="Search" />
        </el-form-item>
        <el-form-item label="量表类型">
          <el-select v-model="filters.scaleType" placeholder="请选择量表类型" clearable>
            <el-option label="HAMD" value="HAMD" />
            <el-option label="HAMA" value="HAMA" />
            <el-option label="PHQ-9" value="PHQ-9" />
          </el-select>
        </el-form-item>
        <el-form-item label="任务状态">
          <el-select v-model="filters.status" placeholder="请选择状态" clearable>
            <el-option label="待处理" value="PENDING" />
            <el-option label="处理中" value="RUNNING" />
            <el-option label="已完成" value="COMPLETED" />
            <el-option label="异常" value="FAILED" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交时间" class="date-filter">
          <el-date-picker v-model="filters.dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" range-separator="至" value-format="YYYY-MM-DD" />
        </el-form-item>
        <div class="filter-actions">
          <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          <el-button type="primary" :icon="Search" native-type="submit">查询</el-button>
        </div>
      </el-form>
    </section>

    <section class="list-panel">
      <div class="list-toolbar">
        <div><strong>共 {{ total }} 条数据</strong><span>任务处理状态将自动更新</span></div>
        <div class="list-toolbar-actions">
          <el-button :icon="Refresh" :loading="loading" @click="loadTasks">刷新</el-button>
          <el-button type="primary" :icon="Plus" @click="uploadDialogVisible = true">新建质控任务</el-button>
        </div>
      </div>

      <el-table v-loading="loading" class="task-table" :data="filteredTasks" row-key="id" empty-text="暂无任务数据">
        <el-table-column label="任务编号" min-width="138">
          <template #default="{ row }"><span class="task-code">{{ formatTaskCode(row) }}</span></template>
        </el-table-column>
        <el-table-column prop="scale_type" label="量表类型" width="112">
          <template #default="{ row }"><span class="scale-label">{{ row.scale_type }}</span></template>
        </el-table-column>
        <el-table-column prop="audio_original_name" label="原始音频" min-width="180" show-overflow-tooltip />
        <el-table-column label="ASR 状态" width="112">
          <template #default="{ row }"><span class="status-badge" :class="asrStatusClass(row)">{{ asrStatusText(row) }}</span></template>
        </el-table-column>
        <el-table-column label="任务状态" width="112">
          <template #default="{ row }"><span class="status-badge" :class="statusClass(row.status)">{{ taskStatusText(row.status, row.stage) }}</span></template>
        </el-table-column>
        <el-table-column label="医生评分" width="92" align="center">
          <template #default="{ row }">{{ formatScore(row.doctor_score) }}</template>
        </el-table-column>
        <el-table-column label="AI评分" width="82" align="center">
          <template #default="{ row }">{{ formatScore(row.ai_score) }}</template>
        </el-table-column>
        <el-table-column label="AI质控得分" width="126">
          <template #default="{ row }"><span v-if="row.ai_score !== null" class="score-badge" :class="scoreClass(row.ai_score)">{{ row.ai_score }} {{ scoreText(row.ai_score) }}</span><span v-else>-</span></template>
        </el-table-column>
        <el-table-column label="审核状态" width="104">
          <template #default="{ row }"><span class="review-badge" :class="row.review_status === 'REVIEWED' ? 'reviewed' : 'unreviewed'">{{ row.review_status === 'REVIEWED' ? '已审核' : '待审核' }}</span></template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }"><span class="time-value">{{ formatTime(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="166" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button link type="primary" @click="openDetail(row.id)">详情</el-button>
              <el-button link type="primary" :disabled="row.ai_score === null" @click="openReview(row.id)">审核</el-button>
              <el-dropdown trigger="click">
                <el-button link class="more-button" aria-label="更多操作"><el-icon><MoreFilled /></el-icon></el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :icon="Document" @click="openTranscript(row.id)">转录文本</el-dropdown-item>
                    <el-dropdown-item :icon="DataAnalysis" @click="openAiScore(row.id)">AI评分</el-dropdown-item>
                    <el-dropdown-item v-if="row.status === 'FAILED'" :icon="RefreshRight" @click="handleRetry(row.id)">重新尝试</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <span>共 {{ total }} 条</span>
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="sizes, prev, pager, next" :page-sizes="[10, 20, 50]" @change="loadTasks" />
      </div>
    </section>

    <el-dialog v-model="uploadDialogVisible" title="新建质控任务" width="520px" @closed="resetUpload">
      <div class="generated-task-note"><div class="generated-task-label">任务 ID</div><div class="generated-task-value">提交后由系统自动生成<span>自动生成</span></div></div>
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-position="top">
        <el-form-item label="量表类型" prop="scale_type">
          <el-select v-model="uploadForm.scale_type" placeholder="请选择量表类型" class="full-width">
            <el-option label="HAMD" value="HAMD" /><el-option label="HAMA" value="HAMA" /><el-option label="PHQ-9" value="PHQ-9" />
          </el-select>
        </el-form-item>
        <el-form-item label="医患对话音频" prop="audio_file">
          <el-upload drag :auto-upload="false" :limit="1" :on-change="handleAudioChange" :on-remove="handleAudioRemove" accept=".mp3,.wav,.flac,.opus,.m4a,audio/mpeg,audio/wav,audio/flac,audio/ogg">
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="el-upload__text">点击或拖拽音频到此处</div>
            <template #tip><div class="el-upload__tip">讯飞语音转写支持 wav、flac、opus、m4a、mp3；请上传音频文件，不支持 MP4 视频。</div></template>
          </el-upload>
        </el-form-item>
        <el-form-item label="医生打分表" prop="doctor_test_file">
          <el-upload drag :auto-upload="false" :limit="1" :on-change="handleDoctorTestChange" :on-remove="handleDoctorTestRemove" accept=".xls,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
            <el-icon class="upload-icon"><Document /></el-icon>
            <div class="el-upload__text">点击或拖拽 Excel 打分表到此处</div>
            <template #tip><div class="el-upload__tip">请上传医生填写的 Excel 打分表，仅支持 .xls 或 .xlsx 格式。</div></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="uploadDialogVisible = false">取消</el-button><el-button type="primary" :loading="uploading" @click="submitUpload">提交解析</el-button></template>
    </el-dialog>

    <el-dialog v-model="transcriptDialogVisible" title="转录文本" width="760px"><el-input :model-value="formatTranscript(selectedTask?.asr_text || '暂无转录文本')" type="textarea" :rows="16" readonly /></el-dialog>

    <el-dialog v-model="aiDialogVisible" title="AI 质控分析" width="800px">
      <template v-if="selectedTask?.qc_result">
        <div class="dialog-score-row"><span>医生评分 <b>{{ formatScore(selectedTask.qc_result.doctor_score) }}</b></span><span>AI评分 <b>{{ formatScore(selectedTask.qc_result.ai_score) }}</b></span></div>
        <div class="analysis-grid"><section><h3>评分依据</h3><p>{{ selectedTask.qc_result.scoring_basis || '暂无' }}</p></section><section><h3>证据分析</h3><p>{{ selectedTask.qc_result.evidence_analysis || '暂无' }}</p></section><section><h3>错误原因</h3><p>{{ selectedTask.qc_result.error_reason || '暂无' }}</p></section><section><h3>优化建议</h3><p>{{ selectedTask.qc_result.optimization_suggestion || '暂无' }}</p></section></div>
      </template>
      <el-empty v-else description="暂无 AI 质控结果" />
    </el-dialog>

    <el-dialog v-model="reviewDialogVisible" title="人工审核" width="860px">
      <template v-if="selectedTask">
        <div class="review-layout">
          <section class="transcript-preview"><span>转录文本</span><p>{{ formatTranscript(selectedTask.asr_text || '暂无转录文本') }}</p></section>
          <el-form ref="reviewFormRef" :model="reviewForm" :rules="reviewRules" label-position="top">
            <el-form-item label="人工复核评分" prop="reviewed_score"><el-input-number v-model="reviewForm.reviewed_score" :min="0" :max="100" :precision="1" class="full-width" /></el-form-item>
            <el-form-item label="复核原因" prop="review_reason"><el-input v-model="reviewForm.review_reason" type="textarea" :rows="4" /></el-form-item>
            <el-form-item label="审核意见"><el-input v-model="reviewForm.review_comment" type="textarea" :rows="3" /></el-form-item>
          </el-form>
        </div>
      </template>
      <template #footer><el-button @click="reviewDialogVisible = false">取消</el-button><el-button type="primary" :loading="reviewing" @click="submitReview">提交审核</el-button></template>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { DataAnalysis, Document, MoreFilled, Plus, Refresh, RefreshLeft, RefreshRight, Search, UploadFilled } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import { ElMessage, ElNotification } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createTask, fetchTask, fetchTasks, retryTask, reviewTask } from '../api/tasks'
import AppShell from '../components/AppShell.vue'
import type { ScaleType, TaskDetail, TaskListItem, TaskStage, TaskStatus } from '../types/task'

const router = useRouter()
const loading = ref(false)
const uploading = ref(false)
const reviewing = ref(false)
const tasks = ref<TaskListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const selectedTask = ref<TaskDetail | null>(null)
const uploadDialogVisible = ref(false)
const transcriptDialogVisible = ref(false)
const aiDialogVisible = ref(false)
const reviewDialogVisible = ref(false)
const uploadFormRef = ref<FormInstance>()
const reviewFormRef = ref<FormInstance>()
let timer: number | undefined
const taskStates = new Map<number, TaskStatus>()

const filters = reactive<{ taskCode: string; scaleType: ScaleType | ''; status: TaskStatus | ''; dateRange: string[] }>({ taskCode: '', scaleType: '', status: '', dateRange: [] })
const uploadForm = reactive<{ scale_type: ScaleType | ''; audio_file: File | null; doctor_test_file: File | null }>({ scale_type: '', audio_file: null, doctor_test_file: null })
const reviewForm = reactive({ reviewed_score: 0, review_reason: '', review_comment: '' })
const uploadRules: FormRules = { scale_type: [{ required: true, message: '请选择量表类型', trigger: 'change' }], audio_file: [{ required: true, message: '请上传音频文件', trigger: 'change' }], doctor_test_file: [{ required: true, message: '请上传医生打分表', trigger: 'change' }] }
const reviewRules: FormRules = { reviewed_score: [{ required: true, message: '请输入人工复核评分', trigger: 'blur' }], review_reason: [{ required: true, message: '请填写复核原因', trigger: 'blur' }] }
const hasRunningTasks = computed(() => tasks.value.some((item) => item.status === 'PENDING' || item.status === 'RUNNING'))
const filteredTasks = computed(() => tasks.value.filter((item) => {
  const taskCode = formatTaskCode(item).toLowerCase()
  const created = item.created_at.slice(0, 10)
  const [start, end] = filters.dateRange
  return (!filters.taskCode || taskCode.includes(filters.taskCode.toLowerCase()) || String(item.id).includes(filters.taskCode)) && (!filters.scaleType || item.scale_type === filters.scaleType) && (!filters.status || item.status === filters.status) && (!start || created >= start) && (!end || created <= end)
}))

async function loadTasks() {
  loading.value = true
  try {
    const data = await fetchTasks(page.value, pageSize.value)
    data.items.forEach((item) => {
      const previousStatus = taskStates.get(item.id)
      if ((previousStatus === 'PENDING' || previousStatus === 'RUNNING') && item.status === 'COMPLETED') {
        ElNotification({ title: '转录与 AI 质控完成', message: `任务 ${formatTaskCode(item)} 已完成，请在质控列表中查看分析结果。`, type: 'success', duration: 5000 })
      }
      if ((previousStatus === 'PENDING' || previousStatus === 'RUNNING') && item.status === 'FAILED') {
        ElNotification({ title: '任务分析异常', message: `任务 ${formatTaskCode(item)} 分析失败，请在质控列表中查看详情。`, type: 'error', duration: 6000 })
      }
      taskStates.set(item.id, item.status)
    })
    tasks.value = data.items
    total.value = data.total
  }
  catch (error) { throw error }
  finally { loading.value = false }
}
async function loadSelected(taskId: number) { selectedTask.value = await fetchTask(taskId) }
function openDetail(taskId: number) { router.push({ name: 'task-detail', params: { id: taskId } }) }
async function openTranscript(taskId: number) { await loadSelected(taskId); transcriptDialogVisible.value = true }
async function openAiScore(taskId: number) { await loadSelected(taskId); aiDialogVisible.value = true }
async function openReview(taskId: number) {
  await loadSelected(taskId)
  if (!selectedTask.value?.qc_result) { ElMessage.warning('AI 质控完成后才能审核'); return }
  reviewForm.reviewed_score = selectedTask.value.review_record?.reviewed_score ?? selectedTask.value.qc_result.ai_score ?? 0
  reviewForm.review_reason = selectedTask.value.review_record?.review_reason ?? ''
  reviewForm.review_comment = selectedTask.value.review_record?.review_comment ?? ''
  reviewDialogVisible.value = true
}
function applyFilters() { page.value = 1 }
function resetFilters() { filters.taskCode = ''; filters.scaleType = ''; filters.status = ''; filters.dateRange = []; page.value = 1 }
function handleAudioChange(file: UploadFile) { uploadForm.audio_file = file.raw || null }
function handleAudioRemove() { uploadForm.audio_file = null }
function handleDoctorTestChange(file: UploadFile) {
  const raw = file.raw || null
  if (raw && !['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'].includes(raw.type) && !/\.(xls|xlsx)$/i.test(raw.name)) {
    ElMessage.error('医生打分表仅支持 .xls 或 .xlsx 格式')
    uploadForm.doctor_test_file = null
    return
  }
  uploadForm.doctor_test_file = raw
}
function handleDoctorTestRemove() { uploadForm.doctor_test_file = null }
function resetUpload() { uploadForm.scale_type = ''; uploadForm.audio_file = null; uploadForm.doctor_test_file = null; uploadFormRef.value?.resetFields() }
async function submitUpload() {
  await uploadFormRef.value?.validate()
  if (!uploadForm.scale_type || !uploadForm.audio_file || !uploadForm.doctor_test_file) return
  uploading.value = true
  try {
    const createdTask = await createTask(uploadForm.scale_type, uploadForm.audio_file, uploadForm.doctor_test_file)
    taskStates.set(createdTask.id, createdTask.status)
    ElNotification({ title: '任务已创建', message: `任务 ${formatTaskCode(createdTask)} 已进入讯飞语音转录分析，请稍后在质控列表查看结果。`, type: 'info', duration: 6000 })
    uploadDialogVisible.value = false
    await loadTasks()
  } finally { uploading.value = false }
}
async function handleRetry(taskId: number) { await retryTask(taskId); ElMessage.success('已重新投递任务'); await loadTasks() }
async function submitReview() { if (!selectedTask.value) return; await reviewFormRef.value?.validate(); reviewing.value = true; try { await reviewTask(selectedTask.value.id, { reviewed_score: reviewForm.reviewed_score, review_reason: reviewForm.review_reason, review_comment: reviewForm.review_comment || undefined }); ElMessage.success('审核已提交'); reviewDialogVisible.value = false; await loadTasks() } finally { reviewing.value = false } }
function asrStatusText(row: TaskListItem) { if (row.status === 'FAILED' && row.stage === 'ASR') return '识别失败'; if (row.status === 'RUNNING' && row.stage === 'ASR') return '识别中'; if (row.status === 'PENDING') return '等待中'; return row.asr_text ? '已转录' : '待处理' }
function taskStatusText(status: TaskStatus, stage: TaskStage | null) { if (status === 'RUNNING' && stage === 'ASR') return '转录中'; if (status === 'RUNNING' && stage === 'QC') return '质控中'; return { PENDING: '待处理', RUNNING: '处理中', COMPLETED: '已完成', FAILED: '异常' }[status] }
function asrStatusClass(row: TaskListItem) { return row.status === 'FAILED' && row.stage === 'ASR' ? 'danger' : row.status === 'RUNNING' && row.stage === 'ASR' ? 'processing' : row.asr_text ? 'success' : 'pending' }
function statusClass(status: TaskStatus) { return { PENDING: 'pending', RUNNING: 'processing', COMPLETED: 'success', FAILED: 'danger' }[status] }
function scoreClass(score: number) { return score >= 90 ? 'excellent' : score >= 75 ? 'good' : score >= 60 ? 'average' : 'poor' }
function scoreText(score: number) { return score >= 90 ? '优秀' : score >= 75 ? '良好' : score >= 60 ? '一般' : '较差' }
function formatTaskCode(row: TaskListItem) { return `QC${new Date(row.created_at).toISOString().slice(0, 10).replace(/-/g, '')}${String(row.id).padStart(3, '0')}` }
function formatScore(score: number | null) { return score === null || score === undefined ? '-' : String(score) }
function formatTime(value: string) { return new Date(value).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-') }
function formatTranscript(text: string): string {
  if (!text) return text
  return text
    .replace(/([。！？；])\s*/g, '$1\n')
    .replace(/\n{2,}/g, '\n')
    .trim()
}
onMounted(async () => { await loadTasks(); timer = window.setInterval(() => { if (hasRunningTasks.value) loadTasks() }, 5000) })
onBeforeUnmount(() => { if (timer) window.clearInterval(timer) })
</script>

<style scoped>
.filter-panel, .list-panel { min-width: 0; border: 1px solid #eff1f6; border-radius: 8px; background: #fff; box-shadow: 0 4px 16px rgba(15, 23, 42, .035); }
.filter-panel { padding: 22px 30px; }
.filter-form { display: grid; min-width: 0; grid-template-columns: repeat(3, minmax(0, 1fr)); column-gap: 32px; align-items: end; }
.filter-form :deep(.el-form-item) { min-width: 0; margin-bottom: 0; }.filter-form :deep(.el-form-item__label) { padding-bottom: 8px; color: #374151; font-size: 14px; }.filter-form :deep(.el-date-editor) { width: 100%; min-width: 0; }.date-filter { grid-column: span 2; }.filter-actions { display: flex; justify-content: flex-end; gap: 10px; padding-bottom: 0; }
.list-panel { margin-top: 24px; overflow: hidden; }.list-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 22px 22px 18px; }.list-toolbar strong { color: #374151; font-size: 15px; }.list-toolbar span { margin-left: 12px; color: #9ca3af; font-size: 12px; }.list-toolbar-actions { display: flex; gap: 10px; }
.task-table { width: 100%; }.task-table :deep(.el-table__header-wrapper th.el-table__cell) { height: 48px; background: #fafbff; color: #64748b; font-size: 13px; font-weight: 500; }.task-table :deep(.el-table__cell) { border-bottom-color: #f1f5f9; }.task-table :deep(.el-table__row td.el-table__cell) { height: 58px; color: #4b5563; font-size: 14px; }.task-table :deep(.el-table__row:hover > td.el-table__cell) { background: #f8faff; }.task-code { color: #1f2937; font-weight: 600; }.scale-label { color: #55647b; font-weight: 500; }.time-value { color: #64748b; white-space: nowrap; }
.status-badge, .review-badge, .score-badge { display: inline-flex; align-items: center; justify-content: center; min-width: 56px; padding: 4px 9px; border-radius: 6px; font-size: 12px; font-weight: 500; white-space: nowrap; }.status-badge.success, .review-badge.reviewed { background: #ecfdf5; color: #10b981; }.status-badge.processing { background: #eff6ff; color: #3b82f6; }.status-badge.pending, .review-badge.unreviewed { background: #fffbeb; color: #d97706; }.status-badge.danger { background: #fef2f2; color: #dc2626; }.score-badge.excellent { background: #ecfdf5; color: #10b981; }.score-badge.good { background: #eff6ff; color: #3b82f6; }.score-badge.average { background: #fffbeb; color: #f59e0b; }.score-badge.poor { background: #fef2f2; color: #ef4444; }.row-actions { display: flex; align-items: center; gap: 4px; }.more-button { padding: 4px; color: #64748b; }
.pager { display: flex; align-items: center; justify-content: flex-end; gap: 20px; min-height: 72px; padding: 14px 22px; border-top: 1px solid #f1f5f9; color: #4b5563; font-size: 14px; }.pager :deep(.el-pager li.is-active) { background: #6366f1; color: #fff; }.pager :deep(.el-pager li), .pager :deep(.btn-prev), .pager :deep(.btn-next) { border: 1px solid #e5e7eb; border-radius: 7px; }
.upload-icon { color: #6366f1; font-size: 36px; }.dialog-score-row { display: flex; gap: 32px; padding: 14px 16px; border-radius: 8px; background: #f8faff; color: #64748b; font-size: 14px; }.dialog-score-row b { margin-left: 8px; color: #252f43; font-size: 18px; }.analysis-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }.analysis-grid section, .transcript-preview { min-height: 120px; padding: 15px; border: 1px solid #e8ebf2; border-radius: 8px; background: #fafbfc; }.analysis-grid h3, .analysis-grid p, .transcript-preview p { margin: 0; }.analysis-grid h3, .transcript-preview > span { display: block; margin-bottom: 8px; color: #374151; font-size: 14px; }.analysis-grid p, .transcript-preview p { color: #667085; font-size: 13px; line-height: 1.7; white-space: pre-wrap; }.review-layout { display: grid; grid-template-columns: minmax(0, 1fr) 310px; gap: 20px; }.transcript-preview { max-height: 360px; overflow: auto; }
.generated-task-note { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 21px; padding: 12px 14px; border: 1px solid #e6e9ff; border-radius: 8px; background: #f8f9ff; }.generated-task-label { color: #64748b; font-size: 13px; }.generated-task-value { color: #9ca3af; font-size: 13px; }.generated-task-value span { display: inline-flex; margin-left: 8px; padding: 3px 7px; border-radius: 5px; background: #eef0ff; color: #6366f1; font-size: 11px; }
@media (max-width: 1120px) { .filter-form { grid-template-columns: repeat(2, minmax(180px, 1fr)); }.date-filter { grid-column: auto; } }
@media (max-width: 720px) { .filter-panel { padding: 18px; }.filter-form { grid-template-columns: 1fr; gap: 12px; }.filter-actions { justify-content: flex-start; }.list-toolbar { align-items: flex-start; flex-direction: column; }.list-toolbar span { display: block; margin: 5px 0 0; }.pager { align-items: flex-end; flex-direction: column; }.analysis-grid, .review-layout { grid-template-columns: 1fr; } }
</style>

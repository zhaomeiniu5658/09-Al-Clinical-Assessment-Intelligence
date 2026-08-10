<template>
  <main class="workspace">
    <header class="topbar">
      <div>
        <h1>质控列表</h1>
        <p>上传医患对话音频，完成转录、AI评分与人工复核。</p>
      </div>
      <div class="topbar-actions">
        <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
        <el-button type="primary" :icon="Upload" @click="uploadDialogVisible = true">上传音频解析</el-button>
        <el-button :icon="SwitchButton" @click="logout">退出</el-button>
      </div>
    </header>

    <section class="table-panel">
      <el-table v-loading="loading" :data="tasks" row-key="id" height="calc(100vh - 220px)">
        <el-table-column prop="id" label="任务编号" width="100" />
        <el-table-column prop="scale_type" label="量表类型" width="120" />
        <el-table-column prop="audio_original_name" label="原始音频" min-width="190" show-overflow-tooltip />
        <el-table-column label="ASR状态" width="120">
          <template #default="{ row }">
            <el-tag :type="asrTagType(row)">{{ asrStatusText(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="AI质控状态" width="130">
          <template #default="{ row }">
            <el-tag :type="taskTagType(row.status)">{{ taskStatusText(row.status, row.stage) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.review_status === 'REVIEWED' ? 'success' : 'info'">
              {{ row.review_status === 'REVIEWED' ? '已审核' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="医生评分" width="110">
          <template #default="{ row }">{{ formatScore(row.doctor_score) }}</template>
        </el-table-column>
        <el-table-column label="AI评分" width="100">
          <template #default="{ row }">{{ formatScore(row.ai_score) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="View" @click="openDetail(row.id)">查看</el-button>
            <el-button link :icon="Document" @click="openTranscript(row.id)">转录文本</el-button>
            <el-button link :icon="EditPen" @click="openDoctorScore(row.id)">医生评分</el-button>
            <el-button link :icon="DataAnalysis" @click="openAiScore(row.id)">AI评分</el-button>
            <el-button link type="success" :icon="Checked" @click="openReview(row.id)">审核</el-button>
            <el-button v-if="row.status === 'FAILED'" link type="danger" :icon="RefreshRight" @click="handleRetry(row.id)">
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next, sizes"
          :page-sizes="[10, 20, 50]"
          @change="loadTasks"
        />
      </div>
    </section>

    <el-dialog v-model="uploadDialogVisible" title="上传音频解析" width="520px" @closed="resetUpload">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-position="top">
        <el-form-item label="量表类型" prop="scale_type">
          <el-select v-model="uploadForm.scale_type" placeholder="请选择量表类型" class="full-width">
            <el-option label="HAMD" value="HAMD" />
            <el-option label="HAMA" value="HAMA" />
            <el-option label="PHQ-9" value="PHQ-9" />
          </el-select>
        </el-form-item>
        <el-form-item label="医患对话音频" prop="audio_file">
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleAudioChange"
            :on-remove="handleAudioRemove"
            accept=".mp3,.wav,.m4a,.aac,.flac,.ogg,.webm,.amr,audio/*"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="el-upload__text">点击或拖拽音频到此处</div>
            <template #tip>
              <div class="el-upload__tip">支持 mp3、wav、m4a、aac、flac、ogg、webm、amr</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">提交解析</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="任务详情" width="760px">
      <el-descriptions v-if="selectedTask" :column="2" border>
        <el-descriptions-item label="任务编号">{{ selectedTask.id }}</el-descriptions-item>
        <el-descriptions-item label="量表类型">{{ selectedTask.scale_type }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ selectedTask.audio_original_name }}</el-descriptions-item>
        <el-descriptions-item label="文件大小">{{ formatBytes(selectedTask.audio_size) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ taskStatusText(selectedTask.status, selectedTask.stage) }}</el-descriptions-item>
        <el-descriptions-item label="审核">{{ selectedTask.review_status === 'REVIEWED' ? '已审核' : '待审核' }}</el-descriptions-item>
      </el-descriptions>
      <el-alert v-if="selectedTask?.error_message" class="dialog-gap" type="error" :title="selectedTask.error_message" show-icon />
    </el-dialog>

    <el-dialog v-model="transcriptDialogVisible" title="转录文本" width="760px">
      <el-input
        :model-value="selectedTask?.asr_text || '暂无转录文本'"
        type="textarea"
        :rows="16"
        readonly
      />
    </el-dialog>

    <el-dialog v-model="doctorDialogVisible" title="医生评分" width="520px">
      <el-descriptions v-if="selectedTask" :column="1" border>
        <el-descriptions-item label="量表类型">{{ selectedTask.scale_type }}</el-descriptions-item>
        <el-descriptions-item label="医生评分">{{ formatScore(selectedTask.qc_result?.doctor_score ?? null) }}</el-descriptions-item>
      </el-descriptions>
      <el-alert class="dialog-gap" type="info" title="医生评分由 AI 从转录文本中提炼。" show-icon />
    </el-dialog>

    <el-dialog v-model="aiDialogVisible" title="AI评分" width="800px">
      <template v-if="selectedTask?.qc_result">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="医生评分">{{ formatScore(selectedTask.qc_result.doctor_score) }}</el-descriptions-item>
          <el-descriptions-item label="AI评分">{{ formatScore(selectedTask.qc_result.ai_score) }}</el-descriptions-item>
        </el-descriptions>
        <div class="analysis-grid">
          <section>
            <h3>评分依据</h3>
            <p>{{ selectedTask.qc_result.scoring_basis || '暂无' }}</p>
          </section>
          <section>
            <h3>证据分析</h3>
            <p>{{ selectedTask.qc_result.evidence_analysis || '暂无' }}</p>
          </section>
          <section>
            <h3>错误原因</h3>
            <p>{{ selectedTask.qc_result.error_reason || '暂无' }}</p>
          </section>
          <section>
            <h3>优化建议</h3>
            <p>{{ selectedTask.qc_result.optimization_suggestion || '暂无' }}</p>
          </section>
        </div>
      </template>
      <el-empty v-else description="暂无AI质控结果" />
    </el-dialog>

    <el-dialog v-model="reviewDialogVisible" title="审核复核" width="860px">
      <template v-if="selectedTask">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="量表">{{ selectedTask.scale_type }}</el-descriptions-item>
          <el-descriptions-item label="医生评分">{{ formatScore(selectedTask.qc_result?.doctor_score ?? null) }}</el-descriptions-item>
          <el-descriptions-item label="AI评分">{{ formatScore(selectedTask.qc_result?.ai_score ?? null) }}</el-descriptions-item>
        </el-descriptions>
        <div class="review-layout">
          <el-input :model-value="selectedTask.asr_text || '暂无转录文本'" type="textarea" :rows="10" readonly />
          <el-form ref="reviewFormRef" :model="reviewForm" :rules="reviewRules" label-position="top">
            <el-form-item label="人工复核评分" prop="reviewed_score">
              <el-input-number v-model="reviewForm.reviewed_score" :min="0" :precision="1" class="full-width" />
            </el-form-item>
            <el-form-item label="复核原因" prop="review_reason">
              <el-input v-model="reviewForm.review_reason" type="textarea" :rows="4" />
            </el-form-item>
            <el-form-item label="审核意见">
              <el-input v-model="reviewForm.review_comment" type="textarea" :rows="3" />
            </el-form-item>
          </el-form>
        </div>
      </template>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewing" @click="submitReview">提交审核</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import {
  Checked,
  DataAnalysis,
  Document,
  EditPen,
  Refresh,
  RefreshRight,
  SwitchButton,
  Upload,
  UploadFilled,
  View
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createTask, fetchTask, fetchTasks, retryTask, reviewTask } from '../api/tasks'
import { useAuthStore } from '../stores/auth'
import type { ScaleType, TaskDetail, TaskListItem, TaskStage, TaskStatus } from '../types/task'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const uploading = ref(false)
const reviewing = ref(false)
const tasks = ref<TaskListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const selectedTask = ref<TaskDetail | null>(null)
const uploadDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const transcriptDialogVisible = ref(false)
const doctorDialogVisible = ref(false)
const aiDialogVisible = ref(false)
const reviewDialogVisible = ref(false)
const uploadFormRef = ref<FormInstance>()
const reviewFormRef = ref<FormInstance>()
let timer: number | undefined

const uploadForm = reactive<{ scale_type: ScaleType | ''; audio_file: File | null }>({
  scale_type: '',
  audio_file: null
})

const reviewForm = reactive({
  reviewed_score: 0,
  review_reason: '',
  review_comment: ''
})

const uploadRules: FormRules = {
  scale_type: [{ required: true, message: '请选择量表类型', trigger: 'change' }],
  audio_file: [{ required: true, message: '请上传音频文件', trigger: 'change' }]
}

const reviewRules: FormRules = {
  reviewed_score: [{ required: true, message: '请输入人工复核评分', trigger: 'blur' }],
  review_reason: [{ required: true, message: '请填写复核原因', trigger: 'blur' }]
}

const hasRunningTasks = computed(() => tasks.value.some((item) => item.status === 'PENDING' || item.status === 'RUNNING'))

async function loadTasks() {
  loading.value = true
  try {
    const data = await fetchTasks(page.value, pageSize.value)
    tasks.value = data.items
    total.value = data.total
  } catch (error) {
    if (localStorage.getItem('access_token') === 'demo-token') {
      tasks.value = []
      total.value = 0
      return
    }
    throw error
  } finally {
    loading.value = false
  }
}

async function loadSelected(taskId: number) {
  selectedTask.value = await fetchTask(taskId)
}

async function openDetail(taskId: number) {
  await loadSelected(taskId)
  detailDialogVisible.value = true
}

async function openTranscript(taskId: number) {
  await loadSelected(taskId)
  transcriptDialogVisible.value = true
}

async function openDoctorScore(taskId: number) {
  await loadSelected(taskId)
  doctorDialogVisible.value = true
}

async function openAiScore(taskId: number) {
  await loadSelected(taskId)
  aiDialogVisible.value = true
}

async function openReview(taskId: number) {
  await loadSelected(taskId)
  if (!selectedTask.value?.qc_result) {
    ElMessage.warning('AI质控完成后才能审核')
    return
  }
  reviewForm.reviewed_score = selectedTask.value.review_record?.reviewed_score ?? selectedTask.value.qc_result.ai_score ?? 0
  reviewForm.review_reason = selectedTask.value.review_record?.review_reason ?? ''
  reviewForm.review_comment = selectedTask.value.review_record?.review_comment ?? ''
  reviewDialogVisible.value = true
}

function handleAudioChange(file: UploadFile) {
  uploadForm.audio_file = file.raw || null
}

function handleAudioRemove() {
  uploadForm.audio_file = null
}

function resetUpload() {
  uploadForm.scale_type = ''
  uploadForm.audio_file = null
  uploadFormRef.value?.resetFields()
}

async function submitUpload() {
  await uploadFormRef.value?.validate()
  if (!uploadForm.scale_type || !uploadForm.audio_file) return
  uploading.value = true
  try {
    await createTask(uploadForm.scale_type, uploadForm.audio_file)
    ElMessage.success('任务已创建，正在后台解析')
    uploadDialogVisible.value = false
    await loadTasks()
  } finally {
    uploading.value = false
  }
}

async function handleRetry(taskId: number) {
  await retryTask(taskId)
  ElMessage.success('已重新投递任务')
  await loadTasks()
}

async function submitReview() {
  if (!selectedTask.value) return
  await reviewFormRef.value?.validate()
  reviewing.value = true
  try {
    await reviewTask(selectedTask.value.id, {
      reviewed_score: reviewForm.reviewed_score,
      review_reason: reviewForm.review_reason,
      review_comment: reviewForm.review_comment || undefined
    })
    ElMessage.success('审核已提交')
    reviewDialogVisible.value = false
    await loadTasks()
  } finally {
    reviewing.value = false
  }
}

function logout() {
  auth.logout()
  router.replace('/login')
}

function taskTagType(status: TaskStatus) {
  return {
    PENDING: 'info',
    RUNNING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger'
  }[status] as 'info' | 'warning' | 'success' | 'danger'
}

function asrTagType(row: TaskListItem) {
  if (row.asr_text) return 'success'
  if (row.status === 'FAILED' && row.stage === 'ASR') return 'danger'
  if (row.status === 'RUNNING' && row.stage === 'ASR') return 'warning'
  return 'info'
}

function asrStatusText(row: TaskListItem) {
  if (row.status === 'FAILED' && row.stage === 'ASR') return '识别失败'
  if (row.status === 'RUNNING' && row.stage === 'ASR') return '识别中'
  if (row.status === 'PENDING') return '等待中'
  return '已转录'
}

function taskStatusText(status: TaskStatus, stage: TaskStage | null) {
  if (status === 'RUNNING' && stage === 'ASR') return '转录中'
  if (status === 'RUNNING' && stage === 'QC') return '质控中'
  return {
    PENDING: '等待中',
    RUNNING: '处理中',
    COMPLETED: '已完成',
    FAILED: '失败'
  }[status]
}

function formatScore(score: number | null) {
  return score === null || score === undefined ? '-' : String(score)
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

onMounted(async () => {
  await loadTasks()
  timer = window.setInterval(() => {
    if (hasRunningTasks.value) loadTasks()
  }, 5000)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<template>
  <AppShell title="工作台" subtitle="查看临床评估质控任务的实时进展" platform-page>
    <section class="dashboard-header">
      <div><strong>任务概览</strong><span>数据来自当前登录账户</span></div>
      <el-button :icon="Refresh" :loading="loading" @click="loadOverview">刷新</el-button>
    </section>

    <section class="metric-grid" aria-label="任务概览数据">
      <article class="metric-card total"><div class="metric-icon"><el-icon><Files /></el-icon></div><div><span>全部任务</span><strong>{{ overview.total_tasks }}</strong></div></article>
      <article class="metric-card running"><div class="metric-icon"><el-icon><Loading /></el-icon></div><div><span>处理中</span><strong>{{ overview.running_tasks + overview.pending_tasks }}</strong></div></article>
      <article class="metric-card complete"><div class="metric-icon"><el-icon><CircleCheck /></el-icon></div><div><span>已完成</span><strong>{{ overview.completed_tasks }}</strong></div></article>
      <article class="metric-card exception"><div class="metric-icon"><el-icon><Warning /></el-icon></div><div><span>异常任务</span><strong>{{ overview.failed_tasks }}</strong></div></article>
    </section>

    <section class="dashboard-grid">
      <section class="work-panel progress-panel">
        <div class="panel-heading"><div><h2>处理进度</h2><p>任务处理状态分布</p></div><strong>{{ completionRate }}%</strong></div>
        <div class="completion-track"><i :style="{ width: `${completionRate}%` }"></i></div>
        <div class="status-grid">
          <div><span class="status-dot pending"></span><span>待处理</span><strong>{{ overview.pending_tasks }}</strong></div>
          <div><span class="status-dot running"></span><span>处理中</span><strong>{{ overview.running_tasks }}</strong></div>
          <div><span class="status-dot complete"></span><span>已完成</span><strong>{{ overview.completed_tasks }}</strong></div>
          <div><span class="status-dot failed"></span><span>异常</span><strong>{{ overview.failed_tasks }}</strong></div>
        </div>
        <div class="review-summary"><div><span>已完成审核</span><strong>{{ overview.reviewed_tasks }} 项</strong></div><RouterLink to="/">查看全部任务<el-icon><ArrowRight /></el-icon></RouterLink></div>
      </section>

      <section class="work-panel quick-panel">
        <div class="panel-heading"><div><h2>快捷操作</h2><p>进入常用工作流程</p></div></div>
        <RouterLink class="quick-action primary" to="/"><span class="quick-icon"><el-icon><UploadFilled /></el-icon></span><span><strong>新建质控任务</strong><small>上传录音并启动智能分析</small></span><el-icon><ArrowRight /></el-icon></RouterLink>
      </section>
    </section>

    <section class="work-panel recent-panel">
      <div class="panel-heading"><div><h2>最近任务</h2><p>最新提交的质控任务</p></div><RouterLink to="/" class="view-all">质控任务<el-icon><ArrowRight /></el-icon></RouterLink></div>
      <el-table v-loading="loading" class="recent-table" :data="overview.recent_tasks" empty-text="暂未创建质控任务">
        <el-table-column label="任务编号" min-width="150"><template #default="{ row }"><el-button link type="primary" @click="openTask(row.id)">{{ taskCode(row) }}</el-button></template></el-table-column>
        <el-table-column prop="scale_type" label="量表类型" width="120" />
        <el-table-column prop="audio_original_name" label="原始音频" min-width="220" show-overflow-tooltip />
        <el-table-column label="任务状态" width="120"><template #default="{ row }"><span class="status-badge" :class="statusClass(row.status)">{{ statusText(row.status, row.stage) }}</span></template></el-table-column>
        <el-table-column label="AI评分" width="100"><template #default="{ row }">{{ row.ai_score ?? '-' }}</template></el-table-column>
        <el-table-column label="创建时间" width="180"><template #default="{ row }"><span class="time-value">{{ formatTime(row.created_at) }}</span></template></el-table-column>
      </el-table>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { ArrowRight, CircleCheck, Files, Loading, Refresh, UploadFilled, Warning } from '@element-plus/icons-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDashboardOverview, type DashboardOverview, type DashboardRecentTask } from '../api/dashboard'
import AppShell from '../components/AppShell.vue'
import { useAuthStore } from '../stores/auth'
import type { TaskStage, TaskStatus } from '../types/task'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const overview = reactive<DashboardOverview>({ total_tasks: 0, pending_tasks: 0, running_tasks: 0, completed_tasks: 0, failed_tasks: 0, reviewed_tasks: 0, recent_tasks: [] })
const completionRate = computed(() => overview.total_tasks ? Math.round((overview.completed_tasks / overview.total_tasks) * 100) : 0)

async function loadOverview() {
  loading.value = true
  try { Object.assign(overview, await fetchDashboardOverview()) } finally { loading.value = false }
}

function openTask(taskId: number) { router.push({ name: 'task-detail', params: { id: taskId } }) }
function taskCode(task: DashboardRecentTask) { return `QC${new Date(task.created_at).toISOString().slice(0, 10).replace(/-/g, '')}${String(task.id).padStart(3, '0')}` }
function statusText(status: TaskStatus, stage: TaskStage | null) { if (status === 'RUNNING' && stage === 'ASR') return '转录中'; if (status === 'RUNNING' && stage === 'QC') return '质控中'; return { PENDING: '待处理', RUNNING: '处理中', COMPLETED: '已完成', FAILED: '异常' }[status] }
function statusClass(status: TaskStatus) { return { PENDING: 'pending', RUNNING: 'running', COMPLETED: 'complete', FAILED: 'failed' }[status] }
function formatTime(value: string) { return new Date(value).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-') }

onMounted(() => {
  if (auth.isAuthenticated) loadOverview()
})
</script>

<style scoped>
.dashboard-header { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin: 8px 0 18px; }.dashboard-header strong { color: #374151; font-size: 16px; }.dashboard-header span { margin-left: 12px; color: #98a1b1; font-size: 12px; }.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }.metric-card { display: flex; align-items: center; gap: 14px; min-height: 108px; padding: 20px; border: 1px solid #edf0f5; border-radius: 8px; background: #fff; box-shadow: 0 3px 13px rgba(15, 23, 42, .03); }.metric-icon { display: grid; width: 42px; height: 42px; flex: 0 0 42px; place-items: center; border-radius: 8px; font-size: 21px; }.metric-card span, .metric-card strong { display: block; }.metric-card span { color: #7a8798; font-size: 13px; }.metric-card strong { margin-top: 6px; color: #303b4f; font-size: 28px; line-height: 1; }.metric-card.total .metric-icon { background: #eef0ff; color: #6366f1; }.metric-card.running .metric-icon { background: #eff6ff; color: #3b82f6; }.metric-card.complete .metric-icon { background: #ecfdf5; color: #10b981; }.metric-card.exception .metric-icon { background: #fef2f2; color: #ef4444; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(300px, .7fr); gap: 18px; margin-top: 18px; }.work-panel { min-width: 0; padding: 22px; border: 1px solid #edf0f5; border-radius: 8px; background: #fff; box-shadow: 0 3px 13px rgba(15, 23, 42, .03); }.panel-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }.panel-heading h2, .panel-heading p { margin: 0; }.panel-heading h2 { color: #374151; font-size: 16px; }.panel-heading p { margin-top: 5px; color: #98a1b1; font-size: 12px; }.panel-heading > strong { color: #5b5ce2; font-size: 24px; }.completion-track { height: 9px; overflow: hidden; margin-top: 26px; border-radius: 9px; background: #eef1f7; }.completion-track i { display: block; height: 100%; border-radius: inherit; background: #6366f1; transition: width .25s ease; }.status-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 24px; margin-top: 22px; }.status-grid > div { display: grid; grid-template-columns: 9px 1fr auto; align-items: center; gap: 8px; color: #68758b; font-size: 13px; }.status-grid strong { color: #374151; font-size: 15px; }.status-dot { width: 8px; height: 8px; border-radius: 50%; }.status-dot.pending { background: #f59e0b; }.status-dot.running { background: #3b82f6; }.status-dot.complete { background: #10b981; }.status-dot.failed { background: #ef4444; }.review-summary { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 25px; padding-top: 18px; border-top: 1px solid #edf0f5; }.review-summary span, .review-summary strong { display: block; }.review-summary span { color: #98a1b1; font-size: 12px; }.review-summary strong { margin-top: 4px; color: #46546a; font-size: 14px; }.review-summary a, .view-all { display: inline-flex; align-items: center; gap: 5px; color: #5b5ce2; font-size: 13px; text-decoration: none; }
.quick-panel { display: flex; flex-direction: column; }.quick-action { display: grid; grid-template-columns: 38px minmax(0, 1fr) 18px; align-items: center; gap: 12px; min-height: 78px; margin-top: 14px; padding: 13px; border: 1px solid #edf0f5; border-radius: 8px; color: #64748b; text-decoration: none; }.quick-action:hover { border-color: #dfe2ff; background: #fafbff; }.quick-icon { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 8px; background: #f3f5fa; color: #68758b; font-size: 18px; }.quick-action.primary .quick-icon { background: #eef0ff; color: #6366f1; }.quick-action strong, .quick-action small { display: block; }.quick-action strong { color: #46546a; font-size: 14px; }.quick-action small { margin-top: 4px; color: #98a1b1; font-size: 12px; }.quick-action > :last-child { color: #a0a8b6; }
.recent-panel { margin-top: 18px; padding-bottom: 0; overflow: hidden; }.recent-panel .panel-heading { padding-bottom: 18px; }.recent-table { width: calc(100% + 44px); margin-left: -22px; }.recent-table :deep(.el-table__header-wrapper th.el-table__cell) { height: 48px; background: #fafbff; color: #64748b; font-size: 13px; font-weight: 500; }.recent-table :deep(.el-table__row td.el-table__cell) { height: 56px; color: #4b5563; font-size: 14px; }.status-badge { display: inline-flex; min-width: 56px; justify-content: center; padding: 4px 9px; border-radius: 6px; font-size: 12px; }.status-badge.pending { background: #fffbeb; color: #d97706; }.status-badge.running { background: #eff6ff; color: #3b82f6; }.status-badge.complete { background: #ecfdf5; color: #10b981; }.status-badge.failed { background: #fef2f2; color: #dc2626; }.time-value { color: #64748b; white-space: nowrap; }
@media (max-width: 1050px) { .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }.dashboard-grid { grid-template-columns: 1fr; } }
@media (max-width: 620px) { .dashboard-header span { display: block; margin: 5px 0 0; }.metric-grid { grid-template-columns: 1fr; }.status-grid { grid-template-columns: 1fr; }.work-panel { padding: 18px; }.recent-table { width: calc(100% + 36px); margin-left: -18px; } }
</style>

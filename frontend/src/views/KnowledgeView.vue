<template>
  <AppShell title="知识库" subtitle="沉淀临床评估规范、质控规则与参考资料">
    <section class="filter-panel" aria-label="知识库筛选">
      <el-form class="filter-form" label-position="top" @submit.prevent="applyFilters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" :prefix-icon="Search" placeholder="搜索标题或正文内容" clearable />
        </el-form-item>
        <el-form-item label="资料分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable>
            <el-option v-for="category in categories" :key="category.id" :label="category.name" :value="category.name" />
          </el-select>
        </el-form-item>
        <div class="filter-actions">
          <el-button :icon="RefreshLeft" @click="resetFilters">重置</el-button>
          <el-button type="primary" :icon="Search" native-type="submit">查询</el-button>
        </div>
      </el-form>
    </section>

    <section class="list-panel">
      <div class="list-toolbar">
        <div><strong>共 {{ total }} 条知识</strong><span>内容来自平台真实知识库数据</span></div>
        <div v-if="auth.user?.is_admin" class="toolbar-actions"><el-button :icon="FolderOpened" @click="openCategoryDialog">分类设置</el-button><el-button :icon="Key" @click="openExternalApiDialog">对外 API</el-button><el-button type="primary" :icon="Plus" @click="openCreate">新增知识</el-button></div>
      </div>

      <el-table v-loading="loading" class="knowledge-table" :data="entries" empty-text="暂无知识库内容">
        <el-table-column label="知识标题" min-width="220">
          <template #default="{ row }"><el-button link type="primary" class="title-link" @click="openDetail(row.id)">{{ row.title }}</el-button></template>
        </el-table-column>
        <el-table-column label="分类" width="135"><template #default="{ row }"><span class="category-badge">{{ row.category }}</span></template></el-table-column>
        <el-table-column label="内容摘要" min-width="280" show-overflow-tooltip><template #default="{ row }">{{ row.summary || contentPreview(row.content) || '附件资料' }}</template></el-table-column>
        <el-table-column label="附件" width="170">
          <template #default="{ row }"><el-button v-if="row.attachment_name" link type="primary" :icon="Paperclip" @click="downloadAttachment(row)">{{ row.attachment_name }}</el-button><span v-else class="muted">-</span></template>
        </el-table-column>
        <el-table-column prop="created_by_username" label="维护人" width="120" />
        <el-table-column label="更新时间" width="180"><template #default="{ row }"><span class="time-value">{{ formatTime(row.updated_at) }}</span></template></el-table-column>
        <el-table-column v-if="auth.user?.is_admin" label="操作" width="155" fixed="right">
          <template #default="{ row }"><el-button link type="primary" :icon="EditPen" @click="openEdit(row)">编辑</el-button><el-button link type="danger" :icon="Delete" @click="confirmDelete(row)">删除</el-button></template>
        </el-table-column>
      </el-table>

      <div class="pager"><span>共 {{ total }} 条</span><el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="sizes, prev, pager, next" :page-sizes="[10, 20, 50]" @change="loadEntries" /></div>
    </section>

    <el-dialog v-model="detailVisible" :title="selectedEntry?.title || '知识详情'" width="760px">
      <template v-if="selectedEntry">
        <div class="detail-meta"><span class="category-badge">{{ selectedEntry.category }}</span><span>维护人：{{ selectedEntry.created_by_username }}</span><span>更新于 {{ formatTime(selectedEntry.updated_at) }}</span></div>
        <p v-if="selectedEntry.summary" class="detail-summary">{{ selectedEntry.summary }}</p>
        <div v-if="selectedEntry.content" class="detail-content">{{ selectedEntry.content }}</div>
        <div v-if="selectedEntry.attachment_name" class="attachment-row"><div><span>资料附件</span><strong>{{ selectedEntry.attachment_name }}</strong></div><el-button :icon="Download" @click="downloadAttachment(selectedEntry)">下载</el-button></div>
      </template>
    </el-dialog>

    <el-dialog v-model="editorVisible" :title="editingEntry ? '编辑知识' : '新增知识'" width="760px" @closed="resetEditor">
      <el-form ref="editorFormRef" :model="editorForm" :rules="editorRules" label-position="top" @submit.prevent="submitEditor">
        <div class="editor-grid">
          <el-form-item label="知识标题" prop="title"><el-input v-model="editorForm.title" maxlength="255" show-word-limit placeholder="请输入知识标题" /></el-form-item>
          <el-form-item label="资料分类" prop="category"><el-select v-model="editorForm.category" placeholder="请选择资料分类"><el-option v-for="category in categories" :key="category.id" :label="category.name" :value="category.name" /></el-select></el-form-item>
        </div>
        <el-form-item label="内容摘要"><el-input v-model="editorForm.summary" type="textarea" :rows="2" maxlength="500" show-word-limit placeholder="概括资料用途，便于检索" /></el-form-item>
        <el-form-item label="正文内容"><el-input v-model="editorForm.content" type="textarea" :rows="10" placeholder="请输入可直接阅读的知识内容；若仅上传附件可留空" /></el-form-item>
        <el-form-item label="资料附件">
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" :on-change="handleAttachmentChange" :on-remove="handleAttachmentRemove" accept=".pdf,.doc,.docx,.txt,.md,.csv,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.svg,.tif,.tiff,.heic,image/*"><el-button :icon="Upload">选择文件</el-button><template #tip><div class="el-upload__tip">支持 PDF、Word、文本、表格及常见图片，最大 20 MB</div></template></el-upload>
          <el-checkbox v-if="editingEntry?.attachment_name && !attachmentFile" v-model="editorForm.removeAttachment" class="remove-attachment">移除当前附件：{{ editingEntry.attachment_name }}</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer><el-button @click="editorVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitEditor">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="categoryDialogVisible" title="资料分类设置" width="540px">
      <div class="category-create-row"><el-input v-model="categoryName" maxlength="64" placeholder="请输入资料分类名称" @keyup.enter="addCategory" /><el-button type="primary" :loading="categorySaving" @click="addCategory">添加</el-button></div>
      <div v-if="categories.length" class="category-list"><div v-for="category in categories" :key="category.id" class="category-list-item"><span>{{ category.name }}</span><el-button link type="danger" :icon="Delete" @click="confirmDeleteCategory(category)">删除</el-button></div></div>
      <el-empty v-else description="暂未设置资料分类" :image-size="76" />
    </el-dialog>

    <el-dialog v-model="externalApiDialogVisible" title="知识库对外 API" width="620px">
      <div class="external-status"><div><strong>开通对外访问</strong><span>使用 API Key 供外部系统检索知识库与下载附件</span></div><el-switch v-model="externalApi.is_enabled" /></div>
      <el-form class="external-form" label-position="top">
        <el-form-item label="API 地址"><div class="copy-input"><el-input :model-value="externalEndpoint" readonly /><el-button :icon="CopyDocument" aria-label="复制 API 地址" @click="copyText(externalEndpoint)">复制</el-button></div></el-form-item>
        <el-form-item label="API Key"><div class="copy-input"><el-input :model-value="displayedApiKey" type="password" show-password readonly /><el-button :disabled="!externalApi.api_key" :icon="CopyDocument" aria-label="复制 API Key" @click="copyText(externalApi.api_key || '')">复制</el-button></div><span class="api-key-hint">{{ externalApi.api_key ? '请立即保存该密钥，关闭窗口后无法再次查看完整内容。' : externalApi.key_configured ? `当前密钥：${externalApi.api_key_prefix}...` : '开通后将自动生成 API Key。' }}</span></el-form-item>
      </el-form>
      <template #footer><el-button v-if="externalApi.key_configured" :loading="externalApiSaving" @click="regenerateExternalApiKey">重新生成密钥</el-button><el-button @click="externalApiDialogVisible = false">取消</el-button><el-button type="primary" :loading="externalApiSaving" @click="saveExternalApiSettings">保存</el-button></template>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { CopyDocument, Delete, Download, EditPen, FolderOpened, Key, Paperclip, Plus, RefreshLeft, Search, Upload } from '@element-plus/icons-vue'
import type { FormInstance, FormRules, UploadFile, UploadInstance } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { createKnowledgeCategory, createKnowledgeEntry, deleteKnowledgeCategory, deleteKnowledgeEntry, downloadKnowledgeAttachment, fetchKnowledge, fetchKnowledgeCategories, fetchKnowledgeEntry, fetchKnowledgeExternalApiSettings, updateKnowledgeEntry, updateKnowledgeExternalApiSettings, type KnowledgeCategory, type KnowledgeEntry } from '../api/knowledge'
import { useAuthStore } from '../stores/auth'

const categories = ref<KnowledgeCategory[]>([])
const auth = useAuthStore()
const entries = ref<KnowledgeEntry[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const saving = ref(false)
const detailVisible = ref(false)
const editorVisible = ref(false)
const categoryDialogVisible = ref(false)
const externalApiDialogVisible = ref(false)
const categorySaving = ref(false)
const externalApiSaving = ref(false)
const selectedEntry = ref<KnowledgeEntry | null>(null)
const editingEntry = ref<KnowledgeEntry | null>(null)
const attachmentFile = ref<File | null>(null)
const editorFormRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()
const filters = reactive({ keyword: '', category: '' })
const editorForm = reactive({ title: '', category: '', summary: '', content: '', removeAttachment: false })
const categoryName = ref('')
const externalApi = reactive({ is_enabled: false, key_configured: false, api_key_prefix: null as string | null, api_key: null as string | null })
const externalEndpoint = computed(() => `${window.location.origin}/api/v1/external/knowledge`)
const displayedApiKey = computed(() => externalApi.api_key || (externalApi.key_configured ? `${externalApi.api_key_prefix || 'kb'}********` : '未生成'))
const editorRules: FormRules = {
  title: [{ required: true, message: '请输入知识标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择或输入资料分类', trigger: 'change' }]
}

async function loadEntries() {
  loading.value = true
  try {
    const data = await fetchKnowledge({ page: page.value, pageSize: pageSize.value, keyword: filters.keyword, category: filters.category })
    entries.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try { categories.value = await fetchKnowledgeCategories() } catch (error) { ElMessage.error(errorMessage(error)) }
}

function applyFilters() { page.value = 1; loadEntries() }
function resetFilters() { filters.keyword = ''; filters.category = ''; page.value = 1; loadEntries() }

async function openDetail(entryId: number) {
  try {
    selectedEntry.value = await fetchKnowledgeEntry(entryId)
    detailVisible.value = true
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

function openCreate() {
  editingEntry.value = null
  resetEditor()
  editorVisible.value = true
}

function openCategoryDialog() {
  categoryName.value = ''
  categoryDialogVisible.value = true
  loadCategories()
}

async function addCategory() {
  if (!categoryName.value.trim()) { ElMessage.warning('请输入资料分类名称'); return }
  categorySaving.value = true
  try {
    const category = await createKnowledgeCategory(categoryName.value.trim())
    categoryName.value = ''
    editorForm.category = category.name
    ElMessage.success('资料分类已添加')
    await loadCategories()
  } catch (error) { ElMessage.error(errorMessage(error)) } finally { categorySaving.value = false }
}

async function confirmDeleteCategory(category: KnowledgeCategory) {
  try {
    await ElMessageBox.confirm(`确定删除资料分类“${category.name}”吗？`, '删除分类', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteKnowledgeCategory(category.id)
    if (filters.category === category.name) filters.category = ''
    if (editorForm.category === category.name) editorForm.category = ''
    ElMessage.success('资料分类已删除')
    await loadCategories()
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(errorMessage(error)) }
}

async function openExternalApiDialog() {
  try {
    const settings = await fetchKnowledgeExternalApiSettings()
    externalApi.is_enabled = settings.is_enabled
    externalApi.key_configured = settings.key_configured
    externalApi.api_key_prefix = settings.api_key_prefix
    externalApi.api_key = null
    externalApiDialogVisible.value = true
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

async function saveExternalApiSettings() {
  externalApiSaving.value = true
  try {
    const settings = await updateKnowledgeExternalApiSettings({ is_enabled: externalApi.is_enabled })
    externalApi.key_configured = settings.key_configured
    externalApi.api_key_prefix = settings.api_key_prefix
    externalApi.api_key = settings.api_key
    ElMessage.success(settings.is_enabled ? '知识库对外 API 已开通' : '知识库对外 API 已关闭')
  } catch (error) { ElMessage.error(errorMessage(error)) } finally { externalApiSaving.value = false }
}

async function regenerateExternalApiKey() {
  try {
    await ElMessageBox.confirm('重新生成后，原 API Key 将立即失效。确认继续吗？', '重新生成密钥', { type: 'warning', confirmButtonText: '重新生成', cancelButtonText: '取消' })
    externalApiSaving.value = true
    const settings = await updateKnowledgeExternalApiSettings({ is_enabled: true, regenerate_key: true })
    externalApi.is_enabled = settings.is_enabled
    externalApi.key_configured = settings.key_configured
    externalApi.api_key_prefix = settings.api_key_prefix
    externalApi.api_key = settings.api_key
    ElMessage.success('API Key 已重新生成')
  } catch (error) { if (error !== 'cancel' && error !== 'close') ElMessage.error(errorMessage(error)) } finally { externalApiSaving.value = false }
}

function openEdit(entry: KnowledgeEntry) {
  editingEntry.value = entry
  editorForm.title = entry.title
  editorForm.category = entry.category
  editorForm.summary = entry.summary || ''
  editorForm.content = entry.content
  editorForm.removeAttachment = false
  attachmentFile.value = null
  editorVisible.value = true
}

function resetEditor() {
  editorFormRef.value?.resetFields()
  uploadRef.value?.clearFiles()
  editorForm.title = ''
  editorForm.category = ''
  editorForm.summary = ''
  editorForm.content = ''
  editorForm.removeAttachment = false
  attachmentFile.value = null
  editingEntry.value = null
}

function handleAttachmentChange(file: UploadFile) {
  attachmentFile.value = file.raw || null
  if (attachmentFile.value) editorForm.removeAttachment = false
}

function handleAttachmentRemove() { attachmentFile.value = null }

async function submitEditor() {
  await editorFormRef.value?.validate()
  if (!editorForm.content.trim() && !attachmentFile.value && !(editingEntry.value?.attachment_name && !editorForm.removeAttachment)) {
    ElMessage.warning('请填写正文内容或上传资料附件')
    return
  }
  saving.value = true
  try {
    const payload = new FormData()
    payload.append('title', editorForm.title.trim())
    payload.append('category', editorForm.category.trim())
    payload.append('summary', editorForm.summary.trim())
    payload.append('content', editorForm.content.trim())
    payload.append('remove_attachment', String(editorForm.removeAttachment))
    if (attachmentFile.value) payload.append('attachment', attachmentFile.value)
    if (editingEntry.value) {
      await updateKnowledgeEntry(editingEntry.value.id, payload)
      ElMessage.success('知识已更新')
    } else {
      await createKnowledgeEntry(payload)
      ElMessage.success('知识已创建')
    }
    editorVisible.value = false
    await loadEntries()
  } catch (error) { ElMessage.error(errorMessage(error)) } finally { saving.value = false }
}

async function confirmDelete(entry: KnowledgeEntry) {
  try {
    await ElMessageBox.confirm(`确定删除知识“${entry.title}”吗？`, '删除知识', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteKnowledgeEntry(entry.id)
    ElMessage.success('知识已删除')
    if (entries.value.length === 1 && page.value > 1) page.value -= 1
    await loadEntries()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(errorMessage(error))
  }
}

async function downloadAttachment(entry: KnowledgeEntry) {
  try {
    const blob = await downloadKnowledgeAttachment(entry.id)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = entry.attachment_name || 'knowledge-attachment'
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (error) { ElMessage.error(errorMessage(error)) }
}

function contentPreview(content: string) { return content.replace(/\s+/g, ' ').slice(0, 70) }
function formatTime(value: string) { return new Date(value).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-') }
function errorMessage(error: unknown) { return (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '操作失败，请稍后重试' }
async function copyText(value: string) { try { await navigator.clipboard.writeText(value); ElMessage.success('已复制') } catch { ElMessage.error('复制失败，请手动复制') } }

onMounted(async () => { await loadCategories(); await loadEntries() })
</script>

<style scoped>
.filter-panel, .list-panel { min-width: 0; border: 1px solid #eff1f6; border-radius: 8px; background: #fff; box-shadow: 0 4px 16px rgba(15, 23, 42, .035); }.filter-panel { padding: 22px 30px; }.filter-form { display: grid; grid-template-columns: minmax(220px, 1fr) minmax(180px, 1fr) auto; align-items: end; gap: 24px; max-width: 900px; }.filter-form :deep(.el-form-item) { margin-bottom: 0; }.filter-form :deep(.el-form-item__label) { padding-bottom: 8px; color: #374151; font-size: 14px; }.filter-actions { display: flex; gap: 10px; }
.list-panel { margin-top: 24px; overflow: hidden; }.list-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 22px; }.list-toolbar strong { color: #374151; font-size: 15px; }.list-toolbar span { margin-left: 12px; color: #9ca3af; font-size: 12px; }.toolbar-actions { display: flex; gap: 10px; }.knowledge-table { width: 100%; }.knowledge-table :deep(.el-table__header-wrapper th.el-table__cell) { height: 48px; background: #fafbff; color: #64748b; font-size: 13px; font-weight: 500; }.knowledge-table :deep(.el-table__row td.el-table__cell) { height: 60px; color: #4b5563; font-size: 14px; }.knowledge-table :deep(.el-table__row:hover > td.el-table__cell) { background: #f8faff; }.title-link { max-width: 100%; padding: 0; overflow: hidden; font-weight: 600; text-overflow: ellipsis; }.category-badge { display: inline-flex; padding: 4px 9px; border-radius: 6px; background: #eef0ff; color: #5b5ce2; font-size: 12px; }.time-value, .muted { color: #8a94a6; white-space: nowrap; }
.pager { display: flex; align-items: center; justify-content: flex-end; gap: 20px; min-height: 72px; padding: 14px 22px; border-top: 1px solid #f1f5f9; color: #4b5563; font-size: 14px; }.pager :deep(.el-pager li.is-active) { background: #6366f1; color: #fff; }.pager :deep(.el-pager li), .pager :deep(.btn-prev), .pager :deep(.btn-next) { border: 1px solid #e5e7eb; border-radius: 7px; }
.detail-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; color: #7b8798; font-size: 13px; }.detail-summary { margin: 18px 0 0; padding: 12px 14px; border-left: 3px solid #818cf8; background: #f8f9ff; color: #56647a; font-size: 14px; line-height: 1.65; }.detail-content { max-height: 420px; overflow: auto; margin-top: 18px; padding: 16px; border: 1px solid #edf0f5; border-radius: 8px; background: #fafbff; color: #46546a; font-size: 14px; line-height: 1.85; white-space: pre-wrap; }.attachment-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 18px; padding: 14px 16px; border: 1px solid #e8ebf2; border-radius: 8px; }.attachment-row span, .attachment-row strong { display: block; }.attachment-row span { color: #8a94a6; font-size: 12px; }.attachment-row strong { margin-top: 4px; color: #46546a; font-size: 14px; }.editor-grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(180px, .65fr); gap: 18px; }.editor-grid :deep(.el-form-item) { min-width: 0; }.editor-grid :deep(.el-select) { width: 100%; }.remove-attachment { display: block; margin-top: 12px; }
.category-create-row { display: flex; gap: 10px; }.category-list { display: grid; gap: 8px; margin-top: 18px; }.category-list-item { display: flex; align-items: center; justify-content: space-between; min-height: 44px; padding: 0 12px; border: 1px solid #edf0f5; border-radius: 7px; color: #46546a; font-size: 14px; }.external-status { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 14px 16px; border: 1px solid #e5e7ff; border-radius: 8px; background: #f8f9ff; }.external-status strong, .external-status span { display: block; }.external-status strong { color: #374151; font-size: 14px; }.external-status span, .api-key-hint { margin-top: 5px; color: #8a94a6; font-size: 12px; line-height: 1.5; }.external-form { margin-top: 20px; }.copy-input { display: flex; gap: 8px; }.copy-input :deep(.el-input) { min-width: 0; flex: 1; }
@media (max-width: 720px) { .filter-panel { padding: 18px; }.filter-form, .editor-grid { grid-template-columns: 1fr; gap: 12px; }.list-toolbar { align-items: flex-start; flex-direction: column; }.list-toolbar span { display: block; margin: 5px 0 0; }.toolbar-actions { flex-wrap: wrap; }.pager { align-items: flex-end; flex-direction: column; } }
</style>

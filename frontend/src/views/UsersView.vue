<template>
  <AppShell title="用户管理" subtitle="管理平台用户、账号状态与登录权限">
    <section class="filter-panel" aria-label="用户筛选">
      <el-form class="filter-form" label-position="top" @submit.prevent="applyFilters">
        <el-form-item label="用户名">
          <el-input v-model="filters.keyword" :prefix-icon="Search" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="账号状态">
          <el-select v-model="filters.isActive" placeholder="全部状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="停用" :value="false" />
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
        <div><strong>共 {{ total }} 位用户</strong><span>账号变更将立即生效</span></div>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
      </div>

      <el-table v-loading="loading" class="user-table" :data="users" empty-text="暂无用户数据">
        <el-table-column prop="id" label="用户 ID" width="120" />
        <el-table-column label="用户名" min-width="220">
          <template #default="{ row }">
            <div class="user-name"><span class="user-avatar">{{ row.username.slice(0, 1).toUpperCase() }}</span><strong>{{ row.username }}</strong><span v-if="row.is_admin" class="admin-badge">管理员</span></div>
          </template>
        </el-table-column>
        <el-table-column label="账号状态" width="140">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" :disabled="row.id === auth.user?.id" active-text="启用" inactive-text="停用" inline-prompt @change="handleStatusChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="190">
          <template #default="{ row }"><span class="time-value">{{ formatTime(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="EditPen" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" :icon="Key" @click="openPasswordDialog(row)">修改密码</el-button>
            <el-button link type="danger" :icon="Delete" :disabled="row.id === auth.user?.id" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <span>共 {{ total }} 条</span>
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="sizes, prev, pager, next" :page-sizes="[10, 20, 50]" @change="loadUsers" />
      </div>
    </section>

    <el-dialog v-model="dialogVisible" :title="editingUser ? '编辑用户' : '新建用户'" width="480px" @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="formRules" label-position="top" @submit.prevent="submitForm">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" maxlength="64" show-word-limit placeholder="请输入 3-64 位用户名" autocomplete="off" />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="登录密码" prop="password">
          <el-input v-model="form.password" type="password" maxlength="128" show-password placeholder="请输入不少于 8 位的密码" autocomplete="new-password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="440px" @closed="resetPasswordForm">
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top" @submit.prevent="submitPassword">
        <el-form-item label="用户"><el-input :model-value="passwordUser?.username" disabled /></el-form-item>
        <el-form-item label="新密码" prop="password"><el-input v-model="passwordForm.password" type="password" maxlength="128" show-password placeholder="请输入不少于 8 位的新密码" autocomplete="new-password" /></el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword"><el-input v-model="passwordForm.confirmPassword" type="password" maxlength="128" show-password placeholder="请再次输入新密码" autocomplete="new-password" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="passwordDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="submitPassword">确认修改</el-button></template>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { Delete, EditPen, Key, Plus, RefreshLeft, Search } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { createUser, deleteUser, fetchUsers, updateUser, updateUserStatus, type ManagedUser } from '../api/users'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const passwordDialogVisible = ref(false)
const editingUser = ref<ManagedUser | null>(null)
const passwordUser = ref<ManagedUser | null>(null)
const users = ref<ManagedUser[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const formRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const filters = reactive<{ keyword: string; isActive: boolean | '' }>({ keyword: '', isActive: '' })
const form = reactive({ username: '', password: '' })
const passwordForm = reactive({ password: '', confirmPassword: '' })
const formRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, max: 64, message: '用户名长度为 3-64 位', trigger: 'blur' }],
  password: [{ min: 8, max: 128, message: '密码长度不少于 8 位', trigger: 'blur' }]
}
const passwordRules: FormRules = {
  password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 8, max: 128, message: '密码长度不少于 8 位', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请再次输入新密码', trigger: 'blur' }, { min: 8, max: 128, message: '密码长度不少于 8 位', trigger: 'blur' }]
}

async function loadUsers() {
  loading.value = true
  try {
    const data = await fetchUsers({ page: page.value, pageSize: pageSize.value, keyword: filters.keyword, isActive: filters.isActive })
    users.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  page.value = 1
  loadUsers()
}

function resetFilters() {
  filters.keyword = ''
  filters.isActive = ''
  page.value = 1
  loadUsers()
}

function openCreate() {
  editingUser.value = null
  form.username = ''
  form.password = ''
  dialogVisible.value = true
}

function openEdit(user: ManagedUser) {
  editingUser.value = user
  form.username = user.username
  form.password = ''
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
  editingUser.value = null
  form.username = ''
  form.password = ''
}

function openPasswordDialog(user: ManagedUser) {
  passwordUser.value = user
  passwordForm.password = ''
  passwordForm.confirmPassword = ''
  passwordDialogVisible.value = true
}

function resetPasswordForm() {
  passwordFormRef.value?.resetFields()
  passwordUser.value = null
  passwordForm.password = ''
  passwordForm.confirmPassword = ''
}

async function submitForm() {
  await formRef.value?.validate()
  if (!editingUser.value && !form.password) {
    ElMessage.warning('请设置登录密码')
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      await updateUser(editingUser.value.id, { username: form.username.trim() })
      ElMessage.success('用户信息已更新')
    } else {
      await createUser({ username: form.username.trim(), password: form.password })
      ElMessage.success('用户已创建')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}

async function submitPassword() {
  if (!passwordUser.value) return
  await passwordFormRef.value?.validate()
  if (passwordForm.password !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  saving.value = true
  try {
    await updateUser(passwordUser.value.id, { password: passwordForm.password })
    ElMessage.success('密码已修改')
    passwordDialogVisible.value = false
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}

async function handleStatusChange(user: ManagedUser) {
  const nextStatus = user.is_active
  try {
    await updateUserStatus(user.id, nextStatus)
    ElMessage.success(nextStatus ? '用户已启用' : '用户已停用')
  } catch (error) {
    user.is_active = !nextStatus
    ElMessage.error(errorMessage(error))
  }
}

async function confirmDelete(user: ManagedUser) {
  try {
    await ElMessageBox.confirm(`确定删除用户“${user.username}”吗？`, '删除用户', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
    await deleteUser(user.id)
    ElMessage.success('用户已删除')
    if (users.value.length === 1 && page.value > 1) page.value -= 1
    await loadUsers()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(errorMessage(error))
  }
}

function errorMessage(error: unknown) {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
  return detail || '操作失败，请稍后重试'
}

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
}

onMounted(loadUsers)
</script>

<style scoped>
.filter-panel, .list-panel { min-width: 0; border: 1px solid #eff1f6; border-radius: 8px; background: #fff; box-shadow: 0 4px 16px rgba(15, 23, 42, .035); }
.filter-panel { padding: 22px 30px; }.filter-form { display: grid; grid-template-columns: minmax(220px, 1fr) minmax(180px, 1fr) auto; align-items: end; gap: 24px; max-width: 900px; }.filter-form :deep(.el-form-item) { margin-bottom: 0; }.filter-form :deep(.el-form-item__label) { padding-bottom: 8px; color: #374151; font-size: 14px; }.filter-actions { display: flex; gap: 10px; }
.list-panel { margin-top: 24px; overflow: hidden; }.list-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 22px; }.list-toolbar strong { color: #374151; font-size: 15px; }.list-toolbar span { margin-left: 12px; color: #9ca3af; font-size: 12px; }
.user-table { width: 100%; }.user-table :deep(.el-table__header-wrapper th.el-table__cell) { height: 48px; background: #fafbff; color: #64748b; font-size: 13px; font-weight: 500; }.user-table :deep(.el-table__row td.el-table__cell) { height: 60px; color: #4b5563; font-size: 14px; }.user-table :deep(.el-table__row:hover > td.el-table__cell) { background: #f8faff; }.user-name { display: flex; align-items: center; gap: 10px; }.user-name strong { color: #374151; font-weight: 600; }.user-avatar { display: grid; width: 30px; height: 30px; place-items: center; border-radius: 50%; background: #eef0ff; color: #5b5ce2; font-size: 13px; font-weight: 700; }.admin-badge { padding: 3px 7px; border-radius: 5px; background: #fff7ed; color: #ea580c; font-size: 11px; }.time-value { color: #64748b; white-space: nowrap; }
.pager { display: flex; align-items: center; justify-content: flex-end; gap: 20px; min-height: 72px; padding: 14px 22px; border-top: 1px solid #f1f5f9; color: #4b5563; font-size: 14px; }.pager :deep(.el-pager li.is-active) { background: #6366f1; color: #fff; }.pager :deep(.el-pager li), .pager :deep(.btn-prev), .pager :deep(.btn-next) { border: 1px solid #e5e7eb; border-radius: 7px; }
@media (max-width: 720px) { .filter-panel { padding: 18px; }.filter-form { grid-template-columns: 1fr; gap: 12px; }.list-toolbar { align-items: flex-start; flex-direction: column; }.list-toolbar span { display: block; margin: 5px 0 0; }.pager { align-items: flex-end; flex-direction: column; } }
</style>

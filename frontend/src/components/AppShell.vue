<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <aside class="app-sidebar">
      <div class="brand">
        <div class="brand-mark">AI</div>
        <div>
          <strong>AI临床评估质控平台</strong>
          <span>AI Clinical QC Platform</span>
        </div>
      </div>

      <nav class="primary-nav" aria-label="主导航">
        <RouterLink class="nav-item" :class="{ active: route.name === 'dashboard' }" to="/dashboard">
          <el-icon><Grid /></el-icon>
          <span>工作台</span>
        </RouterLink>
        <RouterLink class="nav-item" :class="{ active: route.name === 'qc-list' || route.name === 'task-detail' }" to="/">
          <el-icon><DocumentChecked /></el-icon>
          <span>质控任务</span>
        </RouterLink>
        <RouterLink class="nav-item" :class="{ active: route.name === 'knowledge' }" to="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </RouterLink>
        <RouterLink v-if="auth.user?.is_admin" class="nav-item" :class="{ active: route.name === 'users' }" to="/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </RouterLink>
        <RouterLink class="nav-item" :class="{ active: route.name === 'settings' }" to="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </RouterLink>
      </nav>

      <div class="user-panel">
        <div class="user-summary">
          <div class="avatar">{{ auth.user?.username.slice(0, 1).toUpperCase() || 'U' }}</div>
          <div>
            <strong>{{ auth.user?.username || '未登录用户' }}</strong>
            <span>{{ auth.user?.is_admin ? '系统管理员' : '临床用户' }}</span>
          </div>
        </div>
        <div class="user-panel-divider"></div>
        <strong class="empower-title">AI赋能临床评估</strong>
        <span class="empower-copy">让质控更智能，更高效</span>
        <div class="progress-row">
          <div class="progress-track"><i></i></div>
          <span>82%</span>
        </div>
      </div>
    </aside>

    <div class="app-main">
      <header class="app-header">
        <div class="page-heading">
          <el-tooltip :content="sidebarCollapsed ? '展开菜单' : '折叠菜单'" placement="bottom">
            <el-button class="sidebar-toggle" circle text :aria-label="sidebarCollapsed ? '展开菜单' : '折叠菜单'" @click="toggleSidebar">
              <el-icon :size="20"><Expand v-if="sidebarCollapsed" /><Fold v-else /></el-icon>
            </el-button>
          </el-tooltip>
          <div class="heading-copy">
            <h1>{{ title }}</h1>
            <p>{{ subtitle }}</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button circle text aria-label="通知">
            <el-badge is-dot type="danger"><el-icon :size="20"><Bell /></el-icon></el-badge>
          </el-button>
          <el-button circle text aria-label="帮助"><el-icon :size="20"><QuestionFilled /></el-icon></el-button>
          <el-button circle text aria-label="退出登录" @click="logout"><el-icon :size="19"><SwitchButton /></el-icon></el-button>
        </div>
      </header>
      <main class="page-canvas"><slot /></main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Bell,
  Collection,
  DocumentChecked,
  Expand,
  Fold,
  Grid,
  QuestionFilled,
  Setting,
  SwitchButton,
  UserFilled
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useRoute } from 'vue-router'
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

defineProps<{ title: string; subtitle: string }>()

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const sidebarCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar-collapsed', String(sidebarCollapsed.value))
}

function logout() {
  auth.logout()
  router.replace('/login')
}
</script>

<style scoped>
.app-shell { display: flex; min-height: 100vh; background: #f7f8fc; }
.app-sidebar { position: sticky; top: 0; z-index: 10; display: flex; width: 240px; height: 100vh; flex: 0 0 240px; flex-direction: column; border-right: 1px solid #e8ebf2; background: #fff; }
.brand { display: flex; align-items: center; gap: 10px; min-height: 92px; padding: 20px 24px; border-bottom: 1px solid #edf0f5; }
.brand-mark { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 14px 10px 14px 10px; background: linear-gradient(135deg, #3279f4, #8655ef); color: #fff; font-weight: 700; font-size: 16px; }
.brand strong, .brand span { display: block; white-space: nowrap; }
.brand strong { color: #111827; font-size: 15px; line-height: 1.35; }
.brand span { margin-top: 3px; color: #7c879b; font-size: 10px; }
.primary-nav { display: flex; min-height: 0; flex: 1; flex-direction: column; gap: 5px; padding: 30px 16px; }
.nav-label { padding: 0 16px 8px; color: #9ca3af; font-size: 12px; }
.nav-item { position: relative; display: flex; align-items: center; min-height: 46px; gap: 15px; border: 0; border-radius: 7px; padding: 0 16px; background: transparent; color: #64748b; font: inherit; font-size: 15px; text-align: left; text-decoration: none; cursor: pointer; }
.nav-item:hover:not(:disabled) { background: #f5f7ff; color: #5b5ce2; }
.nav-item:disabled { cursor: default; }
.nav-item.active { background: #eef0ff; color: #5b5ce2; font-weight: 600; }
.nav-item.active::before { position: absolute; left: 0; width: 4px; height: 26px; border-radius: 0 4px 4px 0; background: #6366f1; content: ''; }
.user-panel { flex-shrink: 0; margin: 16px; padding: 18px; border: 1px solid #eef0f6; border-radius: 8px; box-shadow: 0 4px 16px rgba(15, 23, 42, .04); }
.user-summary { display: flex; align-items: center; gap: 11px; }
.avatar { display: grid; width: 40px; height: 40px; place-items: center; border-radius: 50%; background: linear-gradient(135deg, #52a1ff, #8b5cf6); color: #fff; font-size: 18px; }
.user-summary strong, .user-summary span { display: block; }
.user-summary strong { color: #1f2937; font-size: 14px; }
.user-summary span, .empower-copy { margin-top: 3px; color: #8a94a6; font-size: 12px; }
.user-panel-divider { height: 1px; margin: 16px -18px; background: #eef0f6; }
.empower-title, .empower-copy { display: block; }
.empower-title { color: #1f2937; font-size: 13px; }
.progress-row { display: flex; align-items: center; gap: 9px; margin-top: 14px; color: #667085; font-size: 12px; }
.progress-track { height: 8px; flex: 1; overflow: hidden; border-radius: 99px; background: #eef2ff; }
.progress-track i { display: block; width: 82%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.app-main { min-width: 0; flex: 1; }
.app-header { display: flex; min-height: 92px; align-items: center; justify-content: space-between; gap: 24px; border-bottom: 1px solid #f0f2f8; padding: 16px 40px 15px 44px; background: #fff; }
.page-heading { display: flex; align-items: flex-start; gap: 12px; min-width: 0; }
.sidebar-toggle { flex-shrink: 0; margin-top: -2px; color: #64748b; }
.sidebar-toggle:hover { color: #5b5ce2; background: #f5f7ff; }
.heading-copy { min-width: 0; }
.page-heading h1, .page-heading p { margin: 0; }
.page-heading h1 { color: #111827; font-size: 24px; line-height: 1.25; }
.page-heading p { margin-top: 6px; color: #68758b; font-size: 14px; }
.header-actions { display: flex; align-items: center; gap: 6px; }
.page-canvas { min-width: 0; overflow: hidden; padding: 16px 24px 32px; }
.sidebar-collapsed .app-sidebar { width: 72px; flex-basis: 72px; }
.sidebar-collapsed .brand { justify-content: center; padding: 16px; }
.sidebar-collapsed .brand > div:last-child, .sidebar-collapsed .nav-item span, .sidebar-collapsed .nav-label, .sidebar-collapsed .user-panel { display: none; }
.sidebar-collapsed .primary-nav { align-items: center; padding: 30px 10px; }
.sidebar-collapsed .nav-item { justify-content: center; width: 48px; padding: 0; }
@media (max-width: 900px) { .app-sidebar { width: 72px; flex-basis: 72px; } .brand { padding: 16px; justify-content: center; } .brand > div:last-child, .nav-item span, .nav-label, .user-panel { display: none; } .primary-nav { align-items: center; padding: 20px 10px; } .nav-item { justify-content: center; width: 48px; padding: 0; } .app-header { padding: 16px 22px; } }
@media (max-width: 600px) { .app-sidebar { display: none; } .app-header { min-height: 78px; padding: 14px 18px; } .page-heading h1 { font-size: 20px; } .page-heading p { display: none; } .page-canvas { padding: 14px; } }
</style>

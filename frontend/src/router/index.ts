import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import QcListView from '../views/QcListView.vue'
import SettingsView from '../views/SettingsView.vue'
import TaskDetailView from '../views/TaskDetailView.vue'
import UsersView from '../views/UsersView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import DashboardView from '../views/DashboardView.vue'
import PlatformHomeView from '../views/PlatformHomeView.vue'
import PlatformLoginView from '../views/PlatformLoginView.vue'
import PlatformResearchView from '../views/PlatformResearchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/platform/login', name: 'platform-login', component: PlatformLoginView, meta: { publicPlatform: true } },
    { path: '/platform', name: 'platform-home', component: PlatformHomeView, meta: { publicPlatform: true, platformShell: true } },
    { path: '/platform/research', name: 'platform-research', component: PlatformResearchView, meta: { publicPlatform: true, platformShell: true } },
    { path: '/login', name: 'login', component: PlatformLoginView, meta: { publicPlatform: true } },
    { path: '/', name: 'qc-list', component: QcListView, meta: { platformShell: true } },
    { path: '/tasks/:id', name: 'task-detail', component: TaskDetailView, meta: { platformShell: true } },
    { path: '/settings', name: 'settings', component: SettingsView, meta: { platformShell: true } },
    { path: '/users', name: 'users', component: UsersView, meta: { requiresAdmin: true, platformShell: true } },
    { path: '/knowledge', name: 'knowledge', component: KnowledgeView, meta: { platformShell: true } },
    { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { publicPlatform: true, platformShell: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.publicPlatform) return true
  if (to.name === 'login') {
    if (!auth.isAuthenticated) return true
    if (!auth.user) {
      try {
        await auth.loadMe()
      } catch {
        auth.logout()
        return true
      }
    }
    return { name: 'qc-list' }
  }
  if (!auth.isAuthenticated) return { name: 'login' }
  if (!auth.user) {
    try {
      await auth.loadMe()
    } catch {
      return { name: 'login' }
    }
  }
  if (to.meta.requiresAdmin && !auth.user?.is_admin) return { name: 'qc-list' }
  return true
})

export default router


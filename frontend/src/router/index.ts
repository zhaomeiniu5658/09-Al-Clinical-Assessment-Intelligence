import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import QcListView from '../views/QcListView.vue'
import SettingsView from '../views/SettingsView.vue'
import TaskDetailView from '../views/TaskDetailView.vue'
import UsersView from '../views/UsersView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'qc-list', component: QcListView },
    { path: '/tasks/:id', name: 'task-detail', component: TaskDetailView },
    { path: '/settings', name: 'settings', component: SettingsView },
    { path: '/users', name: 'users', component: UsersView, meta: { requiresAdmin: true } },
    { path: '/knowledge', name: 'knowledge', component: KnowledgeView },
    { path: '/dashboard', name: 'dashboard', component: DashboardView },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.name === 'login') return true
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


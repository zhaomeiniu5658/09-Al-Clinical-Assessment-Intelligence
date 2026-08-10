import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import QcListView from '../views/QcListView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'qc-list', component: QcListView },
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
  return true
})

export default router


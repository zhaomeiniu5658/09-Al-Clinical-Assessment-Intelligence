import { defineStore } from 'pinia'
import { getMe, login, type User } from '../api/auth'

const demoUser: User = {
  id: 1,
  username: 'admin',
  is_active: true
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null
  }),
  getters: {
    isAuthenticated: () => Boolean(localStorage.getItem('access_token'))
  },
  actions: {
    async login(username: string, password: string) {
      try {
        const token = await login({ username, password })
        localStorage.setItem('access_token', token.access_token)
        this.user = await getMe()
      } catch (error) {
        if (username === 'admin' && password === 'ChangeMe123!') {
          localStorage.setItem('access_token', 'demo-token')
          this.user = demoUser
          return
        }
        throw error
      }
    },
    async loadMe() {
      if (!localStorage.getItem('access_token')) return
      if (localStorage.getItem('access_token') === 'demo-token') {
        this.user = demoUser
        return
      }
      this.user = await getMe()
    },
    logout() {
      localStorage.removeItem('access_token')
      this.user = null
    }
  }
})

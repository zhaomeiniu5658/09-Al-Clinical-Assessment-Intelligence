import { defineStore } from 'pinia'
import { getMe, login, type User } from '../api/auth'
import { clearAccessToken, getAccessToken, saveAccessToken } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null
  }),
  getters: {
    isAuthenticated: () => Boolean(getAccessToken())
  },
  actions: {
    async login(username: string, password: string, remember = false) {
      const token = await login({ username, password, remember_me: remember })
      saveAccessToken(token.access_token, remember)
      this.user = await getMe()
    },
    async loadMe() {
      if (!getAccessToken()) return
      this.user = await getMe()
    },
    logout() {
      clearAccessToken()
      this.user = null
    }
  }
})

import axios from 'axios'

const accessTokenKey = 'access_token'

export function getAccessToken() {
  return localStorage.getItem(accessTokenKey) || sessionStorage.getItem(accessTokenKey)
}

export function saveAccessToken(token: string, remember: boolean) {
  if (remember) {
    localStorage.setItem(accessTokenKey, token)
    sessionStorage.removeItem(accessTokenKey)
    return
  }
  sessionStorage.setItem(accessTokenKey, token)
  localStorage.removeItem(accessTokenKey)
}

export function clearAccessToken() {
  localStorage.removeItem(accessTokenKey)
  sessionStorage.removeItem(accessTokenKey)
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000
})

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAccessToken()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)


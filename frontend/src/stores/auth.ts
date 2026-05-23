import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

interface User {
  id: number
  username: string
  email: string
  created_at: string
  virtual_money?: number
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const res: any = await api.auth.login({ username, password })
      token.value = res.access_token
      user.value = res.user
      localStorage.setItem('token', res.access_token)
      return res
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true
    try {
      const res: any = await api.auth.register({ username, email, password })
      token.value = res.access_token
      user.value = res.user
      localStorage.setItem('token', res.access_token)
      return res
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res: any = await api.auth.me()
      user.value = res
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, loading, isAuthenticated, login, register, fetchUser, logout }
})

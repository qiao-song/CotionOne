import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMe, login as loginApi, register as registerApi, logout as logoutApi } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  async function fetchUser() {
    try {
      loading.value = true
      const res = await getMe()
      user.value = res.data
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function login(data) {
    const res = await loginApi(data)
    user.value = res.data
    return res
  }

  async function register(data) {
    const res = await registerApi(data)
    user.value = res.data
    return res
  }

  async function logout() {
    try {
      await logoutApi()
    } catch {
      // ignore
    } finally {
      user.value = null
    }
  }

  function clearUser() {
    user.value = null
  }

  return { user, loading, isLoggedIn, fetchUser, login, register, logout, clearUser }
})

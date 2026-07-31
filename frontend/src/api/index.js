import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: '',
  timeout: 15000,
  withCredentials: true
})

api.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      // Use window.location to get the actual browser URL, not Vue Router's internal state
      // router.currentRoute is not updated during navigation guards, causing infinite redirect loops
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/register') {
        router.push(`/login?redirect=${encodeURIComponent(currentPath + window.location.search)}`)
      }
    }
    return Promise.reject(err.response?.data || { code: -1, msg: err.message, data: null })
  }
)

export default api

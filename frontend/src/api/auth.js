import api from './index'

export const sendCode = (phone) => api.post('/api/auth/send-code', { phone })
export const register = (data) => api.post('/api/auth/register', data)
export const login = (data) => api.post('/api/auth/login', data)
export const getMe = () => api.get('/api/auth/me')
export const logout = () => api.post('/api/auth/logout')

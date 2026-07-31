import api from './index'

export const getMyGoods = () => api.get('/api/user/goods')
export const updateProfile = (formData) => api.put('/api/user/profile', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const changePassword = (data) => api.put('/api/user/password', data)
export const getBalance = () => api.get('/api/user/balance')
export const earnPoints = (data) => api.post('/api/user/earn-points', data)

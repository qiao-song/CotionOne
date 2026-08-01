import api from './index'

export const getEmojis = (params) => api.get('/api/emojis', { params })
export const uploadEmoji = (formData) => api.post('/api/emojis', formData)
export const downloadEmoji = (id) => api.post(`/api/emojis/${id}/download`)

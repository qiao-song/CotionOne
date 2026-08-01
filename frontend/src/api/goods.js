import api from './index'

export const getGoodsList = (params) => api.get('/api/goods', { params })
export const createGoods = (formData) => api.post('/api/goods', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const updateGoods = (id, formData) => api.put(`/api/goods/${id}`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const deleteGoods = (id) => api.delete(`/api/goods/${id}`)
export const toggleGoodsStatus = (id) => api.put(`/api/goods/${id}/status`)
export const getGoodsDetail = (id) => api.get(`/api/goods/${id}`)
export const getDiscoverFeed = (params) => api.get('/api/discover', { params })
export const likeVideo = (id) => api.post(`/api/goods/${id}/like`)
export const shareVideo = (id) => api.post(`/api/goods/${id}/share`)
export const getTags = () => api.get('/api/goods/tags')

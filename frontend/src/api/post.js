import api from './index'

export const getPosts = (params) => api.get('/api/posts', { params })
export const createPost = (formData) => api.post('/api/posts', formData)
export const getPostDetail = (id) => api.get(`/api/posts/${id}`)

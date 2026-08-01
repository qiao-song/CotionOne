import api from './index'

export const getVideoComments = (goodsId, params) => api.get(`/api/video-comments/${goodsId}`, { params })
export const createVideoComment = (data) => api.post('/api/video-comments', data)

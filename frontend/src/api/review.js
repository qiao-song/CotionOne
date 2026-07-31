import api from './index'

export const createReview = (data) => api.post('/api/reviews', data)
export const getGoodsReviews = (goodsId, params) => api.get(`/api/reviews/goods/${goodsId}`, { params })

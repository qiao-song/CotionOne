import api from './index'

export const getSellerInfo = (id) => api.get(`/api/seller/${id}`)

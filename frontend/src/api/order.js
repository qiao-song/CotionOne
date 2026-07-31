import api from './index'

export const createOrder = (data) => api.post('/api/orders', data)
export const getOrders = (params) => api.get('/api/orders', { params })
export const getOrderDetail = (id) => api.get(`/api/orders/${id}`)
export const updateOrderStatus = (id, status) => api.put(`/api/orders/${id}/status`, { status })

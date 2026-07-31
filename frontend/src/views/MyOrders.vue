<template>
  <div class="orders-page">
    <h1 class="page-title">我的订单</h1>

    <div v-if="loading" class="loading-text">加载中...</div>
    <div v-else-if="orders.length === 0" class="empty">
      <p>还没有任何订单</p>
      <router-link to="/" class="btn-primary" style="display:inline-flex;align-items:center;justify-content:center;text-decoration:none;margin-top:16px;">
        去逛逛
      </router-link>
    </div>

    <div v-else class="order-list">
      <div v-for="order in orders" :key="order.id" class="order-card">
        <!-- Order header -->
        <div class="order-header">
          <span class="order-time">{{ order.created_at }}</span>
          <span :class="['order-status', `status-${order.status}`]">{{ statusMap[order.status] || order.status }}</span>
        </div>

        <!-- Order goods info -->
        <div class="order-body" @click="goToDetail(order.goods_id)">
          <div class="order-image">
            <img :src="order.goods_image || placeholderImage" :alt="order.goods_title" />
          </div>
          <div class="order-info">
            <div class="order-title">{{ order.goods_title }}</div>
            <div class="order-meta">
              <span class="order-price">¥{{ order.goods_price }}</span>
              <span class="order-qty">×{{ order.quantity }}</span>
            </div>
            <div class="order-total">实付：<strong>¥{{ order.total_amount }}</strong></div>
          </div>
        </div>

        <!-- Logistics (expandable) -->
        <div class="order-logistics">
          <div class="logistics-toggle" @click="toggleLogistics(order.id)">
            <span>📦 物流信息</span>
            <span class="toggle-arrow" :class="{ expanded: expandedLogistics[order.id] }">▼</span>
          </div>
          <div v-if="expandedLogistics[order.id]" class="logistics-timeline">
            <div v-if="!order.logistics || order.logistics.length === 0" class="no-logistics">
              暂无物流信息
            </div>
            <div v-for="(log, idx) in order.logistics" :key="idx" class="logistics-step">
              <div class="step-dot" :class="{ active: idx === 0 }"></div>
              <div class="step-line" v-if="idx < order.logistics.length - 1"></div>
              <div class="step-content">
                <div class="step-desc">{{ log.desc }}</div>
                <div class="step-meta">
                  <span>{{ log.location }}</span>
                  <span>{{ log.time }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="order-actions">
          <button
            v-if="order.status === 'shipped' || order.status === 'pending'"
            class="btn-primary btn-sm"
            @click="handleReceive(order.id)"
          >
            确认收货
          </button>
          <button
            v-if="order.status === 'received'"
            class="btn-outline btn-sm"
            @click="handleReturn(order.id)"
          >
            申请退货
          </button>
          <button
            v-if="order.status === 'received' && !order.has_review"
            class="btn-outline btn-sm"
            @click="showReviewForm(order)"
          >
            写评价
          </button>
          <span v-if="order.status === 'received' && order.has_review" class="reviewed-text">已评价</span>
        </div>
      </div>
    </div>

    <!-- Review modal -->
    <Teleport to="body">
      <div v-if="reviewModalOrder" class="modal-overlay" @click.self="reviewModalOrder = null">
        <div class="modal-content">
          <h3>写评价</h3>
          <div class="form-group">
            <label>评分</label>
            <div class="rating-stars">
              <span
                v-for="s in 5"
                :key="s"
                :class="['rating-star', { active: s <= reviewRating }]"
                @click="reviewRating = s"
              >★</span>
            </div>
          </div>
          <div class="form-group">
            <label>评价内容</label>
            <textarea v-model="reviewContent" rows="4" placeholder="分享你的使用体验..."></textarea>
          </div>
          <div class="form-actions">
            <button class="btn-outline" @click="reviewModalOrder = null">取消</button>
            <button class="btn-primary" @click="submitReview" :disabled="reviewSubmitting">
              {{ reviewSubmitting ? '提交中...' : '提交评价' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { getOrders, updateOrderStatus } from '../api/order'
import { createReview } from '../api/review'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const orders = ref([])
const loading = ref(true)
const expandedLogistics = ref({})

const statusMap = {
  pending: '待发货',
  shipped: '已发货',
  received: '已签收',
  returned: '已退货'
}

const placeholderImage = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="#F3F4F6"><rect width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="#9CA3AF" font-size="10">暂无</text></svg>'
)

// Review modal
const reviewModalOrder = ref(null)
const reviewRating = ref(5)
const reviewContent = ref('')
const reviewSubmitting = ref(false)

async function fetchOrders() {
  loading.value = true
  try {
    const res = await getOrders({ page: 1, page_size: 50 })
    orders.value = res.data.items || []
  } catch (e) {
    toast.error(e.msg || '加载失败')
  } finally {
    loading.value = false
  }
}

function toggleLogistics(orderId) {
  expandedLogistics.value[orderId] = !expandedLogistics.value[orderId]
}

function goToDetail(goodsId) {
  if (goodsId) {
    router.push(`/goods/${goodsId}`)
  }
}

async function handleReceive(orderId) {
  if (!confirm('确认已收到商品？')) return
  try {
    await updateOrderStatus(orderId, 'received')
    toast.success('已确认收货')
    await fetchOrders()
  } catch (e) {
    toast.error(e.msg || '操作失败')
  }
}

async function handleReturn(orderId) {
  if (!confirm('确定要申请退货吗？退款将退回您的账户余额。')) return
  try {
    await updateOrderStatus(orderId, 'returned')
    toast.success('退货成功，退款已退回')
    await authStore.fetchUser()
    await fetchOrders()
  } catch (e) {
    toast.error(e.msg || '操作失败')
  }
}

function showReviewForm(order) {
  reviewModalOrder.value = order
  reviewRating.value = 5
  reviewContent.value = ''
}

async function submitReview() {
  if (!reviewModalOrder.value) return
  reviewSubmitting.value = true
  try {
    await createReview({
      order_id: reviewModalOrder.value.id,
      goods_id: reviewModalOrder.value.goods_id,
      rating: reviewRating.value,
      content: reviewContent.value
    })
    toast.success('评价成功')
    reviewModalOrder.value = null
    await fetchOrders()
  } catch (e) {
    toast.error(e.msg || '评价失败')
  } finally {
    reviewSubmitting.value = false
  }
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.orders-page {
  padding-bottom: 40px;
}

.loading-text, .empty {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.order-card:hover {
  box-shadow: 0 12px 28px rgba(249, 115, 22, 0.08);
  border-color: rgba(249, 115, 22, 0.08);
  transform: translateY(-2px);
}

/* Order header */
.order-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--bg);
  border-bottom: 1px solid var(--border-light);
}

.order-time {
  font-size: 13px;
  color: var(--text-muted);
}

.order-status {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 4px;
}

.status-pending { background: linear-gradient(135deg, #FEF3C7, #FDE68A); color: #B45309; }
.status-shipped { background: linear-gradient(135deg, #DBEAFE, #BFDBFE); color: #1D4ED8; }
.status-received { background: linear-gradient(135deg, #D1FAE5, #A7F3D0); color: #047857; }
.status-returned { background: linear-gradient(135deg, #FEE2E2, #FECACA); color: #DC2626; }

/* Order body */
.order-body {
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  cursor: pointer;
  transition: background var(--transition);
}

.order-body:hover {
  background: #FAFAFA;
}

.order-image {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--border-light);
}

.order-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.order-info {
  flex: 1;
  min-width: 0;
}

.order-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 8px;
}

.order-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.order-price {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.order-qty {
  font-size: 13px;
  color: var(--text-muted);
}

.order-total {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 6px;
}

.order-total strong {
  color: var(--primary);
  font-size: 16px;
}

/* Logistics */
.order-logistics {
  border-top: 1px solid var(--border-light);
}

.logistics-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.logistics-toggle:hover {
  color: var(--primary);
}

.toggle-arrow {
  font-size: 12px;
  transition: transform 0.2s;
}

.toggle-arrow.expanded {
  transform: rotate(180deg);
}

.logistics-timeline {
  padding: 0 20px 16px 36px;
  position: relative;
}

.logistics-step {
  display: flex;
  gap: 16px;
  position: relative;
  padding-bottom: 16px;
}

.logistics-step:last-child {
  padding-bottom: 0;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border);
  flex-shrink: 0;
  margin-top: 4px;
  position: relative;
  z-index: 1;
}

.step-dot.active {
  background: var(--primary);
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.2);
}

.step-line {
  position: absolute;
  left: 24px;
  top: 18px;
  bottom: 0;
  width: 1px;
  background: var(--border);
}

.step-content {
  flex: 1;
}

.step-desc {
  font-size: 14px;
  color: var(--text);
  line-height: 1.4;
}

.step-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.no-logistics {
  font-size: 13px;
  color: var(--text-muted);
  padding: 8px 0;
}

/* Actions */
.order-actions {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-light);
  justify-content: flex-end;
}

.reviewed-text {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 36px;
}

/* Review modal */
.rating-stars {
  display: flex;
  gap: 8px;
}

.rating-star {
  font-size: 32px;
  color: #D1D5DB;
  cursor: pointer;
  transition: color 0.2s;
}

.rating-star.active {
  color: #F59E0B;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
</style>

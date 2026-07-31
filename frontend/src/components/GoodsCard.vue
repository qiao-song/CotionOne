<template>
  <div class="goods-card" @click="handleClick">
    <div class="card-image">
      <img
        :src="goods.images?.[0] || placeholderImage"
        :alt="goods.title"
      />
      <div class="card-badge" v-if="goods.sales_count > 0">
        已售 {{ goods.sales_count }}
      </div>
    </div>
    <div class="card-body">
      <div class="card-title">{{ goods.title }}</div>
      <div class="card-tags" v-if="goods.sales_count > 0 || goods.avg_rating">
        <span v-if="goods.sales_count > 0" class="tag tag-sales">月销 {{ goods.sales_count }}</span>
        <span v-if="goods.avg_rating" class="tag tag-rating">★ {{ goods.avg_rating }}</span>
      </div>
      <div class="card-price-row">
        <span class="card-price">¥{{ goods.price }}</span>
        <span class="card-shipping">包邮</span>
      </div>
      <div class="card-footer">
        <div class="seller-info">
          <img
            :src="goods.seller_avatar || '/static/default.png'"
            class="seller-avatar"
            alt="seller"
          />
          <span class="seller-name">{{ goods.seller_name }}</span>
        </div>
        <div class="card-actions">
          <button class="btn-cart btn-sm" @click.stop="handleAddToCart" title="加入购物车">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
          </button>
          <button class="btn-buy-card btn-sm" @click.stop="handleBuy">
            立即购买
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'
import { useToast } from '../composables/useToast'

const props = defineProps({
  goods: { type: Object, required: true }
})

const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const toast = useToast()

const placeholderImage = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="260" height="200" fill="#F3F4F6"><rect width="260" height="200"/><text x="130" y="105" text-anchor="middle" fill="#9CA3AF" font-size="14">暂无图片</text></svg>'
)

function handleClick() {
  router.push(`/goods/${props.goods.id}`)
}

function handleAddToCart(e) {
  e.stopPropagation()
  if (!authStore.isLoggedIn) {
    router.push(`/login?redirect=${encodeURIComponent(router.currentRoute.value.fullPath)}`)
    return
  }
  cartStore.addItem(props.goods, 1)
  toast.success('已加入购物车')
}

function handleBuy(e) {
  e.stopPropagation()
  if (!authStore.isLoggedIn) {
    router.push(`/login?redirect=${encodeURIComponent(router.currentRoute.value.fullPath)}`)
    return
  }
  cartStore.addItem(props.goods, 1)
  router.push('/cart')
}
</script>

<style scoped>
.goods-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  border: 1px solid transparent;
  position: relative;
}

.goods-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: var(--radius);
  background: linear-gradient(135deg, rgba(249,115,22,0.03), transparent 60%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 0;
}

.goods-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(249, 115, 22, 0.12), 0 8px 16px rgba(0,0,0,0.06);
  border-color: rgba(249, 115, 22, 0.12);
}

.goods-card:hover::before {
  opacity: 1;
}

.card-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: linear-gradient(135deg, #F9FAFB, #F3F4F6);
  position: relative;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.goods-card:hover .card-image img {
  transform: scale(1.08);
}

.card-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.92), rgba(220, 38, 38, 0.92));
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  letter-spacing: 0.5px;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
}

.card-body {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.45;
  min-height: 43px;
  transition: color 0.25s;
}

.goods-card:hover .card-title {
  color: var(--primary);
}

.card-tags {
  display: flex;
  gap: 6px;
  margin: 8px 0 4px;
}

.tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.tag-sales {
  background: linear-gradient(135deg, #FEF3C7, #FDE68A);
  color: #B45309;
}

.tag-rating {
  background: linear-gradient(135deg, #FEE2E2, #FECACA);
  color: #DC2626;
}

.card-price-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 10px 0 4px;
}

.card-price {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #EF4444, #F97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.card-shipping {
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-light);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.seller-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.seller-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-light);
  flex-shrink: 0;
  transition: border-color var(--transition);
}

.goods-card:hover .seller-avatar {
  border-color: var(--primary-light);
}

.seller-name {
  font-size: 13px;
  color: var(--text-secondary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.btn-cart {
  min-width: auto;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: #fff;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
}

.btn-cart:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: linear-gradient(135deg, rgba(249,115,22,0.08), rgba(249,115,22,0.02));
  transform: scale(1.08);
}

.btn-buy-card {
  min-width: auto;
  padding: 0 14px;
  height: 34px;
  font-size: 12px;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  background: var(--gradient-primary);
  color: #fff;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(249, 115, 22, 0.3);
}

.btn-buy-card:hover {
  background: linear-gradient(135deg, #FB923C, #F97316);
  box-shadow: 0 4px 14px rgba(249, 115, 22, 0.45);
  transform: translateY(-2px);
}
</style>

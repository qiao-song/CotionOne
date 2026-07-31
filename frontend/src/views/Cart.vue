<template>
  <div class="cart-page">
    <div class="cart-header">
      <h1 class="page-title">购物车</h1>
      <button v-if="cartStore.items.length > 0" class="btn-outline btn-sm" @click="handleClearCart">
        清空购物车
      </button>
    </div>

    <div v-if="cartStore.items.length === 0" class="empty-cart">
      <div class="empty-icon">🛒</div>
      <p>购物车是空的</p>
      <router-link to="/" class="btn-primary" style="display:inline-flex;align-items:center;justify-content:center;text-decoration:none;margin-top:16px;">
        去逛逛
      </router-link>
    </div>

    <template v-else>
      <!-- Select all bar -->
      <div class="select-all-bar">
        <label class="checkbox-label">
          <input type="checkbox" :checked="cartStore.isAllSelected" @change="cartStore.toggleSelectAll()" />
          <span>全选</span>
        </label>
      </div>

      <!-- Cart items -->
      <div class="cart-items">
        <div v-for="item in cartStore.items" :key="item.goods_id" class="cart-item">
          <div class="item-checkbox">
            <input type="checkbox" :checked="item.selected" @change="cartStore.toggleSelect(item.goods_id)" />
          </div>
          <div class="item-image" @click="goToDetail(item.goods_id)">
            <img :src="item.image || placeholderImage" :alt="item.title" />
          </div>
          <div class="item-info" @click="goToDetail(item.goods_id)">
            <div class="item-title">{{ item.title }}</div>
            <div class="item-seller" v-if="item.seller_name">{{ item.seller_name }}</div>
          </div>
          <div class="item-price">¥{{ item.price }}</div>
          <div class="item-qty">
            <button class="qty-btn" @click="cartStore.updateQty(item.goods_id, item.quantity - 1)" :disabled="item.quantity <= 1">−</button>
            <span class="qty-num">{{ item.quantity }}</span>
            <button class="qty-btn" @click="cartStore.updateQty(item.goods_id, item.quantity + 1)">+</button>
          </div>
          <div class="item-subtotal">¥{{ (parseFloat(item.price) * item.quantity).toFixed(2) }}</div>
          <button class="item-delete" @click="cartStore.removeItem(item.goods_id)">删除</button>
        </div>
      </div>

      <!-- Bottom checkout bar -->
      <div class="checkout-bar">
        <div class="checkout-left">
          <label class="checkbox-label">
            <input type="checkbox" :checked="cartStore.isAllSelected" @change="cartStore.toggleSelectAll()" />
            <span>全选</span>
          </label>
          <span class="checkout-count">已选 <strong>{{ cartStore.selectedCount }}</strong> 件</span>
        </div>
        <div class="checkout-right">
          <div class="checkout-total">
            合计：<span class="total-price">¥{{ cartStore.totalAmount.toFixed(2) }}</span>
          </div>
          <button
            class="btn-primary checkout-btn"
            :disabled="cartStore.selectedCount === 0 || checkingOut"
            @click="handleCheckout"
          >
            {{ checkingOut ? '结算中...' : `结算(${cartStore.selectedCount})` }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { createOrder } from '../api/order'

const router = useRouter()
const cartStore = useCartStore()
const authStore = useAuthStore()
const toast = useToast()

const checkingOut = ref(false)

const placeholderImage = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="#F3F4F6"><rect width="80" height="80"/><text x="40" y="45" text-anchor="middle" fill="#9CA3AF" font-size="10">暂无</text></svg>'
)

function goToDetail(goodsId) {
  router.push(`/goods/${goodsId}`)
}

async function handleCheckout() {
  if (cartStore.selectedCount === 0) return

  // Check balance first
  await authStore.fetchUser()
  const balance = parseFloat(authStore.user?.balance || 0)
  if (balance < cartStore.totalAmount) {
    toast.error(`余额不足！需要 ¥${cartStore.totalAmount.toFixed(2)}，当前余额 ¥${balance.toFixed(2)}`)
    return
  }

  if (!confirm(`确认支付 ¥${cartStore.totalAmount.toFixed(2)}？`)) return

  checkingOut.value = true
  try {
    const items = cartStore.selectedItems.map(i => ({
      goods_id: i.goods_id,
      quantity: i.quantity
    }))
    const res = await createOrder({ items })
    toast.success('下单成功！')
    cartStore.clearSelected()
    await authStore.fetchUser()
  } catch (e) {
    toast.error(e.msg || '下单失败')
  } finally {
    checkingOut.value = false
  }
}

async function handleClearCart() {
  if (!confirm('确定要清空购物车吗？')) return
  cartStore.clearCart()
  toast.success('购物车已清空')
}
</script>

<style scoped>
.cart-page {
  padding-bottom: 100px;
}

.cart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.cart-header .page-title {
  margin-bottom: 0;
}

.empty-cart {
  text-align: center;
  padding: 100px 0;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.empty-cart p {
  font-size: 17px;
  font-weight: 500;
}

.select-all-bar {
  background: var(--card-bg);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-light);
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text);
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--primary);
}

.cart-items {
  background: var(--card-bg);
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
  transition: background var(--transition);
}

.cart-item:last-child {
  border-bottom: none;
}

.cart-item:hover {
  background: linear-gradient(135deg, #FAFAFA, #FFF7ED);
}

.item-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--primary);
}

.item-image {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  flex-shrink: 0;
  background: var(--border-light);
}

.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.item-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-seller {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.item-price {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  min-width: 80px;
  text-align: center;
}

.item-qty {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid var(--border);
  border-radius: 4px;
  overflow: hidden;
}

.qty-btn {
  min-width: 32px;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background: #F9FAFB;
  color: var(--text);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qty-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.qty-btn:hover:not(:disabled) {
  background: var(--border-light);
}

.qty-num {
  min-width: 40px;
  text-align: center;
  font-size: 14px;
  color: var(--text);
}

.item-subtotal {
  font-size: 15px;
  font-weight: 700;
  color: var(--primary);
  min-width: 80px;
  text-align: center;
}

.item-delete {
  min-width: auto;
  padding: 4px 12px;
  height: auto;
  font-size: 13px;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
}

.item-delete:hover {
  color: #EF4444;
}

/* Checkout bar */
.checkout-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-top: 1px solid rgba(229, 231, 235, 0.6);
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 50;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.06);
}

.checkout-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.checkout-count {
  font-size: 14px;
  color: var(--text-secondary);
}

.checkout-count strong {
  color: var(--primary);
}

.checkout-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.checkout-total {
  font-size: 16px;
  color: var(--text);
}

.total-price {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #EF4444, #F97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.checkout-btn {
  min-width: 160px;
  height: 48px;
  font-size: 16px;
  font-weight: 700;
  border-radius: 24px;
  box-shadow: 0 4px 16px rgba(249, 115, 22, 0.35);
}

.checkout-btn:not(:disabled):hover {
  box-shadow: 0 6px 24px rgba(249, 115, 22, 0.5);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .cart-item {
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px;
  }
  .item-price, .item-subtotal {
    min-width: auto;
    font-size: 14px;
  }
  .checkout-bar {
    padding: 12px 16px;
    flex-direction: column;
    gap: 12px;
  }
  .checkout-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>

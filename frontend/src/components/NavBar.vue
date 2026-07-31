<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <div class="nav-left">
        <router-link to="/" class="logo">Tbao</router-link>
        <router-link to="/" class="nav-link" :class="{ active: $route.name === 'Home' }">
          商品广场
        </router-link>
        <router-link to="/discover" class="nav-link discover-link" :class="{ active: $route.name === 'Discover' }">
          发现
        </router-link>
        <router-link to="/my-shop" class="nav-link" :class="{ active: $route.name === 'MyShop' }">
          我的店铺
        </router-link>
        <router-link to="/cart" class="nav-link cart-link" :class="{ active: $route.name === 'Cart' }">
          购物车
          <span v-if="cartCount > 0" class="cart-badge">{{ cartCount > 99 ? '99+' : cartCount }}</span>
        </router-link>
        <router-link to="/my-orders" class="nav-link" :class="{ active: $route.name === 'MyOrders' }">
          我的订单
        </router-link>
        <router-link to="/profile" class="nav-link" :class="{ active: $route.name === 'Profile' }">
          个人中心
        </router-link>
      </div>
      <div class="nav-right">
        <template v-if="authStore.isLoggedIn">
          <div class="user-info">
            <img :src="authStore.user.avatar || '/static/default.png'" class="user-avatar" alt="avatar" />
            <span class="username">{{ authStore.user.username }}</span>
          </div>
          <button class="btn-outline btn-sm" @click="handleLogout">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-primary btn-sm" style="display:inline-flex;align-items:center;justify-content:center;text-decoration:none;min-width:80px;">
            登录
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const cartStore = useCartStore()
const router = useRouter()

const cartCount = computed(() => cartStore.cartCount)

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border-bottom: 1px solid rgba(229, 231, 235, 0.6);
  display: flex;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.04);
}

.navbar-inner {
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.logo {
  font-size: 26px;
  font-weight: 900;
  background: linear-gradient(135deg, #F97316 0%, #FBBF24 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-decoration: none;
  margin-right: 20px;
  letter-spacing: -1px;
  position: relative;
}
.logo::after {
  content: '';
  position: absolute;
  bottom: 2px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-warm);
  border-radius: 1px;
  transform: scaleX(0);
  transition: transform 0.3s ease;
  transform-origin: left;
}
.logo:hover::after {
  transform: scaleX(1);
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.25s ease;
  position: relative;
}

.nav-link:hover {
  color: var(--primary);
  background: linear-gradient(135deg, rgba(249,115,22,0.06), rgba(249,115,22,0.02));
}

.nav-link.active {
  color: var(--primary);
  background: linear-gradient(135deg, rgba(249,115,22,0.1), rgba(249,115,22,0.04));
  font-weight: 600;
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: var(--primary);
  border-radius: 2px;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px 4px 4px;
  border-radius: 24px;
  background: var(--bg);
  transition: all var(--transition);
}
.user-info:hover {
  background: var(--primary-light);
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--primary-light);
  transition: border-color var(--transition);
}
.user-info:hover .user-avatar {
  border-color: var(--primary);
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.cart-link {
  position: relative;
}

.cart-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: linear-gradient(135deg, #EF4444, #DC2626);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
  animation: badgePop 0.3s ease;
}

@keyframes badgePop {
  0% { transform: scale(0.5); }
  70% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.discover-link {
  position: relative;
}
.discover-link::before {
  content: 'NEW';
  position: absolute;
  top: -2px;
  right: 2px;
  font-size: 9px;
  font-weight: 700;
  color: #EF4444;
  letter-spacing: 0.5px;
}
</style>

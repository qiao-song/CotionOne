<template>
  <div class="home">
    <!-- Hero Banner -->
    <div class="hero-banner">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="hero-icon">🔥</span> 商品广场
          <span class="hero-subtitle">发现好物，开启品质生活</span>
        </h1>
        <div class="hero-stats" v-if="!loading && total > 0">
          <span class="hero-stat"><strong>{{ total }}</strong> 件商品</span>
          <span class="hero-stat-divider">·</span>
          <span class="hero-stat">品质保证</span>
          <span class="hero-stat-divider">·</span>
          <span class="hero-stat">极速发货</span>
        </div>
      </div>
      <div class="hero-decoration">
        <div class="hero-circle c1"></div>
        <div class="hero-circle c2"></div>
        <div class="hero-circle c3"></div>
      </div>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="loading" class="skeleton-grid">
      <div v-for="n in 8" :key="n" class="skeleton-card">
        <div class="skeleton skeleton-img"></div>
        <div class="skeleton skeleton-text" style="width:80%"></div>
        <div class="skeleton skeleton-text" style="width:50%"></div>
      </div>
    </div>

    <div v-else-if="items.length === 0" class="empty">
      <div class="empty-icon">📦</div>
      <h2>暂无商品</h2>
      <p>快去发布第一个商品吧！</p>
      <router-link to="/my-shop" class="btn-primary" style="display:inline-flex;align-items:center;justify-content:center;text-decoration:none;margin-top:16px;">
        发布商品
      </router-link>
    </div>
    <div v-else class="goods-grid">
      <GoodsCard v-for="item in items" :key="item.id" :goods="item" />
    </div>
    <div v-if="hasMore" class="load-more">
      <button class="btn-outline load-more-btn" @click="loadMore" :disabled="loadingMore">
        <span v-if="loadingMore" class="loading-spinner"></span>
        {{ loadingMore ? '加载中...' : '加载更多商品' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useToast } from '../composables/useToast'
import { getGoodsList } from '../api/goods'
import GoodsCard from '../components/GoodsCard.vue'

const toast = useToast()

const items = ref([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const pageSize = 20

const hasMore = computed(() => items.value.length < total.value)

async function fetchGoods(p = 1, append = false) {
  try {
    if (append) loadingMore.value = true
    else loading.value = true

    const res = await getGoodsList({ page: p, page_size: pageSize })
    if (append) {
      items.value.push(...res.data.items)
    } else {
      items.value = res.data.items
    }
    total.value = res.data.total
    page.value = p
  } catch (e) {
    toast.error(e.msg || '加载失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  fetchGoods(page.value + 1, true)
}

onMounted(() => {
  fetchGoods()
})
</script>

<style scoped>
.home {
  padding-bottom: 40px;
}

/* Hero Banner */
.hero-banner {
  position: relative;
  background: linear-gradient(135deg, #FFF7ED 0%, #FFFFFF 40%, #FFFBEB 100%);
  border-radius: 20px;
  padding: 32px 36px;
  margin-bottom: 28px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(249, 115, 22, 0.06);
  border: 1px solid rgba(249, 115, 22, 0.08);
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 28px;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 10px;
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-icon {
  font-size: 30px;
}

.hero-subtitle {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-muted);
  letter-spacing: 0;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.hero-stat strong {
  color: var(--primary);
  font-size: 16px;
  font-weight: 700;
}

.hero-stat-divider {
  color: var(--border);
}

/* Hero decoration */
.hero-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.hero-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}

.hero-circle.c1 {
  width: 200px;
  height: 200px;
  background: var(--primary);
  top: -60px;
  right: -40px;
}

.hero-circle.c2 {
  width: 120px;
  height: 120px;
  background: #FBBF24;
  top: 30px;
  right: 100px;
}

.hero-circle.c3 {
  width: 80px;
  height: 80px;
  background: var(--primary);
  bottom: -20px;
  right: 200px;
}

/* Skeleton loading */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}

.skeleton-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 0 0 16px;
  overflow: hidden;
}

.skeleton-img {
  width: 100%;
  height: 200px;
  border-radius: 0;
}

.skeleton-text {
  height: 16px;
  margin: 12px 16px 0;
  border-radius: 6px;
}

.goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}

.loading-text, .empty {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 16px;
}

.empty h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.empty p {
  font-size: 14px;
  color: var(--text-muted);
}

.load-more {
  text-align: center;
  margin-top: 36px;
}

.load-more-btn {
  min-width: 180px;
  height: 46px;
  border-radius: 23px;
  font-size: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.load-more-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: linear-gradient(135deg, rgba(249,115,22,0.04), rgba(249,115,22,0.01));
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(249,115,22,0.1);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

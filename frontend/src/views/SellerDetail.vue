<template>
  <div class="seller-page" v-if="seller">
    <!-- Breadcrumb -->
    <div class="breadcrumb">
      <router-link to="/">商品广场</router-link>
      <span class="sep">/</span>
      <span>{{ seller.username }} 的店铺</span>
    </div>

    <!-- Seller Profile Banner -->
    <div class="seller-banner">
      <div class="banner-bg"></div>
      <div class="banner-content">
        <div class="seller-avatar-wrap">
          <img :src="seller.avatar || '/static/default.png'" :alt="seller.username" class="seller-avatar" />
          <div class="avatar-ring"></div>
        </div>
        <div class="seller-info">
          <h1 class="seller-name">{{ seller.username }}</h1>
          <div class="seller-meta">
            <span class="meta-item" title="注册时间">
              <span class="meta-icon">📅</span> 注册时间 {{ seller.created_at }}
            </span>
            <span class="meta-item" title="入驻时间">
              <span class="meta-icon">🏪</span> 入驻Tbao {{ seller.created_at }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-num">{{ seller.sold_count }}</div>
        <div class="stat-label">售出订单</div>
        <div class="stat-sub" v-if="seller.returned_count > 0">含退货 {{ seller.returned_count }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🛒</div>
        <div class="stat-num">{{ seller.goods_count }}</div>
        <div class="stat-label">在售商品</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-num">{{ seller.avg_rating }}</div>
        <div class="stat-label">店铺评分</div>
        <div class="stat-sub" v-if="seller.review_count > 0">{{ seller.review_count }} 条评价</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">💳</div>
        <div class="stat-num">¥{{ parseFloat(seller.total_spent || 0).toFixed(2) }}</div>
        <div class="stat-label">累计消费</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📋</div>
        <div class="stat-num">{{ seller.total_orders || 0 }}</div>
        <div class="stat-label">累计下单</div>
      </div>
    </div>

    <!-- Goods Grid -->
    <div class="goods-section">
      <h2 class="section-title">
        <span class="title-icon">🛍️</span> 全部商品
        <span class="title-count">（{{ seller.goods_count }}件）</span>
      </h2>
      <div v-if="seller.goods && seller.goods.length > 0" class="goods-grid">
        <GoodsCard v-for="item in seller.goods" :key="item.id" :goods="item" />
      </div>
      <div v-else class="empty-goods">
        <div class="empty-icon">📭</div>
        <p>该卖家暂未发布商品</p>
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="loading-text">加载中...</div>
  <div v-else class="empty">卖家不存在</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '../composables/useToast'
import { getSellerInfo } from '../api/seller'
import GoodsCard from '../components/GoodsCard.vue'

const route = useRoute()
const toast = useToast()

const seller = ref(null)
const loading = ref(true)

async function fetchSeller() {
  loading.value = true
  try {
    const res = await getSellerInfo(route.params.id)
    seller.value = res.data
    document.title = `${res.data.username} 的店铺 - Tbao`
  } catch (e) {
    toast.error(e.msg || '加载失败')
    seller.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSeller()
})
</script>

<style scoped>
.seller-page {
  padding-bottom: 40px;
}

.breadcrumb {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 20px;
}
.breadcrumb a { color: var(--text-secondary); }
.breadcrumb a:hover { color: var(--primary); }
.breadcrumb .sep { margin: 0 8px; }

/* Banner */
.seller-banner {
  position: relative;
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 24px;
  background: var(--card-bg);
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}
.banner-bg {
  height: 100px;
  background: linear-gradient(135deg, #F97316 0%, #EA580C 30%, #FBBF24 70%, #F97316 100%);
  background-size: 200% 200%;
  animation: bannerShimmer 4s ease-in-out infinite;
}
@keyframes bannerShimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
.banner-content {
  display: flex;
  align-items: flex-end;
  gap: 24px;
  padding: 0 28px 24px;
  margin-top: -48px;
  position: relative;
  z-index: 1;
}
.seller-avatar-wrap {
  position: relative;
  flex-shrink: 0;
}
.seller-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  position: relative;
  z-index: 1;
}
.avatar-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #F97316, #FBBF24, #F97316);
  animation: ringSpin 3s linear infinite;
  opacity: 0.6;
}
@keyframes ringSpin {
  to { transform: rotate(360deg); }
}
.seller-info { padding-bottom: 6px; }
.seller-name {
  font-size: 26px;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}
.seller-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.meta-item {
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}
.meta-icon { font-size: 14px; }

/* Stats Row */
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
@media (max-width: 1024px) {
  .stats-row { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .stats-row { grid-template-columns: 1fr; }
}
.stat-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  transition: all 0.3s ease;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #F97316, #FBBF24);
  opacity: 0;
  transition: opacity 0.3s;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(249, 115, 22, 0.1);
  border-color: rgba(249, 115, 22, 0.15);
}
.stat-card:hover::before { opacity: 1; }
.stat-icon { font-size: 28px; margin-bottom: 8px; }
.stat-num {
  font-size: 32px;
  font-weight: 800;
  color: var(--primary);
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
.stat-sub {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* Goods Section */
.goods-section { margin-top: 8px; }
.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.title-icon { font-size: 22px; }
.title-count {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
}
.goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}
.empty-goods {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-goods p { font-size: 15px; }

.loading-text, .empty {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
  font-size: 16px;
}
</style>

<template>
  <div class="product-detail" v-if="goods">
    <!-- Breadcrumb -->
    <div class="breadcrumb">
      <router-link to="/">商品广场</router-link>
      <span class="sep">/</span>
      <span>{{ goods.title }}</span>
    </div>

    <!-- Main product section -->
    <div class="product-main">
      <!-- Image gallery -->
      <div class="product-gallery">
        <div class="main-image">
          <img :src="currentImage || placeholderImage" :alt="goods.title" />
        </div>
        <div class="thumbnail-strip" v-if="goods.images && goods.images.length > 1">
          <div
            v-for="(img, idx) in goods.images"
            :key="idx"
            :class="['thumb', { active: currentImage === img }]"
            @click="currentImage = img"
          >
            <img :src="img" alt="" />
          </div>
        </div>
      </div>

      <!-- Product info -->
      <div class="product-info">
        <h1 class="product-title">{{ goods.title }}</h1>
        <div class="product-price">¥{{ goods.price }}</div>

        <!-- Stats row -->
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ goods.sales_count || 0 }}</span>
            <span class="stat-label">月销量</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ goods.review_count || 0 }}</span>
            <span class="stat-label">评价数</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ goods.avg_rating || 0 }}</span>
            <span class="stat-label">评分</span>
          </div>
        </div>

        <!-- Tags -->
        <div class="product-tags" v-if="goods.tags && goods.tags.length > 0">
          <span v-for="tag in goods.tags" :key="tag" class="product-tag" @click="handleTagClick(tag)">{{ tag }}</span>
        </div>

        <!-- Seller info -->
        <div class="seller-card" @click="goToSeller(goods.seller_id)">
          <img :src="goods.seller_avatar || '/static/default.png'" class="seller-avatar" alt="seller" />
          <span class="seller-name">{{ goods.seller_name }}</span>
          <span class="seller-arrow">›</span>
        </div>

        <!-- Description -->
        <div class="product-desc" v-if="goods.description">
          <h3>商品描述</h3>
          <p>{{ goods.description }}</p>
        </div>

        <!-- Quantity selector + action buttons -->
        <div class="action-row">
          <div class="qty-selector">
            <button @click="qty = Math.max(1, qty - 1)">−</button>
            <span>{{ qty }}</span>
            <button @click="qty = Math.min(99, qty + 1)">+</button>
          </div>
        </div>
        <div class="action-buttons">
          <button class="btn-primary btn-lg" @click="handleAddToCart">加入购物车</button>
          <button class="btn-buy btn-lg" @click="handleBuyNow">立即购买</button>
        </div>
        <div class="action-buttons" v-if="!authStore.isLoggedIn">
          <p class="login-tip">
            <router-link :to="`/login?redirect=${encodeURIComponent($route.fullPath)}`">登录</router-link>
            后即可购买
          </p>
        </div>
      </div>
    </div>

    <!-- Price history chart -->
    <div class="card price-chart-section">
      <h3 class="section-title">价格走势</h3>
      <div class="chart-container">
        <svg :viewBox="`0 0 ${chartWidth} 200`" class="price-chart">
          <!-- Grid lines -->
          <line v-for="(_, i) in 5" :key="'grid-' + i" :x1="0" :y1="i * 40" :x2="chartWidth" :y2="i * 40" stroke="#F3F4F6" stroke-width="1" />
          <!-- Area fill -->
          <polygon :points="areaPoints" fill="rgba(249, 115, 22, 0.1)" />
          <!-- Line -->
          <polyline :points="linePoints" fill="none" stroke="#F97316" stroke-width="2.5" stroke-linejoin="round" />
          <!-- Dots -->
          <circle v-for="(pt, i) in chartPoints" :key="'dot-' + i" :cx="pt.x" :cy="pt.y" r="4" fill="#F97316" stroke="#fff" stroke-width="2" />
          <!-- Labels -->
          <text v-for="(pt, i) in chartPoints" :key="'label-' + i" :x="pt.x" :y="190" text-anchor="middle" font-size="11" fill="#9CA3AF">{{ pt.label }}</text>
        </svg>
      </div>
    </div>

    <!-- Reviews section -->
    <div id="reviews" class="card reviews-section">
      <h3 class="section-title">
        商品评价
        <span class="review-count">（{{ reviewTotal }}条）</span>
        <span class="review-avg">平均 {{ avgRating }} 分</span>
      </h3>

      <!-- Review form (anyone logged in can review) -->
      <div class="review-form" v-if="authStore.isLoggedIn">
        <div class="review-form-header">
          <span class="review-form-title">写评价</span>
        </div>
        <div class="review-form-body">
          <div class="rating-select">
            <span class="rating-label">评分：</span>
            <button
              v-for="s in 5"
              :key="s"
              :class="['star-btn', { active: reviewRating >= s }]"
              @click="reviewRating = s"
            >★</button>
          </div>
          <textarea
            v-model="reviewContent"
            class="review-textarea"
            placeholder="分享你的使用感受..."
            maxlength="500"
          ></textarea>
          <button
            class="btn-primary btn-sm"
            @click="submitReview"
            :disabled="submittingReview || !reviewContent.trim()"
          >
            {{ submittingReview ? '提交中...' : '发表评价' }}
          </button>
        </div>
      </div>
      <div class="review-form" v-else>
        <p class="review-login-hint">
          <router-link :to="`/login?redirect=${encodeURIComponent($route.fullPath)}`">登录</router-link> 后即可评价
        </p>
      </div>

      <div v-if="loadingReviews" class="loading-text">加载中...</div>
      <div v-else-if="reviews.length === 0" class="no-reviews">
        <div class="no-review-icon">📝</div>
        <p>暂无评价，成为第一个评价的人吧！</p>
      </div>
      <div v-else class="review-list">
        <div v-for="r in reviews" :key="r.id" class="review-item">
          <div class="review-header">
            <img
              :src="r.user_avatar || '/static/default.png'"
              class="review-avatar"
              alt=""
              @click="goToSeller(r.user_id)"
            />
            <span class="review-username" @click="goToSeller(r.user_id)">{{ r.username }}</span>
            <span v-if="r.purchase" class="purchase-badge" title="已购买">
              已购 {{ r.purchase.quantity }}件 · ¥{{ parseFloat(r.purchase.goods_price).toFixed(2) }}
            </span>
            <div class="review-stars">
              <span v-for="s in 5" :key="s" :class="['star', { filled: s <= r.rating }]">★</span>
            </div>
            <span class="review-date">{{ r.created_at }}</span>
          </div>
          <p class="review-content" v-if="r.content">{{ r.content }}</p>
        </div>
      </div>
      <div v-if="reviewHasMore" class="load-more">
        <button class="btn-outline" @click="loadMoreReviews" :disabled="loadingMoreReviews">
          {{ loadingMoreReviews ? '加载中...' : '加载更多评价' }}
        </button>
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="loading-text">加载中...</div>
  <div v-else class="empty">商品不存在或已下架</div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useCartStore } from '../stores/cart'
import { useToast } from '../composables/useToast'
import { getGoodsDetail } from '../api/goods'
import { getGoodsReviews, createReview } from '../api/review'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const toast = useToast()

const goods = ref(null)
const loading = ref(true)
const qty = ref(1)
const currentImage = ref('')

// Reviews
const reviews = ref([])
const reviewPage = ref(1)
const reviewTotal = ref(0)
const avgRating = ref(0)
const loadingReviews = ref(false)
const loadingMoreReviews = ref(false)
const reviewHasMore = computed(() => reviews.value.length < reviewTotal.value)

// Review form
const reviewRating = ref(5)
const reviewContent = ref('')
const submittingReview = ref(false)

async function submitReview() {
  if (!reviewContent.value.trim() || submittingReview.value) return
  submittingReview.value = true
  try {
    await createReview({
      goods_id: parseInt(route.params.id),
      rating: reviewRating.value,
      content: reviewContent.value.trim()
    })
    toast.success('评价发表成功')
    reviewContent.value = ''
    reviewRating.value = 5
    // Refresh reviews
    await fetchReviews(1)
  } catch (e) {
    toast.error(e.msg || '评价失败')
  } finally {
    submittingReview.value = false
  }
}

const placeholderImage = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" fill="#F3F4F6"><rect width="400" height="400"/><text x="200" y="205" text-anchor="middle" fill="#9CA3AF" font-size="16">暂无图片</text></svg>'
)

// Chart
const chartWidth = 600
const chartPoints = computed(() => {
  const history = goods.value?.price_history || []
  if (history.length === 0) return []
  const prices = history.map(h => h.price)
  const maxPrice = Math.max(...prices)
  const minPrice = Math.min(...prices)
  const range = maxPrice - minPrice || 1
  const padding = 30
  const chartH = 160
  const stepX = (chartWidth - padding * 2) / Math.max(1, history.length - 1)

  return history.map((h, i) => ({
    x: padding + i * stepX,
    y: padding + chartH - ((h.price - minPrice) / range) * chartH,
    label: h.date
  }))
})

const linePoints = computed(() => chartPoints.value.map(p => `${p.x},${p.y}`).join(' '))
const areaPoints = computed(() => {
  const pts = chartPoints.value
  if (pts.length === 0) return ''
  const first = pts[0]
  const last = pts[pts.length - 1]
  const bottom = 190
  return `${first.x},${bottom} ${pts.map(p => `${p.x},${p.y}`).join(' ')} ${last.x},${bottom}`
})

async function fetchGoods() {
  loading.value = true
  try {
    const res = await getGoodsDetail(route.params.id)
    goods.value = res.data
    currentImage.value = res.data.images?.[0] || ''
    document.title = `${res.data.title} - Tbao`
  } catch (e) {
    toast.error(e.msg || '加载失败')
  } finally {
    loading.value = false
  }
}

async function fetchReviews(page = 1, append = false) {
  if (append) loadingMoreReviews.value = true
  else loadingReviews.value = true
  try {
    const res = await getGoodsReviews(route.params.id, { page, page_size: 10 })
    if (append) {
      reviews.value.push(...res.data.items)
    } else {
      reviews.value = res.data.items
    }
    reviewTotal.value = res.data.total
    avgRating.value = res.data.avg_rating
    reviewPage.value = page
  } catch {
    // silent
  } finally {
    loadingReviews.value = false
    loadingMoreReviews.value = false
  }
}

function loadMoreReviews() {
  fetchReviews(reviewPage.value + 1, true)
}

function handleAddToCart() {
  if (!authStore.isLoggedIn) {
    router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    return
  }
  if (!goods.value) return
  cartStore.addItem(goods.value, qty.value)
  toast.success('已加入购物车')
  qty.value = 1
}

function handleBuyNow() {
  if (!authStore.isLoggedIn) {
    router.push(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    return
  }
  if (!goods.value) return
  cartStore.addItem(goods.value, qty.value)
  router.push('/cart')
}

function goToSeller(sellerId) {
  if (!sellerId) return
  router.push(`/seller/${sellerId}`)
}

function handleTagClick(tag) {
  router.push(`/?tag=${encodeURIComponent(tag)}`)
}

function scrollToReviews() {
  nextTick(() => {
    const el = document.getElementById('reviews')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

onMounted(async () => {
  await fetchGoods()
  await fetchReviews()

  // Check if navigated from Discover's comment button or URL hash
  if (route.query.tab === 'reviews' || route.hash === '#reviews') {
    // Small delay to ensure DOM is fully rendered
    setTimeout(scrollToReviews, 300)
  }
})

// Refetch when route param changes
watch(() => route.params.id, async () => {
  await fetchGoods()
  await fetchReviews()
  if (route.query.tab === 'reviews') {
    setTimeout(scrollToReviews, 300)
  }
})
</script>

<style scoped>
.product-detail {
  padding-bottom: 40px;
  animation: detailFadeIn 0.4s ease;
}

@keyframes detailFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.breadcrumb {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 20px;
}

.breadcrumb a {
  color: var(--text-secondary);
  transition: color var(--transition);
}

.breadcrumb a:hover {
  color: var(--primary);
}

.breadcrumb .sep {
  margin: 0 8px;
}

/* Main section */
.product-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
  margin-bottom: 32px;
}

@media (max-width: 768px) {
  .product-main {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

/* Gallery */
.product-gallery {
  position: sticky;
  top: 80px;
}

.main-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: var(--radius);
  overflow: hidden;
  background: linear-gradient(135deg, #F9FAFB, #F3F4F6);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
  position: relative;
}

.main-image::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(249,115,22,0.02), transparent);
  pointer-events: none;
}

.main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.main-image:hover img {
  transform: scale(1.02);
}

.thumbnail-strip {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.thumb {
  width: 68px;
  height: 68px;
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.25s ease;
  background: var(--border-light);
  position: relative;
}

.thumb:hover {
  border-color: rgba(249,115,22,0.3);
  transform: translateY(-2px);
}

.thumb.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(249,115,22,0.15);
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Product info */
.product-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.4;
  margin-bottom: 16px;
  letter-spacing: -0.3px;
}

.product-price {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #EF4444, #F97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  letter-spacing: -1px;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px;
  background: linear-gradient(135deg, #FFF7ED, #FFFFFF, #FFFBEB);
  border-radius: 12px;
  margin-bottom: 20px;
  border: 1px solid rgba(249,115,22,0.06);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.stat-divider {
  width: 1px;
  height: 30px;
  background: linear-gradient(180deg, transparent, var(--border), transparent);
}

/* Product tags */
.product-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.product-tag {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1.5px solid var(--border);
  background: #fff;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.product-tag:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: linear-gradient(135deg, #FFF7ED, #FFEDD5);
}

.seller-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  margin-bottom: 20px;
  cursor: pointer;
  transition: all var(--transition);
  border: 1px solid transparent;
}

.seller-card:hover {
  background: linear-gradient(135deg, rgba(249,115,22,0.04), rgba(249,115,22,0.01));
  border-color: rgba(249,115,22,0.15);
  transform: translateX(4px);
}

.seller-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.seller-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text);
  flex: 1;
}

.seller-arrow {
  font-size: 22px;
  color: var(--text-muted);
  transition: all var(--transition);
}

.seller-card:hover .seller-arrow {
  color: var(--primary);
  transform: translateX(2px);
}

.product-desc {
  margin-bottom: 20px;
}

.product-desc h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text);
}

.product-desc p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
}

/* Actions */
.action-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.qty-selector {
  display: flex;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.qty-selector button {
  min-width: 36px;
  width: 36px;
  height: 40px;
  padding: 0;
  border: none;
  background: #F9FAFB;
  font-size: 18px;
  color: var(--text);
}

.qty-selector button:hover {
  background: var(--border-light);
}

.qty-selector span {
  min-width: 50px;
  text-align: center;
  font-size: 15px;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.btn-lg {
  flex: 1;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  min-width: auto;
  border-radius: 24px;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.btn-primary.btn-lg {
  background: linear-gradient(135deg, #F97316 0%, #EA580C 100%);
  border: none;
  color: #fff;
  box-shadow: 0 4px 14px rgba(249, 115, 22, 0.35);
  animation: ctaPulse 2s ease-in-out infinite;
}

.btn-primary.btn-lg:hover {
  background: linear-gradient(135deg, #FB923C 0%, #F97316 100%);
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.5);
  transform: translateY(-2px);
  animation: none;
}

.btn-buy {
  background: #fff;
  border: 2px solid var(--primary);
  color: var(--primary);
  height: 48px;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.btn-buy::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #FFF7ED, #FFEDD5);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-buy:hover {
  border-color: #EA580C;
  color: #EA580C;
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.18);
  transform: translateY(-2px);
}

.btn-buy:hover::before {
  opacity: 1;
}

.btn-buy span { position: relative; z-index: 1; }

.login-tip {
  text-align: center;
  width: 100%;
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 12px;
}

.login-tip a {
  color: var(--primary);
  font-weight: 500;
}

/* Price chart section */
.price-chart-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
}

.chart-container {
  width: 100%;
  overflow-x: auto;
}

.price-chart {
  width: 100%;
  max-width: 600px;
  height: auto;
}

/* Reviews */
.reviews-section {
  margin-bottom: 24px;
}

.review-count {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
}

.review-avg {
  font-size: 14px;
  font-weight: 400;
  color: var(--primary);
  margin-left: 12px;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.review-item {
  padding: 16px 0;
  border-bottom: 1px solid var(--border-light);
}

.review-item:last-child {
  border-bottom: none;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.review-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
  border: 2px solid transparent;
}

.review-avatar:hover {
  transform: scale(1.15);
  border-color: var(--primary);
}

.review-username {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  transition: color 0.2s;
}

.review-username:hover {
  color: var(--primary);
}

.purchase-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-light);
  padding: 2px 10px;
  border-radius: 10px;
  white-space: nowrap;
}

.review-stars {
  display: flex;
  gap: 2px;
}

.star {
  font-size: 14px;
  color: #D1D5DB;
}

.star.filled {
  color: #F59E0B;
}

.review-date {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: auto;
}

.review-content {
  margin-top: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-left: 42px;
}

.no-reviews {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 14px;
}

.no-review-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.review-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
  opacity: 0.7;
}

/* Review Form */
.review-form {
  padding: 18px;
  margin-bottom: 16px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}

.review-form-header {
  margin-bottom: 12px;
}

.review-form-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.rating-select {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
}

.rating-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-right: 4px;
}

.star-btn {
  min-width: auto;
  padding: 0;
  width: 32px;
  height: 32px;
  font-size: 24px;
  background: none;
  border: none;
  color: #D1D5DB;
  cursor: pointer;
  transition: all 0.15s ease;
}

.star-btn:hover {
  color: #F59E0B;
  transform: scale(1.15);
}

.star-btn.active {
  color: #F59E0B;
}

.review-textarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  margin-bottom: 12px;
  resize: vertical;
  font-family: inherit;
  background: var(--card-bg);
  color: var(--text);
}

.review-textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
  outline: none;
}

.review-login-hint {
  text-align: center;
  font-size: 14px;
  color: var(--text-muted);
  margin: 8px 0;
}

.review-login-hint a {
  color: var(--primary);
  font-weight: 500;
}

.loading-text, .empty {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}
</style>

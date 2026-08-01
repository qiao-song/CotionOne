<template>
  <div class="home">
    <!-- Hero Banner -->
    <div class="hero-banner">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="hero-icon">🔥</span> 商品广场
          <span class="hero-subtitle">发现好物，开启品质生活</span>
        </h1>
      </div>
      <div class="hero-decoration">
        <div class="hero-circle c1"></div>
        <div class="hero-circle c2"></div>
        <div class="hero-circle c3"></div>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="search-section">
      <div class="search-bar">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索商品、店铺..."
          @keyup.enter="handleSearch"
        />
        <button v-if="searchKeyword" class="search-clear" @click="searchKeyword = ''; handleSearch()">×</button>
        <button class="search-btn" @click="handleSearch">搜索</button>
      </div>

      <!-- Search Tabs -->
      <div class="search-tabs">
        <button :class="['search-tab', { active: searchTab === 'goods' }]" @click="switchTab('goods')">
          📦 商品 <span class="tab-count" v-if="searchTab === 'goods' && total">({{ total }})</span>
        </button>
        <button :class="['search-tab', { active: searchTab === 'seller' }]" @click="switchTab('seller')">
          🏪 店铺
        </button>
        <button :class="['search-tab', { active: searchTab === 'filter' }]" @click="switchTab('filter')">
          ⚙️ 筛选
          <span class="filter-has" v-if="hasActiveFilters">●</span>
        </button>
      </div>

      <!-- Filter Panel -->
      <div v-if="searchTab === 'filter'" class="filter-panel">
        <div class="filter-row">
          <div class="filter-group">
            <label>发布时间</label>
            <select v-model="filterDate" class="filter-select" @change="applyFilters">
              <option value="">不限</option>
              <option value="7">近7天</option>
              <option value="30">近30天</option>
              <option value="90">近3个月</option>
            </select>
          </div>
          <div class="filter-group">
            <label>排序方式</label>
            <select v-model="filterSort" class="filter-select" @change="applyFilters">
              <option value="newest">最新发布</option>
              <option value="random">随机推荐</option>
              <option value="price_asc">价格从低到高</option>
              <option value="price_desc">价格从高到低</option>
            </select>
          </div>
        </div>
        <div class="filter-row">
          <div class="filter-group">
            <label>价格区间</label>
            <div class="price-range">
              <input v-model="filterPriceMin" type="number" placeholder="最低价" class="price-input" @keyup.enter="applyFilters" />
              <span class="price-sep">—</span>
              <input v-model="filterPriceMax" type="number" placeholder="最高价" class="price-input" @keyup.enter="applyFilters" />
            </div>
          </div>
          <div class="filter-group">
            <label>标签筛选</label>
            <select v-model="filterTag" class="filter-select" @change="applyFilters">
              <option value="">全部标签</option>
              <option v-for="t in allTags" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
        </div>
        <div class="filter-actions">
          <button class="btn-outline btn-sm" @click="resetFilters">重置筛选</button>
          <button class="btn-primary btn-sm" @click="applyFilters">应用筛选</button>
        </div>
      </div>

      <!-- Seller Results -->
      <div v-if="searchTab === 'seller'" class="seller-results">
        <div v-if="sellerLoading" class="loading-text">搜索中...</div>
        <div v-else-if="sellerResults.length === 0" class="empty-small">
          <p v-if="searchKeyword">未找到相关店铺</p>
          <p v-else>请输入店铺名称搜索</p>
        </div>
        <div v-else class="seller-list">
          <div v-for="s in sellerResults" :key="s.id" class="seller-result-item" @click="goToSeller(s.id)">
            <img :src="s.avatar || '/static/default.png'" class="s-avatar" />
            <div class="s-info">
              <div class="s-name">{{ s.username }}</div>
              <div class="s-meta">{{ s.goods_count || 0 }} 件在售</div>
            </div>
            <span class="s-arrow">›</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Header -->
    <div class="results-header" v-if="searchTab === 'goods' && (searchKeyword || filterTag)">
      <div class="results-info">
        <span v-if="searchKeyword">搜索 "<strong>{{ searchKeyword }}</strong>"</span>
        <span v-if="filterTag">标签 "<strong>{{ filterTag }}</strong>"</span>
        <span class="results-total" v-if="!loading">共 {{ total }} 件</span>
      </div>
      <button v-if="searchKeyword || filterTag || filterSort !== 'newest'" class="btn-outline btn-sm" @click="resetAll">清除全部</button>
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
      <h2 v-if="searchKeyword || filterTag">未找到相关商品</h2>
      <h2 v-else>暂无商品</h2>
      <p v-if="searchKeyword || filterTag">试试其他关键词或筛选条件</p>
      <p v-else>快去发布第一个商品吧！</p>
      <button v-if="searchKeyword || filterTag" class="btn-outline" @click="resetAll" style="margin-top:16px;">清除筛选</button>
      <router-link v-else to="/my-shop" class="btn-primary" style="display:inline-flex;align-items:center;justify-content:center;text-decoration:none;margin-top:16px;">
        发布商品
      </router-link>
    </div>
    <template v-else>
      <div class="goods-grid">
        <GoodsCard v-for="item in items" :key="item.id" :goods="item" />
      </div>
      <div v-if="hasMore" class="load-more">
        <button class="btn-outline load-more-btn" @click="loadMore" :disabled="loadingMore">
          <span v-if="loadingMore" class="loading-spinner"></span>
          {{ loadingMore ? '加载中...' : '加载更多商品' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { getGoodsList, getTags } from '../api/goods'
import { getSellerInfo } from '../api/seller'
import api from '../api/index'
import GoodsCard from '../components/GoodsCard.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const items = ref([])
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const loadingMore = ref(false)
const pageSize = 20

// Search
const searchKeyword = ref('')
const searchTab = ref('goods')

// Filters
const filterDate = ref('')
const filterSort = ref('random')
const filterPriceMin = ref('')
const filterPriceMax = ref('')
const filterTag = ref('')
const allTags = ref([])

// Seller search
const sellerResults = ref([])
const sellerLoading = ref(false)

const hasActiveFilters = computed(() =>
  filterDate.value || filterSort.value !== 'random' || filterPriceMin.value || filterPriceMax.value || filterTag.value
)
const hasMore = computed(() => items.value.length < total.value)

async function fetchTags() {
  try {
    const res = await getTags()
    allTags.value = res.data || []
  } catch { /* silent */ }
}

// Read tag from URL query on mount
function initFromURL() {
  if (route.query.tag) {
    filterTag.value = route.query.tag
    searchTab.value = 'goods'
    fetchGoods(1, false)
  } else if (route.query.keyword) {
    searchKeyword.value = route.query.keyword
    searchTab.value = 'goods'
    fetchGoods(1, false)
  } else {
    fetchGoods(1, false)
  }
}

function buildParams(p) {
  const params = { page: p, page_size: pageSize, sort: filterSort.value }
  if (searchTab.value === 'goods' && searchKeyword.value) {
    params.keyword = searchKeyword.value
  }
  if (filterTag.value) params.tag = filterTag.value
  if (filterDate.value) {
    const d = new Date()
    d.setDate(d.getDate() - parseInt(filterDate.value))
    params.date_from = d.toISOString().slice(0, 10)
  }
  if (filterPriceMin.value) params.price_min = parseFloat(filterPriceMin.value)
  if (filterPriceMax.value) params.price_max = parseFloat(filterPriceMax.value)
  return params
}

async function fetchGoods(p = 1, append = false) {
  try {
    if (append) loadingMore.value = true
    else loading.value = true

    const params = buildParams(p)
    const res = await getGoodsList(params)
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

async function searchSellers() {
  if (!searchKeyword.value.trim()) { sellerResults.value = []; return }
  sellerLoading.value = true
  try {
    // Search sellers by querying goods grouped by seller
    const res = await api.get('/api/seller/search', { params: { keyword: searchKeyword.value.trim() } })
    sellerResults.value = res.data || []
  } catch {
    sellerResults.value = []
  } finally {
    sellerLoading.value = false
  }
}

function handleSearch() {
  if (searchTab.value === 'seller') {
    searchSellers()
  } else {
    page.value = 1
    fetchGoods(1, false)
  }
}

function switchTab(tab) {
  searchTab.value = tab
  if (tab === 'seller') {
    searchSellers()
  } else if (tab === 'goods' || tab === 'filter') {
    // keep current results
  }
}

function applyFilters() {
  searchTab.value = 'goods'
  page.value = 1
  fetchGoods(1, false)
}

function resetFilters() {
  filterDate.value = ''
  filterSort.value = 'newest'
  filterPriceMin.value = ''
  filterPriceMax.value = ''
  filterTag.value = ''
  searchKeyword.value = ''
  page.value = 1
  searchTab.value = 'goods'
  fetchGoods(1, false)
}

function resetAll() {
  resetFilters()
  router.replace('/')
}

function goToSeller(id) {
  router.push(`/seller/${id}`)
}

function loadMore() {
  fetchGoods(page.value + 1, true)
}

// Watch URL changes
watch(() => route.query.tag, (newTag) => {
  if (newTag) {
    filterTag.value = newTag
    searchTab.value = 'goods'
    fetchGoods(1, false)
  }
})

onMounted(() => {
  fetchTags()
  initFromURL()
})
</script>

<style scoped>
.home {
  padding-bottom: 40px;
}

/* Hero Banner */
.hero-banner {
  position: relative;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--card-bg) 40%, var(--primary-light) 100%);
  border-radius: 20px;
  padding: 28px 36px;
  margin-bottom: 24px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  border: 1px solid var(--border-light);
}

.hero-content { position: relative; z-index: 1; }

.hero-title {
  font-size: 26px;
  font-weight: 800;
  color: var(--text);
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-icon { font-size: 28px; }

.hero-subtitle {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-muted);
}

.hero-decoration { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }

.hero-circle { position: absolute; border-radius: 50%; opacity: 0.08; }
.hero-circle.c1 { width: 200px; height: 200px; background: var(--primary); top: -60px; right: -40px; }
.hero-circle.c2 { width: 120px; height: 120px; background: #FBBF24; top: 30px; right: 100px; }
.hero-circle.c3 { width: 80px; height: 80px; background: var(--primary); bottom: -20px; right: 200px; }

/* Search Section */
.search-section {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 20px 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04);
  border: 1px solid var(--border-light);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg);
  border-radius: 12px;
  padding: 4px 4px 4px 16px;
  border: 1px solid var(--border);
  transition: all 0.25s ease;
}

.search-bar:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.search-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 15px;
  color: var(--text);
  outline: none;
  height: 40px;
  padding: 0;
}

.search-input::placeholder { color: var(--text-muted); }

.search-clear {
  min-width: auto;
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: var(--border-light);
  border-radius: 50%;
  font-size: 16px;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-clear:hover { background: var(--border); color: var(--text); }

.search-btn {
  min-width: auto;
  padding: 0 22px;
  height: 40px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  background: var(--gradient-primary);
  color: #fff;
  border: none;
  cursor: pointer;
}

.search-btn:hover {
  background: var(--gradient-primary);
}

/* Search Tabs */
.search-tabs {
  display: flex;
  gap: 4px;
  margin-top: 16px;
  border-bottom: 1px solid var(--border-light);
  padding-bottom: 0;
}

.search-tab {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s ease;
  min-width: auto;
  position: relative;
}

.search-tab:hover { color: var(--primary); }

.search-tab.active {
  color: var(--primary);
  font-weight: 600;
  border-bottom-color: var(--primary);
}

.tab-count { font-size: 12px; font-weight: 400; }

.filter-has {
  color: var(--primary);
  font-size: 8px;
  position: absolute;
  top: 6px;
  right: 10px;
}

/* Filter Panel */
.filter-panel {
  padding: 16px 0 4px;
  animation: filterSlideDown 0.25s ease;
}

@keyframes filterSlideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.filter-row {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .filter-row { flex-direction: column; gap: 12px; }
}

.filter-group { flex: 1; }

.filter-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.filter-select {
  width: 100%;
  height: 40px;
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 0 12px;
  font-size: 14px;
  color: var(--text);
  background: #fff;
  cursor: pointer;
}

.price-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price-input {
  flex: 1;
  height: 40px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.price-sep { color: var(--text-muted); font-size: 14px; }

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 4px;
}

/* Seller Results */
.seller-results {
  padding-top: 16px;
}

.seller-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.seller-result-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.seller-result-item:hover {
  background: linear-gradient(135deg, var(--primary-light), var(--card-bg));
  border-color: var(--primary-light);
}

.s-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-light);
}

.s-info { flex: 1; }

.s-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.s-meta {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

.s-arrow {
  font-size: 24px;
  color: var(--text-muted);
}

/* Results Header */
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.results-info {
  font-size: 14px;
  color: var(--text-secondary);
}

.results-info strong {
  color: var(--primary);
}

.results-total {
  margin-left: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

/* Skeleton */
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

.skeleton-img { width: 100%; height: 200px; border-radius: 0; }
.skeleton-text { height: 16px; margin: 12px 16px 0; border-radius: 6px; }

.goods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}

.loading-text, .empty, .empty-small {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.empty-icon { font-size: 56px; margin-bottom: 16px; }

.empty h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.empty p { font-size: 14px; color: var(--text-muted); }

.load-more { text-align: center; margin-top: 36px; }

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
  background: linear-gradient(135deg, var(--primary-light), transparent);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>

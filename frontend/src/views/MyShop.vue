<template>
  <div class="my-shop">
    <div class="shop-header">
      <h1 class="page-title">我的店铺</h1>
      <button class="btn-primary" @click="showForm = true">发布商品</button>
    </div>

    <div v-if="loading" class="loading-text">加载中...</div>
    <div v-else-if="goodsList.length === 0" class="empty">
      <p>还没有发布任何商品</p>
      <button class="btn-primary" @click="showForm = true">发布第一个商品</button>
    </div>
    <div v-else class="goods-list">
      <div v-for="item in goodsList" :key="item.id" class="shop-goods-item">
        <div class="item-image">
          <img
            :src="item.images?.[0] || placeholderImage"
            :alt="item.title"
          />
        </div>
        <div class="item-info">
          <div class="item-title">{{ item.title }}</div>
          <div class="item-price">¥{{ item.price }}</div>
          <div class="item-meta">
            <span :class="['status-badge', item.status === 1 ? 'status-up' : 'status-down']">
              {{ item.status === 1 ? '上架中' : '已下架' }}
            </span>
            <span class="item-date">{{ formatDate(item.created_at) }}</span>
          </div>
        </div>
        <div class="item-actions">
          <button
            :class="['btn-sm', item.status === 1 ? 'btn-outline' : 'btn-success']"
            @click="handleToggleStatus(item)"
          >
            {{ item.status === 1 ? '下架' : '上架' }}
          </button>
          <button class="btn-outline btn-sm" @click="openEdit(item)">编辑</button>
          <button class="btn-danger btn-sm" @click="handleDelete(item.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <GoodsForm
      v-if="showForm"
      :goods="editGoods"
      @close="closeForm"
      @saved="onSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { getMyGoods } from '../api/user'
import { getGoodsList, deleteGoods, toggleGoodsStatus } from '../api/goods'
import GoodsForm from '../components/GoodsForm.vue'
import dayjs from 'dayjs'

const router = useRouter()
const toast = useToast()

const goodsList = ref([])
const loading = ref(false)
const showForm = ref(false)
const editGoods = ref(null)

const placeholderImage = 'data:image/svg+xml,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="#F3F4F6"><rect width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="#9CA3AF" font-size="10">暂无图片</text></svg>'
)

async function fetchMyGoods() {
  loading.value = true
  try {
    const res = await getMyGoods()
    goodsList.value = res.data || []
  } catch (e) {
    toast.error(e.msg || '加载失败')
  } finally {
    loading.value = false
  }
}

function openEdit(item) {
  editGoods.value = item
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editGoods.value = null
}

async function onSaved() {
  closeForm()
  await fetchMyGoods()
  // Navigate to home to see updated public listing
  router.push('/')
}

async function handleToggleStatus(item) {
  try {
    await toggleGoodsStatus(item.id)
    toast.success(item.status === 1 ? '商品已下架' : '商品已上架')
    await fetchMyGoods()
  } catch (e) {
    toast.error(e.msg || '操作失败')
  }
}

async function handleDelete(id) {
  if (!confirm('确定要删除该商品吗？')) return
  try {
    await deleteGoods(id)
    toast.success('商品已删除')
    await fetchMyGoods()
  } catch (e) {
    toast.error(e.msg || '删除失败')
  }
}

function formatDate(dateStr) {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  fetchMyGoods()
})
</script>

<style scoped>
.shop-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.shop-header .page-title {
  margin-bottom: 0;
}

.loading-text, .empty {
  text-align: center;
  padding: 60px 0;
  color: var(--text-secondary);
}

.empty button {
  margin-top: 16px;
}

.goods-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shop-goods-item {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  padding: 16px;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.shop-goods-item:hover {
  box-shadow: 0 12px 28px rgba(249, 115, 22, 0.08);
  border-color: rgba(249, 115, 22, 0.1);
  transform: translateX(4px);
}

.item-image {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
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
}

.item-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-price {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent);
  margin: 4px 0;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.status-up {
  background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
  color: #047857;
}

.status-down {
  background: linear-gradient(135deg, #F3F4F6, #E5E7EB);
  color: var(--text-muted);
}

.item-date {
  font-size: 12px;
  color: var(--text-muted);
}

.item-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .shop-goods-item {
    flex-wrap: wrap;
  }
  .item-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>

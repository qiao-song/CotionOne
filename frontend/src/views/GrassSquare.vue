<template>
  <div class="grass-square">
    <!-- Top banner -->
    <div class="gs-banner">
      <div class="gs-title-row">
        <h1 class="gs-title">🌱 种草广场</h1>
        <span class="gs-subtitle">发现好物，分享生活</span>
      </div>
      <button class="btn-plant" @click="goToEditor" v-if="authStore.isLoggedIn">
        ✏️ 我要种草
      </button>
      <router-link to="/login" class="btn-plant" v-else>
        ✏️ 登录后种草
      </router-link>
    </div>

    <!-- Emoji browser button -->
    <div class="gs-toolbar">
      <button class="btn-emoji-browser" @click="emojiPanelMode = 'browser'; showEmojiPanel = true">
        😊 Tbao 表情广场
      </button>
    </div>

    <!-- Feed -->
    <div class="gs-feed" ref="feedRef">
      <PostCard
        v-for="item in feedItems"
        :key="item.id"
        :post="item"
        :emojis-map="emojisMap"
      />

      <!-- Loading -->
      <div v-if="loading" class="feed-loading">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <!-- Empty state -->
      <div v-if="!loading && feedItems.length === 0" class="feed-empty">
        <div class="empty-icon">🌱</div>
        <h2>还没有种草日志</h2>
        <p>快来发布第一条种草日志吧~</p>
      </div>

      <!-- Load more trigger -->
      <div ref="loadMoreRef" class="load-more-trigger"></div>
    </div>

    <!-- Emoji panel -->
    <EmojiPanel
      :visible="showEmojiPanel"
      :mode="emojiPanelMode"
      @close="showEmojiPanel = false"
      @select="onEmojiSelect"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { getPosts } from '../api/post'
import { getEmojis } from '../api/emoji'
import PostCard from '../components/PostCard.vue'
import EmojiPanel from '../components/EmojiPanel.vue'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const feedItems = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const feedRef = ref(null)
const loadMoreRef = ref(null)

const showEmojiPanel = ref(false)
const emojiPanelMode = ref('browser') // 'browser' for GrassSquare
const emojisMap = reactive({})

let observer = null

function goToEditor() {
  router.push('/post-editor')
}

function onEmojiSelect(emoji) {
  // In browser mode, selection just downloads
}

async function fetchEmojisMap() {
  try {
    const res = await getEmojis({ page_size: 100 })
    const items = res.data?.items || []
    items.forEach(e => {
      emojisMap[e.id] = e
    })
  } catch { /* silent */ }
}

async function fetchFeed(p = 1, append = false) {
  if (loading.value) return
  loading.value = true
  try {
    const res = await getPosts({ page: p, page_size: 10 })
    const items = res.data?.items || []
    if (append) {
      feedItems.value.push(...items)
    } else {
      feedItems.value = items
    }
    total.value = res.data?.total || 0
    page.value = p
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  await fetchFeed(page.value + 1, true)
}

// IntersectionObserver for infinite scroll
function setupObserver() {
  if (!loadMoreRef.value) return
  observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !loading.value && feedItems.value.length > 0) {
      loadMore()
    }
  }, { threshold: 0.1 })
  observer.observe(loadMoreRef.value)
}

onMounted(async () => {
  await Promise.all([fetchFeed(1, false), fetchEmojisMap()])
  setupObserver()
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.grass-square {
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 16px;
}

/* Banner */
.gs-banner {
  background: linear-gradient(135deg, #FFF7ED, #FFFFFF, #F0FDF4);
  border-radius: var(--radius);
  padding: 28px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  border: 1px solid var(--border);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.gs-title-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gs-title {
  font-size: 26px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(135deg, #22C55E, #F97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.gs-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}

.btn-plant {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 12px 24px;
  background: var(--gradient-primary);
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
  box-shadow: 0 4px 14px rgba(249, 115, 22, 0.35);
  transition: all 0.3s ease;
}

.btn-plant:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(249, 115, 22, 0.45);
}

/* Toolbar */
.gs-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.btn-emoji-browser {
  background: var(--bg);
  border: 1.5px solid var(--border);
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  min-width: auto;
}

.btn-emoji-browser:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

/* Feed */
.gs-feed {
  min-height: 300px;
}

.feed-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 32px;
  color: var(--text-muted);
  font-size: 14px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.feed-empty {
  text-align: center;
  padding: 60px 20px;
}

.feed-empty .empty-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.feed-empty h2 {
  font-size: 20px;
  color: var(--text);
  margin: 0 0 8px;
}

.feed-empty p {
  font-size: 14px;
  color: var(--text-muted);
}

.load-more-trigger {
  height: 20px;
}
</style>

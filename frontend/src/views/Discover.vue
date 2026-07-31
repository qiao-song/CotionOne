<template>
  <div class="discover-page" ref="pageRef" @wheel.prevent="handleWheel">
    <!-- Feed container -->
    <div class="feed-wrapper" ref="feedRef" :style="{ transform: `translateY(-${currentIndex * 100}vh)` }">
      <div
        v-for="(item, idx) in feedItems"
        :key="item.id"
        class="video-slide"
        :class="{ active: idx === currentIndex }"
      >
        <!-- Video -->
        <video
          :ref="el => setVideoRef(idx, el)"
          :src="item.video"
          class="video-player"
          :loop="true"
          :muted="idx !== currentIndex"
          :playsinline="true"
          preload="metadata"
          @dblclick="handleDoubleClick(idx, $event)"
          @click="handleVideoClick(idx)"
        ></video>

        <!-- Double-click heart animation -->
        <div
          v-for="heart in hearts"
          :key="heart.id"
          class="heart-burst"
          :style="{ left: heart.x + 'px', top: heart.y + 'px' }"
        >
          ❤️
        </div>

        <!-- Right side actions -->
        <div class="video-actions">
          <button class="action-btn" @click.stop="handleLike(idx)">
            <span class="action-icon" :class="{ liked: likedVideos.has(item.id) }">
              {{ likedVideos.has(item.id) ? '❤️' : '🤍' }}
            </span>
            <span class="action-count">{{ item.video_likes || 0 }}</span>
          </button>
          <button class="action-btn" @click.stop="handleComment(idx)">
            <span class="action-icon">💬</span>
            <span class="action-count">评论</span>
          </button>
          <button class="action-btn" @click.stop="handleShare(idx)">
            <span class="action-icon">🔗</span>
            <span class="action-count">{{ item.video_shares || 0 }}</span>
          </button>
        </div>

        <!-- Bottom-left product card -->
        <div class="product-card-overlay" @click="goToProduct(item.id)">
          <div class="pc-image">
            <img :src="item.images?.[0] || '/static/default.png'" alt="product" />
          </div>
          <div class="pc-info">
            <div class="pc-title">{{ item.title }}</div>
            <div class="pc-price">¥{{ parseFloat(item.price).toFixed(2) }}</div>
          </div>
          <div class="pc-arrow">›</div>
        </div>

        <!-- Seller info -->
        <div class="seller-tag">
          <img :src="item.seller_avatar || '/static/default.png'" class="seller-avatar" />
          <span class="seller-name">{{ item.seller_name }}</span>
        </div>
      </div>
    </div>

    <!-- Navigation hint -->
    <div class="nav-hint" v-if="feedItems.length > 0 && !hasInteracted">
      <span class="hint-arrow up">▲</span>
      <span class="hint-text">上下滑动切换视频</span>
      <span class="hint-arrow down">▼</span>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && feedItems.length === 0" class="empty-state">
      <div class="empty-icon">📹</div>
      <h2>暂无发现内容</h2>
      <p>还没有商家上传商品视频</p>
      <router-link to="/" class="btn-primary">去商品广场逛逛</router-link>
    </div>

    <!-- Load more indicator -->
    <div v-if="loading && feedItems.length > 0" class="load-more">
      加载中...
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { getDiscoverFeed, likeVideo, shareVideo } from '../api/goods'

const router = useRouter()
const toast = useToast()

const pageRef = ref(null)
const feedRef = ref(null)
const feedItems = ref([])
const currentIndex = ref(0)
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const hasInteracted = ref(false)

// Video refs management
const videoRefs = {}
function setVideoRef(idx, el) {
  if (el) videoRefs[idx] = el
}

// Hearts animation
const hearts = ref([])
let heartId = 0

// Liked videos tracking (localStorage)
const likedVideos = reactive(new Set(
  JSON.parse(localStorage.getItem('tbao_liked_videos') || '[]')
))

function saveLikes() {
  localStorage.setItem('tbao_liked_videos', JSON.stringify([...likedVideos]))
}

// Scroll handling
let scrollAccum = 0
let scrollThrottle = 0

function handleWheel(e) {
  hasInteracted.value = true
  scrollAccum += e.deltaY

  const now = Date.now()
  if (now - scrollThrottle < 600) return
  scrollThrottle = now

  if (Math.abs(scrollAccum) < 40) return

  if (scrollAccum > 0 && currentIndex.value < feedItems.value.length - 1) {
    switchToVideo(currentIndex.value + 1)
  } else if (scrollAccum < 0 && currentIndex.value > 0) {
    switchToVideo(currentIndex.value - 1)
  }

  // Load more near the end
  if (currentIndex.value >= feedItems.value.length - 2 && hasMore.value) {
    loadMore()
  }

  scrollAccum = 0
}

function handleKey(e) {
  if (e.key === 'ArrowDown' && currentIndex.value < feedItems.value.length - 1) {
    e.preventDefault()
    hasInteracted.value = true
    switchToVideo(currentIndex.value + 1)
    if (currentIndex.value >= feedItems.value.length - 2 && hasMore.value) loadMore()
  } else if (e.key === 'ArrowUp' && currentIndex.value > 0) {
    e.preventDefault()
    hasInteracted.value = true
    switchToVideo(currentIndex.value - 1)
  }
}

function switchToVideo(idx) {
  // Pause current video
  const currentVideo = videoRefs[currentIndex.value]
  if (currentVideo) currentVideo.pause()

  currentIndex.value = idx

  // Play new video
  nextTick(() => {
    const newVideo = videoRefs[idx]
    if (newVideo) {
      newVideo.currentTime = 0
      newVideo.muted = false
      newVideo.play().catch(() => {})
    }
  })
}

// Video click - toggle play/pause
let lastClickTime = 0
function handleVideoClick(idx) {
  const now = Date.now()
  if (now - lastClickTime < 300) return // handled by dblclick
  lastClickTime = now

  const video = videoRefs[idx]
  if (!video) return
  if (video.paused) {
    video.play().catch(() => {})
  } else {
    video.pause()
  }
}

// Double click to like
function handleDoubleClick(idx, e) {
  const video = videoRefs[idx]
  if (!video) return

  // Pause on double-click
  video.pause()

  const item = feedItems.value[idx]
  if (!item) return

  // Show heart animation
  const rect = e.currentTarget.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  spawnHeart(x, y)

  // Like the video
  if (!likedVideos.has(item.id)) {
    likedVideos.add(item.id)
    saveLikes()
    item.video_likes = (item.video_likes || 0) + 1
    likeVideo(item.id).catch(() => {})
  }
}

function spawnHeart(x, y) {
  const id = heartId++
  hearts.value.push({ id, x, y })
  setTimeout(() => {
    hearts.value = hearts.value.filter(h => h.id !== id)
  }, 1000)
}

// Actions
function handleLike(idx) {
  const item = feedItems.value[idx]
  if (!item) return

  if (likedVideos.has(item.id)) {
    // Unlike
    likedVideos.delete(item.id)
    saveLikes()
    item.video_likes = Math.max(0, (item.video_likes || 1) - 1)
    toast.info('已取消点赞')
  } else {
    // Like
    likedVideos.add(item.id)
    saveLikes()
    item.video_likes = (item.video_likes || 0) + 1
    likeVideo(item.id).catch(() => {})
    toast.success('已点赞')
  }
}

function handleComment(idx) {
  const item = feedItems.value[idx]
  if (!item) return
  // Jump to product detail scrolled to reviews section
  router.push(`/goods/${item.id}?tab=reviews`)
}

async function handleShare(idx) {
  const item = feedItems.value[idx]
  if (!item) return

  const link = `${window.location.origin}/goods/${item.id}`
  try {
    await navigator.clipboard.writeText(link)
    item.video_shares = (item.video_shares || 0) + 1
    shareVideo(item.id).catch(() => {})
    toast.success('已复制链接')
  } catch {
    // Fallback
    const textarea = document.createElement('textarea')
    textarea.value = link
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    item.video_shares = (item.video_shares || 0) + 1
    shareVideo(item.id).catch(() => {})
    toast.success('已复制链接')
  }
}

function goToProduct(id) {
  router.push(`/goods/${id}`)
}

// Load data
async function loadFeed() {
  if (loading.value) return
  loading.value = true
  try {
    const res = await getDiscoverFeed({ page: page.value, page_size: 10 })
    const newItems = res.data.items || []
    if (newItems.length < 10) hasMore.value = false
    feedItems.value.push(...newItems)
    page.value++

    // Auto-play first video
    if (feedItems.value.length === newItems.length && newItems.length > 0) {
      nextTick(() => {
        const video = videoRefs[0]
        if (video) video.play().catch(() => {})
      })
    }
  } catch (e) {
    // silent
  } finally {
    loading.value = false
  }
}

function loadMore() {
  loadFeed()
}

onMounted(() => {
  loadFeed()
  window.addEventListener('keydown', handleKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKey)
  // Pause all videos
  Object.values(videoRefs).forEach(v => {
    if (v) v.pause()
  })
})
</script>

<style scoped>
.discover-page {
  position: fixed;
  inset: 64px 0 0 0;
  background: #000;
  overflow: hidden;
  z-index: 50;
}

.feed-wrapper {
  transition: transform 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
}

.video-slide {
  height: calc(100vh - 64px);
  width: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
  cursor: pointer;
}

/* Right side actions */
.video-actions {
  position: absolute;
  right: 16px;
  bottom: 160px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 10;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  min-width: auto;
  color: #fff;
  transition: transform 0.15s ease;
}

.action-btn:hover {
  transform: scale(1.15);
}

.action-btn:active {
  transform: scale(0.9);
}

.action-icon {
  font-size: 32px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
  transition: transform 0.2s ease;
}

.action-icon.liked {
  animation: heartPop 0.3s ease-out;
}

@keyframes heartPop {
  0% { transform: scale(1); }
  50% { transform: scale(1.35); }
  100% { transform: scale(1); }
}

.action-count {
  font-size: 12px;
  font-weight: 600;
  text-shadow: 0 1px 3px rgba(0,0,0,0.6);
}

/* Product card overlay */
.product-card-overlay {
  position: absolute;
  left: 16px;
  bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(12px);
  border-radius: 12px;
  padding: 10px 14px 10px 10px;
  cursor: pointer;
  z-index: 10;
  max-width: 320px;
  border: 1px solid rgba(255,255,255,0.15);
  transition: all 0.2s ease;
}

.product-card-overlay:hover {
  background: rgba(0, 0, 0, 0.8);
  border-color: rgba(255,255,255,0.3);
  transform: translateY(-2px);
}

.pc-image {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #1F2937;
}

.pc-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pc-info {
  min-width: 0;
  flex: 1;
}

.pc-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.pc-price {
  font-size: 18px;
  font-weight: 800;
  color: #22C55E;
}

.pc-arrow {
  font-size: 24px;
  color: rgba(255,255,255,0.6);
  flex-shrink: 0;
}

/* Seller tag */
.seller-tag {
  position: absolute;
  left: 16px;
  bottom: 110px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 10;
}

.seller-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255,255,255,0.4);
}

.seller-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0,0,0,0.5);
}

/* Heart burst animation */
.heart-burst {
  position: absolute;
  font-size: 36px;
  pointer-events: none;
  z-index: 20;
  animation: heartBurst 1s ease-out forwards;
  transform: translate(-50%, -50%);
}

@keyframes heartBurst {
  0% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(0.3);
  }
  30% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.2);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) scale(1.5) translateY(-40px);
  }
}

/* Navigation hint */
.nav-hint {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: rgba(255,255,255,0.5);
  font-size: 12px;
  z-index: 15;
  animation: hintFade 2s ease-in-out infinite;
}

.hint-arrow {
  font-size: 16px;
}

@keyframes hintFade {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

/* Empty state */
.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  gap: 12px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 8px;
}

.empty-state h2 {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}

.empty-state p {
  font-size: 14px;
  color: #9CA3AF;
  margin-bottom: 16px;
}

.load-more {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,0.5);
  font-size: 13px;
}
</style>

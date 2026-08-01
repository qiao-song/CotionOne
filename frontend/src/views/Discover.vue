<template>
  <div class="discover-page" ref="pageRef" @wheel.prevent="handleWheel">
    <!-- Feed container -->
    <div class="feed-wrapper" ref="feedRef" :style="{ transform: `translateY(calc(-${currentIndex} * (100vh - 64px)))` }">
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
          :poster="item.images?.[0] || ''"
          class="video-player"
          :loop="true"
          :muted="idx !== currentIndex"
          :playsinline="true"
          :preload="Math.abs(idx - currentIndex) <= 1 ? 'auto' : 'metadata'"
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
        <div class="seller-tag" @click.stop="goToSeller(item.seller_id)">
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

    <!-- Comment Panel -->
    <div class="comment-overlay" v-if="showCommentPanel" @click.self="closeCommentPanel">
      <div class="comment-panel">
        <div class="comment-panel-header">
          <span class="comment-panel-title">评论 ({{ commentTotal }})</span>
          <button class="comment-panel-close" @click="closeCommentPanel">✕</button>
        </div>
        <div class="comment-list" ref="commentListRef">
          <div v-if="loadingComments" class="comment-loading">加载中...</div>
          <div v-else-if="comments.length === 0" class="comment-empty">
            <p>暂无评论，来说两句吧~</p>
          </div>
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <img
              :src="c.user_avatar || '/static/default.png'"
              class="comment-avatar"
              @click.stop="goToUser(c.user_id)"
              alt="avatar"
            />
            <div class="comment-body">
              <div class="comment-user" @click.stop="goToUser(c.user_id)">{{ c.username }}</div>
              <div class="comment-text">{{ c.content }}</div>
              <div class="comment-time">{{ c.created_at }}</div>
            </div>
          </div>
          <div v-if="commentHasMore" class="comment-load-more" @click="loadMoreComments">
            加载更多...
          </div>
        </div>
        <div class="comment-input-row">
          <input
            v-model="commentInput"
            class="comment-input"
            placeholder="说点什么..."
            maxlength="500"
            @keyup.enter="submitComment"
          />
          <button class="comment-submit" @click="submitComment" :disabled="!commentInput.trim() || submittingComment">
            {{ submittingComment ? '...' : '发送' }}
          </button>
        </div>
      </div>
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
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { getDiscoverFeed, likeVideo, shareVideo } from '../api/goods'
import { getVideoComments, createVideoComment } from '../api/videoComment'

const router = useRouter()
const authStore = useAuthStore()
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

// Scroll handling — no throttle, minimal transition lock with pending queue
let scrollAccum = 0
let isTransitioning = false
let pendingDir = 0  // -1 up, 0 none, +1 down

function executeScroll(dir) {
  if (dir > 0 && currentIndex.value < feedItems.value.length - 1) {
    switchToVideo(currentIndex.value + 1)
  } else if (dir < 0 && currentIndex.value > 0) {
    switchToVideo(currentIndex.value - 1)
  }
  // loadMore() now deferred to after CSS transition completes (inside switchToVideo setTimeout)
  // to avoid killing the slide animation with transition:none
}

function handleWheel(e) {
  hasInteracted.value = true
  scrollAccum += e.deltaY

  if (isTransitioning) {
    // Queue direction for immediate execution after transition ends
    if (scrollAccum > 40) pendingDir = 1
    else if (scrollAccum < -40) pendingDir = -1
    return
  }

  if (Math.abs(scrollAccum) < 60) return

  const dir = scrollAccum > 0 ? 1 : -1
  scrollAccum = 0
  pendingDir = 0
  executeScroll(dir)
}

function handleKey(e) {
  if (isTransitioning) {
    if (e.key === 'ArrowDown') pendingDir = 1
    else if (e.key === 'ArrowUp') pendingDir = -1
    return
  }
  if (e.key === 'ArrowDown' && currentIndex.value < feedItems.value.length - 1) {
    e.preventDefault()
    hasInteracted.value = true
    executeScroll(1)
  } else if (e.key === 'ArrowUp' && currentIndex.value > 0) {
    e.preventDefault()
    hasInteracted.value = true
    executeScroll(-1)
  }
}

function switchToVideo(idx) {
  isTransitioning = true

  // Pause current video
  const currentVideo = videoRefs[currentIndex.value]
  if (currentVideo) currentVideo.pause()

  // Pre-seek target video to first frame BEFORE CSS transition,
  // so the browser decodes the cover frame during the slide animation
  const nextVideo = videoRefs[idx]
  if (nextVideo) {
    nextVideo.currentTime = 0
    nextVideo.muted = false
  }

  // Trigger CSS transition — cover frame already decoding
  currentIndex.value = idx

  // After transition, play seamlessly from the already-visible first frame
  setTimeout(() => {
    if (nextVideo) {
      nextVideo.play().catch(() => {})
    }
    isTransitioning = false

    // Safe to mutate DOM now — transition is fully done
    if (idx >= feedItems.value.length - 2) {
      loadMore()
    }

    // Immediately process any scroll queued during transition
    if (pendingDir !== 0) {
      const dir = pendingDir
      pendingDir = 0
      scrollAccum = 0
      executeScroll(dir)
    }
  }, 400) // Slightly longer than 0.35s CSS transition for visual settle
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

// === Comment Panel ===
const showCommentPanel = ref(false)
const comments = ref([])
const commentTotal = ref(0)
const commentPage = ref(1)
const commentHasMore = ref(false)
const loadingComments = ref(false)
const commentInput = ref('')
const submittingComment = ref(false)
const commentGoodsId = ref(null)
const commentListRef = ref(null)

function handleComment(idx) {
  const item = feedItems.value[idx]
  if (!item) return
  if (!authStore.isLoggedIn) {
    router.push(`/login?redirect=${encodeURIComponent(router.currentRoute.value.fullPath)}`)
    return
  }
  commentGoodsId.value = item.id
  showCommentPanel.value = true
  comments.value = []
  commentPage.value = 1
  commentInput.value = ''
  loadComments()
}

function closeCommentPanel() {
  showCommentPanel.value = false
}

async function loadComments(append = false) {
  if (loadingComments.value || !commentGoodsId.value) return
  loadingComments.value = true
  try {
    const page = append ? commentPage.value + 1 : 1
    const res = await getVideoComments(commentGoodsId.value, { page, page_size: 20 })
    if (append) {
      comments.value.push(...(res.data.items || []))
    } else {
      comments.value = res.data.items || []
    }
    commentTotal.value = res.data.total || 0
    commentPage.value = page
    commentHasMore.value = comments.value.length < commentTotal.value
  } catch { /* silent */ }
  finally { loadingComments.value = false }
}

function loadMoreComments() {
  loadComments(true)
}

async function submitComment() {
  const text = commentInput.value.trim()
  if (!text || submittingComment.value || !commentGoodsId.value) return
  submittingComment.value = true
  try {
    const res = await createVideoComment({ goods_id: commentGoodsId.value, content: text })
    comments.value.unshift(res.data)
    commentTotal.value++
    commentInput.value = ''
    toast.success('评论成功')
  } catch (e) {
    toast.error(e.msg || '评论失败')
  } finally {
    submittingComment.value = false
  }
}

function goToUser(userId) {
  if (userId) {
    showCommentPanel.value = false
    router.push(`/seller/${userId}`)
  }
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

function goToSeller(sellerId) {
  if (sellerId) {
    router.push(`/seller/${sellerId}`)
  }
}

// Load data with random order + dedup tracking
const seenVideoIds = reactive(new Set(
  JSON.parse(localStorage.getItem('tbao_seen_videos') || '[]')
))

function saveSeen() {
  localStorage.setItem('tbao_seen_videos', JSON.stringify([...seenVideoIds]))
}

async function loadFeed() {
  if (loading.value) return
  loading.value = true
  try {
    const params = { page: 1, page_size: 30, sort: 'random' }
    // Pass exclude_ids for dedup — cycle when all seen
    if (seenVideoIds.size > 0) {
      params.exclude_ids = [...seenVideoIds].join(',')
    }
    const res = await getDiscoverFeed(params)
    let newItems = res.data.items || []

    // If no new items (all videos seen), reset and reload
    if (newItems.length === 0 && seenVideoIds.size > 0) {
      seenVideoIds.clear()
      saveSeen()
      const retryRes = await getDiscoverFeed({ page: 1, page_size: 30, sort: 'random' })
      newItems = retryRes.data.items || []
    }

    hasMore.value = newItems.length >= 30
    feedItems.value = newItems
    // Track newly seen video IDs
    newItems.forEach(item => seenVideoIds.add(item.id))
    saveSeen()
    page.value = 2

    // Auto-play first video
    if (feedItems.value.length > 0) {
      nextTick(() => {
        const video = videoRefs[0]
        if (video) video.play().catch(() => {})
      })
    }
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loading.value) return
  loading.value = true
  try {
    const params = { page: page.value, page_size: 10, sort: 'random' }
    if (seenVideoIds.size > 0) {
      params.exclude_ids = [...seenVideoIds].join(',')
    }
    const res = await getDiscoverFeed(params)
    let newItems = res.data.items || []

    // If no new items, reset cycle
    if (newItems.length === 0 && seenVideoIds.size > 0) {
      seenVideoIds.clear()
      saveSeen()
      const retryRes = await getDiscoverFeed({ page: 1, page_size: 10, sort: 'random' })
      newItems = retryRes.data.items || []
    }

    // Only disable CSS transition when no active slide animation
    // (loadMore may be called from switchToVideo's setTimeout AFTER transition ends)
    if (feedRef.value && !isTransitioning) {
      feedRef.value.style.transition = 'none'
    }
    // Always allow infinite scroll — never stop loading
    feedItems.value.push(...newItems)
    newItems.forEach(item => seenVideoIds.add(item.id))
    saveSeen()
    page.value++

    // Re-enable transition after DOM update completes (only if we disabled it)
    await nextTick()
    if (feedRef.value && !isTransitioning) {
      void feedRef.value.offsetHeight // force reflow
      feedRef.value.style.transition = ''
    }
  } catch {
    // silent
  } finally {
    loading.value = false
  }
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
  transition: transform 0.35s cubic-bezier(0.4, 0.0, 0.2, 1.0);
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
  cursor: pointer;
  transition: transform 0.2s ease;
}

.seller-tag:hover {
  transform: scale(1.05);
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

/* === Comment Panel === */
.comment-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  animation: overlayIn 0.25s ease;
}

@keyframes overlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.comment-panel {
  width: 100%;
  max-height: 60vh;
  background: #1a1a2e;
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
  animation: panelUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes panelUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.comment-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.comment-panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.comment-panel-close {
  min-width: auto;
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.7);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
}

.comment-panel-close:hover {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

.comment-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 20px;
  max-height: 40vh;
}

.comment-list::-webkit-scrollbar {
  width: 4px;
}
.comment-list::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.15);
  border-radius: 2px;
}

.comment-loading, .comment-empty {
  text-align: center;
  padding: 40px 0;
  color: rgba(255,255,255,0.4);
  font-size: 14px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  cursor: pointer;
  border: 1.5px solid rgba(255,255,255,0.15);
  transition: border-color 0.2s;
}

.comment-avatar:hover {
  border-color: rgba(255,255,255,0.5);
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-user {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  margin-bottom: 2px;
}

.comment-user:hover {
  color: #fff;
}

.comment-text {
  font-size: 14px;
  color: rgba(255,255,255,0.9);
  line-height: 1.5;
  word-break: break-word;
}

.comment-time {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  margin-top: 4px;
}

.comment-load-more {
  text-align: center;
  padding: 12px;
  color: rgba(255,255,255,0.4);
  font-size: 13px;
  cursor: pointer;
}

.comment-load-more:hover {
  color: rgba(255,255,255,0.7);
}

.comment-input-row {
  display: flex;
  gap: 10px;
  padding: 14px 20px 20px;
  border-top: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
}

.comment-input {
  flex: 1;
  height: 42px;
  padding: 0 16px;
  border-radius: 21px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.08);
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.comment-input::placeholder {
  color: rgba(255,255,255,0.3);
}

.comment-input:focus {
  border-color: rgba(255,255,255,0.4);
}

.comment-submit {
  min-width: auto;
  height: 42px;
  padding: 0 22px;
  border-radius: 21px;
  background: linear-gradient(135deg, #F97316, #EA580C);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.comment-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.comment-submit:not(:disabled):hover {
  transform: scale(1.04);
}
</style>

<template>
  <div
    class="post-card"
    :class="{ expanded: isExpanded, 'news-card': post.type === 'news' }"
    @dblclick="toggleExpand"
    :title="isExpanded ? '双击收起' : '双击展开全文'"
  >
    <!-- News badge -->
    <div class="news-badge" v-if="post.type === 'news'">
      <span class="badge-icon">📰</span>
      <span class="badge-text">新闻热点</span>
    </div>

    <!-- Post header (only for user posts) -->
    <div class="post-header" v-if="post.type === 'post'" @click.stop="goToSeller(post.user_id)">
      <img :src="post.user_avatar || '/static/default.png'" class="post-avatar" alt="avatar" />
      <div class="post-meta">
        <span class="post-username">{{ post.username }}</span>
        <span class="post-time">{{ post.created_at }}</span>
      </div>
    </div>

    <!-- News header -->
    <div class="post-header" v-else>
      <div class="news-source-icon">📰</div>
      <div class="post-meta">
        <span class="post-username news-source">{{ post.source || '新闻热点' }}</span>
        <span class="post-time">{{ post.created_at }}</span>
      </div>
    </div>

    <!-- Content -->
    <div class="post-content" :class="{ clamped: !isExpanded }" ref="contentRef">
      <template v-if="post.type === 'news'">
        <h4 class="news-title" v-if="post.title">{{ post.title }}</h4>
      </template>
      <div class="post-text" v-html="renderContent(post.content)"></div>
    </div>

    <!-- Expand hint -->
    <div class="expand-hint" v-if="needsExpand && !isExpanded" @click="toggleExpand">
      展开全文 ▼
    </div>
    <div class="expand-hint" v-if="needsExpand && isExpanded" @click="toggleExpand">
      收起 ▲
    </div>

    <!-- Images grid -->
    <div class="post-images" v-if="post.images && post.images.length > 0" :class="'img-count-' + Math.min(post.images.length, 9)">
      <img
        v-for="(img, idx) in post.images"
        :key="idx"
        :src="img"
        class="post-image"
        :alt="'image-' + idx"
        loading="lazy"
      />
    </div>

    <!-- Video -->
    <div class="post-video" v-if="post.video">
      <video :src="post.video" controls preload="metadata" class="video-player"></video>
    </div>

    <!-- News source link -->
    <div class="news-footer" v-if="post.type === 'news' && post.url && post.url !== '#'">
      <a :href="post.url" target="_blank" rel="noopener" class="news-link">查看原文 →</a>
    </div>

    <!-- Tooltip overlay -->
    <div class="dbl-tooltip">双击{{ isExpanded ? '收起' : '展开' }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  post: { type: Object, required: true },
  emojisMap: { type: Object, default: () => ({}) }
})

const isExpanded = ref(false)
const contentRef = ref(null)
const needsExpand = ref(false)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

function goToSeller(userId) {
  if (userId) {
    router.push(`/seller/${userId}`)
  }
}

function renderContent(content) {
  if (!content) return ''
  // Replace [emoji:ID] tags with actual emoji images
  let html = content.replace(/\[emoji:(\d+)\]/g, (match, emojiId) => {
    const emoji = props.emojisMap[emojiId]
    if (emoji) {
      return `<img src="${emoji.image_url}" alt="${emoji.name}" class="inline-emoji" title="${emoji.name}" />`
    }
    return match
  })
  // Replace newlines with <br>
  html = html.replace(/\n/g, '<br>')
  return html
}

onMounted(() => {
  nextTick(() => {
    if (contentRef.value) {
      // Check if content overflows 250px (~11 lines at 22px line-height)
      const lineHeight = 22
      const maxCollapsedHeight = lineHeight * 11 // ~250px
      needsExpand.value = contentRef.value.scrollHeight > maxCollapsedHeight + 10
    }
  })
})
</script>

<style scoped>
.post-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  padding: 20px;
  margin-bottom: 16px;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  border: 1px solid var(--border);
  user-select: none;
}

.post-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  border-color: var(--primary-light);
}

.post-card:hover .dbl-tooltip {
  opacity: 1;
}

.post-card.expanded {
  border-color: var(--primary);
  box-shadow: 0 4px 20px rgba(249, 115, 22, 0.12);
}

.news-card {
  border-left: 4px solid #EF4444;
  background: linear-gradient(135deg, #FFF5F5, #FFFFFF);
}

/* News badge */
.news-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.badge-icon {
  font-size: 16px;
}

.badge-text {
  font-size: 12px;
  font-weight: 700;
  color: #EF4444;
  background: rgba(239, 68, 68, 0.1);
  padding: 2px 10px;
  border-radius: 12px;
}

/* Header */
.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  cursor: pointer;
  padding: 4px;
  margin: -4px;
  border-radius: 12px;
  transition: background 0.2s ease;
}

.post-header:hover {
  background: rgba(249, 115, 22, 0.06);
}

.post-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--primary-light);
  flex-shrink: 0;
}

.news-source-icon {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #FEE2E2, #FECACA);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.post-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.post-username {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
}

.news-source {
  color: #DC2626;
}

.post-time {
  font-size: 12px;
  color: var(--text-muted);
}

/* Content */
.post-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text);
  word-break: break-word;
  overflow: hidden;
  transition: max-height 0.4s ease;
}

.post-content.clamped {
  max-height: 250px; /* ~11 lines at 22px line-height */
  position: relative;
}

.post-content.clamped::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(to bottom, transparent, var(--card-bg));
  pointer-events: none;
}

.news-card .post-content.clamped::after {
  background: linear-gradient(to bottom, transparent, #FFF5F5);
}

.post-text {
  white-space: pre-wrap;
}

.news-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.inline-emoji {
  height: 24px;
  width: 24px;
  vertical-align: middle;
  margin: 0 2px;
  border-radius: 4px;
}

/* Expand hint */
.expand-hint {
  margin-top: 10px;
  font-size: 13px;
  color: var(--primary);
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  padding: 6px;
  border-radius: 8px;
  transition: background 0.2s;
}

.expand-hint:hover {
  background: var(--primary-light);
}

/* Images */
.post-images {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.img-count-1 { grid-template-columns: 1fr; max-width: 400px; }
.img-count-2 { grid-template-columns: 1fr 1fr; }
.img-count-3 { grid-template-columns: 1fr 1fr 1fr; }
.img-count-4 { grid-template-columns: 1fr 1fr; }
.img-count-5, .img-count-6 { grid-template-columns: 1fr 1fr 1fr; }
.img-count-7, .img-count-8, .img-count-9 { grid-template-columns: 1fr 1fr 1fr; }

.post-image {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 10px;
  background: #F3F4F6;
  cursor: pointer;
  transition: transform 0.2s;
}

.post-image:hover {
  transform: scale(1.03);
}

/* Video */
.post-video {
  margin-top: 14px;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}

.video-player {
  width: 100%;
  max-height: 400px;
  border-radius: 12px;
}

/* News footer */
.news-footer {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.news-link {
  color: var(--primary);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
}

.news-link:hover {
  text-decoration: underline;
}

/* Double-click tooltip */
.dbl-tooltip {
  position: absolute;
  top: 10px;
  right: 14px;
  font-size: 11px;
  color: var(--text-muted);
  background: rgba(0,0,0,0.06);
  padding: 3px 10px;
  border-radius: 10px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.post-card:hover .dbl-tooltip {
  opacity: 1;
}

/* Dark mode adjustment for clamp gradient */
@media (prefers-color-scheme: dark) {
  .post-content.clamped::after {
    background: linear-gradient(to bottom, transparent, #1a1a1a);
  }
}
</style>

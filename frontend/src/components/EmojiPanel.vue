<template>
  <Teleport to="body">
    <div class="emoji-overlay" v-if="visible" @click.self="close">
      <div class="emoji-panel" @click.stop>
        <!-- Header -->
        <div class="panel-header">
          <h3 class="panel-title">
            {{ mode === 'picker' ? '选择表情' : 'Tbao 表情广场' }}
          </h3>
          <button class="panel-close" @click="close">&times;</button>
        </div>

        <!-- Upload section -->
        <div class="upload-section" v-if="authStore.isLoggedIn">
          <div class="upload-row">
            <input
              type="text"
              v-model="newEmojiName"
              placeholder="表情名称"
              class="emoji-name-input"
              maxlength="50"
            />
            <label class="upload-btn">
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                @change="handleUpload"
                hidden
              />
              📤 上传表情
            </label>
          </div>
          <div class="upload-error" v-if="uploadError">{{ uploadError }}</div>
        </div>

        <!-- Search -->
        <div class="search-row">
          <input
            type="text"
            v-model="searchQuery"
            placeholder="搜索表情..."
            class="search-input"
            @input="onSearch"
          />
        </div>

        <!-- Emoji grid -->
        <div class="emoji-grid" ref="gridRef">
          <div v-if="loading" class="grid-loading">加载中...</div>
          <div v-else-if="emojis.length === 0" class="grid-empty">
            <div class="empty-icon">😊</div>
            <p>还没有表情包</p>
            <p class="empty-hint">快来上传第一个表情吧~</p>
          </div>
          <div
            v-for="emoji in emojis"
            :key="emoji.id"
            class="emoji-item"
            @click="selectEmoji(emoji)"
          >
            <img :src="emoji.image_url" :alt="emoji.name" class="emoji-img" loading="lazy" />
            <div class="emoji-info">
              <span class="emoji-name">{{ emoji.name }}</span>
              <div class="emoji-actions">
                <span class="emoji-uploader">{{ emoji.uploader_name }}</span>
                <button
                  v-if="mode === 'browser'"
                  class="emoji-download"
                  @click.stop="handleDownload(emoji)"
                  title="下载表情"
                >
                  ⬇️ {{ emoji.download_count }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Login prompt -->
        <div class="login-prompt" v-if="!authStore.isLoggedIn && mode === 'picker'">
          <router-link to="/login" class="btn-primary btn-sm" @click="close">
            登录后上传表情
          </router-link>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { getEmojis, uploadEmoji, downloadEmoji } from '../api/emoji'

const props = defineProps({
  visible: { type: Boolean, default: false },
  mode: { type: String, default: 'picker' } // 'picker' | 'browser'
})

const emit = defineEmits(['close', 'select'])

const authStore = useAuthStore()
const toast = useToast()

const emojis = ref([])
const loading = ref(false)
const searchQuery = ref('')
const newEmojiName = ref('')
const uploadError = ref('')
const gridRef = ref(null)

let searchTimer = null

function close() {
  emit('close')
}

function selectEmoji(emoji) {
  if (props.mode === 'picker') {
    emit('select', emoji)
    close()
  }
}

async function fetchEmojis() {
  loading.value = true
  try {
    const params = {}
    if (searchQuery.value) params.search = searchQuery.value
    const res = await getEmojis(params)
    emojis.value = res.data.items || []
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchEmojis, 300)
}

async function handleUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return

  const name = newEmojiName.value.trim()
  if (!name) {
    uploadError.value = '请输入表情名称'
    return
  }

  uploadError.value = ''

  const formData = new FormData()
  formData.append('name', name)
  formData.append('image', file)

  try {
    await uploadEmoji(formData)
    toast.success('表情上传成功')
    newEmojiName.value = ''
    e.target.value = ''
    fetchEmojis()
  } catch (err) {
    uploadError.value = err.msg || '上传失败'
  }
}

async function handleDownload(emoji) {
  try {
    await downloadEmoji(emoji.id)
    emoji.download_count = (emoji.download_count || 0) + 1
    toast.success('下载成功')
  } catch {
    // silent
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    fetchEmojis()
    newEmojiName.value = ''
    uploadError.value = ''
  }
})
</script>

<style scoped>
.emoji-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.emoji-panel {
  background: #fff;
  border-radius: 20px 20px 0 0;
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 12px;
  border-bottom: 1px solid var(--border);
}

.panel-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.panel-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--bg);
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.panel-close:hover {
  background: #FEE2E2;
  color: #EF4444;
}

/* Upload section */
.upload-section {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
}

.upload-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.emoji-name-input {
  flex: 1;
  height: 38px;
  padding: 0 12px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.emoji-name-input:focus {
  border-color: var(--primary);
}

.upload-btn {
  padding: 0 16px;
  height: 38px;
  background: var(--primary);
  color: #fff;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  white-space: nowrap;
  transition: all 0.2s;
  border: none;
}

.upload-btn:hover {
  background: var(--primary-dark);
}

.upload-error {
  color: #EF4444;
  font-size: 12px;
  margin-top: 6px;
}

/* Search */
.search-row {
  padding: 12px 20px;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 14px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  background: var(--bg);
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: var(--primary);
}

/* Grid */
.emoji-grid {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  min-height: 150px;
}

.grid-loading, .grid-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 14px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.emoji-item {
  background: var(--bg);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.emoji-item:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.15);
}

.emoji-img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  background: #F3F4F6;
}

.emoji-info {
  padding: 8px 10px;
}

.emoji-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.emoji-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.emoji-uploader {
  font-size: 11px;
  color: var(--text-muted);
}

.emoji-download {
  background: none;
  border: none;
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
  transition: background 0.2s;
  color: var(--text-secondary);
  min-width: auto;
}

.emoji-download:hover {
  background: var(--primary-light);
  color: var(--primary);
}

/* Login prompt */
.login-prompt {
  padding: 12px 20px;
  text-align: center;
  border-top: 1px solid var(--border);
}

.login-prompt .btn-primary {
  display: inline-flex;
  text-decoration: none;
}
</style>

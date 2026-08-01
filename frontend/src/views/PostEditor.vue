<template>
  <div class="post-editor-page">
    <!-- Header -->
    <div class="editor-header">
      <button class="btn-back" @click="goBack">
        ← 返回
      </button>
      <h2 class="editor-title">✏️ 发布种草日志</h2>
      <button class="btn-submit" @click="handleSubmit" :disabled="submitting">
        {{ submitting ? '发布中...' : '发布' }}
      </button>
    </div>

    <!-- Editor body -->
    <div class="editor-body">
      <!-- Content textarea -->
      <div class="content-area">
        <textarea
          ref="textareaRef"
          v-model="content"
          class="content-input"
          placeholder="分享你的好物心得、生活日常...&#10;&#10;支持插入表情 😊"
          maxlength="5000"
          rows="8"
        ></textarea>
        <div class="char-count">{{ content.length }}/5000</div>
      </div>

      <!-- Emoji button -->
      <div class="editor-toolbar">
        <button class="btn-tool" @click="showEmojiPanel = true">
          😊 插入表情
        </button>
        <span class="tool-hint">点击表情插入到光标位置</span>
      </div>

      <!-- Display inserted emojis preview -->
      <div class="emoji-preview" v-if="insertedEmojis.length > 0">
        <span
          v-for="emoji in insertedEmojis"
          :key="emoji.id"
          class="emoji-tag"
          @click="removeEmoji(emoji)"
          title="点击移除"
        >
          <img :src="emoji.image_url" class="emoji-tag-img" />
          {{ emoji.name }}
          &times;
        </span>
      </div>

      <!-- Image upload -->
      <div class="upload-section">
        <h4 class="section-label">📷 添加图片（最多9张）</h4>
        <div class="image-upload-zone">
          <div
            v-for="(img, idx) in imagePreviews"
            :key="idx"
            class="image-preview-item"
          >
            <img :src="img" alt="preview" class="preview-img" />
            <button class="btn-remove-img" @click="removeImage(idx)">&times;</button>
          </div>
          <label class="upload-placeholder" v-if="imagePreviews.length < 9">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              multiple
              @change="handleImagesChange"
              hidden
            />
            <div class="placeholder-content">
              <span class="placeholder-icon">+</span>
              <span class="placeholder-text">{{ imagePreviews.length }}/9</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Video upload -->
      <div class="upload-section">
        <h4 class="section-label">🎬 添加视频（可选）</h4>
        <div class="video-upload-area">
          <div class="video-preview" v-if="videoPreview">
            <video :src="videoPreview" controls class="preview-video"></video>
            <button class="btn-remove-video" @click="removeVideo">&times; 移除视频</button>
          </div>
          <label class="video-upload-btn" v-else>
            <input
              type="file"
              accept="video/mp4,video/webm,video/mov"
              @change="handleVideoChange"
              hidden
            />
            <span>🎬 选择视频文件</span>
          </label>
        </div>
      </div>
    </div>

    <!-- Emoji panel -->
    <EmojiPanel
      :visible="showEmojiPanel"
      mode="picker"
      @close="showEmojiPanel = false"
      @select="insertEmoji"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'
import { createPost } from '../api/post'
import EmojiPanel from '../components/EmojiPanel.vue'

const router = useRouter()
const toast = useToast()

const content = ref('')
const textareaRef = ref(null)
const showEmojiPanel = ref(false)
const insertedEmojis = ref([])
const submitting = ref(false)

// Images
const imageFiles = ref([])
const imagePreviews = ref([])

// Video
const videoFile = ref(null)
const videoPreview = ref(null)

function goBack() {
  if (content.value.trim() || imageFiles.value.length > 0) {
    if (!confirm('确定要离开吗？未保存的内容将丢失。')) return
  }
  router.push('/grass-square')
}

function insertEmoji(emoji) {
  // Check if already inserted
  if (insertedEmojis.value.find(e => e.id === emoji.id)) return

  insertedEmojis.value.push(emoji)

  // Insert emoji tag at cursor position
  const tag = `[emoji:${emoji.id}]`
  const textarea = textareaRef.value
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    content.value = content.value.slice(0, start) + tag + content.value.slice(end)
    // Move cursor after inserted tag
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + tag.length, start + tag.length)
    }, 50)
  } else {
    content.value += tag
  }
}

function removeEmoji(emoji) {
  insertedEmojis.value = insertedEmojis.value.filter(e => e.id !== emoji.id)
  // Remove all [emoji:ID] references from content
  content.value = content.value.replace(new RegExp(`\\[emoji:${emoji.id}\\]`, 'g'), '')
}

function handleImagesChange(e) {
  const files = Array.from(e.target.files || [])
  const remaining = 9 - imageFiles.value.length
  const toAdd = files.slice(0, remaining)

  toAdd.forEach(file => {
    if (file.size > 5 * 1024 * 1024) {
      toast.error(`图片 ${file.name} 超过5MB限制`)
      return
    }
    imageFiles.value.push(file)
    imagePreviews.value.push(URL.createObjectURL(file))
  })

  if (files.length > remaining) {
    toast.info(`最多9张图片，已保留前${remaining}张`)
  }
}

function removeImage(idx) {
  URL.revokeObjectURL(imagePreviews.value[idx])
  imageFiles.value.splice(idx, 1)
  imagePreviews.value.splice(idx, 1)
}

function handleVideoChange(e) {
  const file = e.target.files?.[0]
  if (!file) return

  if (file.size > 50 * 1024 * 1024) {
    toast.error('视频大小不能超过50MB')
    return
  }

  videoFile.value = file
  videoPreview.value = URL.createObjectURL(file)
}

function removeVideo() {
  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
  videoFile.value = null
  videoPreview.value = null
}

async function handleSubmit() {
  if (!content.value.trim()) {
    toast.error('请输入内容')
    return
  }

  submitting.value = true

  try {
    const formData = new FormData()
    formData.append('content', content.value)

    // Append images
    imageFiles.value.forEach(file => {
      formData.append('images', file)
    })

    // Append video
    if (videoFile.value) {
      formData.append('video', videoFile.value)
    }

    await createPost(formData)
    toast.success('发布成功！')

    // Clean up object URLs
    imagePreviews.value.forEach(url => URL.revokeObjectURL(url))
    if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)

    // Navigate back to grass square
    router.push('/grass-square')
  } catch (e) {
    toast.error(e.msg || '发布失败，请重试')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  textareaRef.value?.focus()
})
</script>

<style scoped>
.post-editor-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

/* Header */
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 64px;
  background: var(--card-bg);
  z-index: 10;
  backdrop-filter: blur(12px);
}

.editor-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.btn-back {
  background: var(--bg);
  border: 1.5px solid var(--border);
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  min-width: auto;
}

.btn-back:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-submit {
  padding: 10px 28px;
  background: var(--gradient-primary);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
  min-width: auto;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(249, 115, 22, 0.4);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Content */
.editor-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.content-area {
  position: relative;
}

.content-input {
  width: 100%;
  min-height: 200px;
  padding: 16px;
  border: 1.5px solid var(--border);
  border-radius: 14px;
  font-size: 16px;
  line-height: 1.7;
  color: var(--text);
  background: var(--card-bg);
  resize: vertical;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.3s;
}

.content-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1);
}

.content-input::placeholder {
  color: var(--text-muted);
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-tool {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  min-width: auto;
}

.btn-tool:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

.tool-hint {
  font-size: 12px;
  color: var(--text-muted);
}

/* Emoji preview */
.emoji-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.emoji-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--primary-light);
  color: var(--primary);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.emoji-tag:hover {
  background: #FEE2E2;
  color: #EF4444;
}

.emoji-tag-img {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  object-fit: cover;
}

/* Upload sections */
.upload-section {
  background: var(--bg);
  border-radius: 14px;
  padding: 16px;
}

.section-label {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 12px;
}

/* Images */
.image-upload-zone {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.image-preview-item {
  width: 100px;
  height: 100px;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  border: 2px solid var(--border);
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.btn-remove-img {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border: none;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  min-width: auto;
  transition: background 0.2s;
}

.btn-remove-img:hover {
  background: rgba(239, 68, 68, 0.85);
}

.upload-placeholder {
  width: 100px;
  height: 100px;
  border: 2px dashed var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-placeholder:hover {
  border-color: var(--primary);
  background: var(--primary-light);
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 4px;
}

.placeholder-icon {
  font-size: 28px;
  color: var(--text-muted);
  font-weight: 300;
}

.placeholder-text {
  font-size: 11px;
  color: var(--text-muted);
}

/* Video */
.video-upload-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.video-preview {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}

.preview-video {
  width: 100%;
  max-height: 260px;
}

.btn-remove-video {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 6px 14px;
  background: rgba(239, 68, 68, 0.85);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  min-width: auto;
}

.video-upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 2px dashed var(--border);
  border-radius: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.video-upload-btn:hover {
  border-color: var(--primary);
  background: var(--primary-light);
  color: var(--primary);
}
</style>

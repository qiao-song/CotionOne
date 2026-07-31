<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content goods-form-modal">
        <h2 class="form-title">{{ isEdit ? '编辑商品' : '发布商品' }}</h2>

        <div class="form-group">
          <label>商品标题</label>
          <input v-model="form.title" type="text" placeholder="请输入商品标题" maxlength="200" />
        </div>

        <div class="form-group">
          <label>价格 (¥)</label>
          <input v-model="form.price" type="number" placeholder="0.00" step="0.01" min="0.01" />
        </div>

        <div class="form-group">
          <label>描述</label>
          <textarea v-model="form.description" placeholder="请输入商品描述" rows="3"></textarea>
        </div>

        <div class="form-group">
          <label>商品图片（最多9张，支持 jpg/png/webp）</label>
          <div class="image-upload-area">
            <div v-for="(img, index) in previewImages" :key="'keep-' + index" class="image-preview">
              <img :src="img" alt="preview" />
              <button class="remove-btn" @click="removeImage(index)">×</button>
            </div>
            <div
              v-for="(file, index) in newFiles"
              :key="'new-' + index"
              class="image-preview"
            >
              <img :src="file.preview" alt="preview" />
              <button class="remove-btn" @click="removeNewFile(index)">×</button>
            </div>
            <label v-if="totalImages < 9" class="upload-placeholder">
              <span>+</span>
              <input type="file" accept="image/jpeg,image/png,image/webp" multiple hidden @change="onFileChange" />
            </label>
          </div>
          <p class="image-count">{{ totalImages }}/9</p>
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <!-- Video upload -->
        <div class="form-group">
          <label>商品视频（可选，15秒以内，mp4/webm/mov，将在"发现"栏目播放）</label>
          <div class="video-upload-area">
            <div v-if="videoPreview" class="video-preview">
              <video :src="videoPreview" class="video-thumb" muted></video>
              <button class="remove-btn" @click="removeVideo">×</button>
            </div>
            <label v-if="!videoPreview" class="upload-video-btn">
              <span>🎬 上传视频</span>
              <input type="file" accept="video/mp4,video/webm,video/mov,video/avi" hidden @change="onVideoChange" />
            </label>
          </div>
          <p class="video-hint" v-if="!videoPreview">支持 mp4/webm/mov，视频将出现在"发现"栏目</p>
        </div>

        <div class="form-actions">
          <button class="btn-outline" @click="$emit('close')">取消</button>
          <button class="btn-primary" @click="handleSubmit" :disabled="submitting">
            {{ submitting ? '提交中...' : (isEdit ? '保存修改' : '发布商品') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useToast } from '../composables/useToast'

const props = defineProps({
  goods: { type: Object, default: null }   // null = create mode, object = edit mode
})

const emit = defineEmits(['close', 'saved'])
const toast = useToast()

const isEdit = computed(() => !!props.goods)

const form = reactive({
  title: props.goods?.title || '',
  price: props.goods?.price || '',
  description: props.goods?.description || ''
})

const previewImages = ref((props.goods?.images || []).map(u => u))
const newFiles = ref([])
const submitting = ref(false)
const errorMsg = ref('')

// Video state
const videoPreview = ref(props.goods?.video || '')
const newVideoFile = ref(null)
const removeVideoFlag = ref(false)

const totalImages = computed(() => previewImages.value.length + newFiles.value.length)

function onFileChange(e) {
  const files = Array.from(e.target.files)
  const remaining = 9 - totalImages.value
  const toAdd = files.slice(0, remaining)

  for (const file of toAdd) {
    if (file.size > 5 * 1024 * 1024) {
      toast.error('单张图片不能超过5MB')
      continue
    }
    newFiles.value.push({
      file,
      preview: URL.createObjectURL(file)
    })
  }
  e.target.value = ''
}

function removeImage(index) {
  previewImages.value.splice(index, 1)
}

function removeNewFile(index) {
  URL.revokeObjectURL(newFiles.value[index].preview)
  newFiles.value.splice(index, 1)
}

// Video handlers
function onVideoChange(e) {
  const file = e.target.files[0]
  if (!file) return

  // Check file size (50MB max)
  if (file.size > 50 * 1024 * 1024) {
    toast.error('视频文件不能超过50MB')
    e.target.value = ''
    return
  }

  // Check video duration
  const url = URL.createObjectURL(file)
  const video = document.createElement('video')
  video.preload = 'metadata'
  video.onloadedmetadata = () => {
    URL.revokeObjectURL(url)
    if (video.duration > 15) {
      toast.error('视频时长不能超过15秒')
      e.target.value = ''
      return
    }
    // Valid video
    videoPreview.value = URL.createObjectURL(file)
    newVideoFile.value = file
    removeVideoFlag.value = false
  }
  video.onerror = () => {
    URL.revokeObjectURL(url)
    toast.error('无法读取视频信息')
    e.target.value = ''
  }
  video.src = url
  e.target.value = ''
}

function removeVideo() {
  if (newVideoFile.value) {
    URL.revokeObjectURL(videoPreview.value)
    newVideoFile.value = null
  }
  videoPreview.value = ''
  removeVideoFlag.value = true
}

async function handleSubmit() {
  errorMsg.value = ''

  if (!form.title.trim()) { errorMsg.value = '请输入商品标题'; return }
  if (!form.price || parseFloat(form.price) <= 0) { errorMsg.value = '请输入有效价格'; return }
  if (totalImages.value === 0) { errorMsg.value = '请至少上传一张图片'; return }

  submitting.value = true

  try {
    const formData = new FormData()
    formData.append('title', form.title.trim())
    formData.append('price', form.price)
    formData.append('description', form.description || '')

    if (isEdit.value) {
      formData.append('keep_images', JSON.stringify(previewImages.value))
      if (removeVideoFlag.value) {
        formData.append('remove_video', '1')
      }
    }

    for (const { file } of newFiles.value) {
      formData.append('images', file)
    }

    // Append video if new one selected
    if (newVideoFile.value) {
      formData.append('video', newVideoFile.value)
    }

    const { createGoods, updateGoods } = await import('../api/goods')
    if (isEdit.value) {
      await updateGoods(props.goods.id, formData)
    } else {
      await createGoods(formData)
    }

    emit('saved')
    toast.success(isEdit.value ? '商品更新成功' : '商品发布成功')
  } catch (e) {
    toast.error(e.msg || '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.goods-form-modal {
  max-width: 560px;
  width: 95%;
}

.form-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--text);
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 6px;
}

.image-upload-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.image-preview {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  position: relative;
  border: 1px solid var(--border);
}

.image-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: auto;
  padding: 0;
  line-height: 1;
}

.upload-placeholder {
  width: 80px;
  height: 80px;
  border: 2px dashed var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 28px;
  cursor: pointer;
  transition: all var(--transition);
}

.upload-placeholder:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.image-count {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}

/* Video upload */
.video-upload-area {
  display: flex;
  align-items: center;
}

.video-preview {
  width: 160px;
  height: 90px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  position: relative;
  border: 1px solid var(--border);
  background: #000;
}

.video-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-video-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: 2px dashed var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all var(--transition);
}

.upload-video-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.video-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 6px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.error-msg {
  color: #EF4444;
  font-size: 14px;
  margin-top: 8px;
}
</style>

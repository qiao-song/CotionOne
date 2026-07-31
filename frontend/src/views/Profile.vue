<template>
  <div class="profile-page">
    <h1 class="page-title">个人中心</h1>

    <!-- Balance & Spending Summary -->
    <div class="balance-row" v-if="balanceData">
      <div class="card balance-card">
        <div class="balance-label">账户余额</div>
        <div class="balance-value">¥{{ parseFloat(balanceData.balance).toFixed(2) }}</div>
        <router-link to="/games" class="btn-play-game">🎮 玩游戏赚余额</router-link>
      </div>
      <div class="card balance-card">
        <div class="balance-label">累计消费</div>
        <div class="balance-value spent">¥{{ parseFloat(balanceData.total_spent).toFixed(2) }}</div>
      </div>
      <div class="card balance-card">
        <div class="balance-label">订单数量</div>
        <div class="balance-value">{{ balanceData.order_count }}</div>
      </div>
    </div>

    <div class="profile-grid">
      <!-- Avatar & Info Section -->
      <div class="card profile-card">
        <div class="avatar-section">
          <div class="avatar-wrapper" @click="triggerAvatarUpload">
            <img :src="authStore.user?.avatar || '/static/default.png'" class="avatar-img" alt="avatar" />
            <div class="avatar-overlay">
              <span>更换头像</span>
            </div>
          </div>
          <input
            ref="avatarInput"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            hidden
            @change="handleAvatarChange"
          />
          <div class="nickname-section">
            <div class="user-name-display" v-if="!editingNickname">
              {{ authStore.user?.username }}
              <button class="btn-edit-nick" @click="startEditNickname" title="修改昵称">✎</button>
            </div>
            <div class="nickname-edit" v-else>
              <input
                ref="nicknameInput"
                v-model="nickname"
                class="nickname-input"
                maxlength="50"
                placeholder="输入新昵称"
                @keyup.enter="saveNickname"
                @keyup.escape="cancelEditNickname"
              />
              <button class="btn-save-nick" @click="saveNickname" :disabled="nicknameSaving">
                {{ nicknameSaving ? '...' : '保存' }}
              </button>
              <button class="btn-cancel-nick" @click="cancelEditNickname">取消</button>
            </div>
          </div>
          <p class="upload-hint">点击头像上传（jpg/png/webp，小于5MB）</p>
        </div>
      </div>

      <!-- Change Password Section -->
      <div class="card password-card">
        <h3 class="card-title">修改密码</h3>
        <div class="form-group">
          <label>原密码</label>
          <input v-model="oldPassword" type="password" placeholder="请输入原密码" />
        </div>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="newPassword" type="password" placeholder="至少6位" />
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <input v-model="confirmNewPassword" type="password" placeholder="再次输入新密码" />
        </div>
        <button class="btn-primary" @click="handleChangePassword" :disabled="pwdLoading">
          {{ pwdLoading ? '保存中...' : '修改密码' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { updateProfile, changePassword, getBalance } from '../api/user'

const authStore = useAuthStore()
const toast = useToast()

const balanceData = ref(null)

async function fetchBalance() {
  try {
    const res = await getBalance()
    balanceData.value = res.data
  } catch {
    // silent
  }
}

// Avatar
const avatarInput = ref(null)

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

async function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return

  if (file.size > 5 * 1024 * 1024) {
    toast.error('图片不能超过5MB')
    return
  }

  const validTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!validTypes.includes(file.type)) {
    toast.error('仅支持 jpg/png/webp 格式')
    return
  }

  try {
    const formData = new FormData()
    formData.append('avatar', file)
    const res = await updateProfile(formData)
    authStore.user = res.data
    toast.success('头像更新成功')
  } catch (e) {
    toast.error(e.msg || '上传失败')
  } finally {
    e.target.value = ''
  }
}

// Nickname
const editingNickname = ref(false)
const nickname = ref('')
const nicknameSaving = ref(false)
const nicknameInput = ref(null)

function startEditNickname() {
  nickname.value = authStore.user?.username || ''
  editingNickname.value = true
  nextTick(() => {
    nicknameInput.value?.focus()
    nicknameInput.value?.select()
  })
}

function cancelEditNickname() {
  editingNickname.value = false
  nickname.value = ''
}

async function saveNickname() {
  const val = nickname.value.trim()
  if (!val) { toast.error('昵称不能为空'); return }
  if (val.length < 2) { toast.error('昵称至少2个字符'); return }
  if (val === authStore.user?.username) { editingNickname.value = false; return }

  nicknameSaving.value = true
  try {
    const formData = new FormData()
    formData.append('username', val)
    const res = await updateProfile(formData)
    authStore.user = res.data
    toast.success('昵称修改成功')
    editingNickname.value = false
  } catch (e) {
    toast.error(e.msg || '修改失败')
  } finally {
    nicknameSaving.value = false
  }
}

// Password
const oldPassword = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')
const pwdLoading = ref(false)

async function handleChangePassword() {
  if (!oldPassword.value) { toast.error('请输入原密码'); return }
  if (!newPassword.value || newPassword.value.length < 6) { toast.error('新密码至少6位'); return }
  if (newPassword.value !== confirmNewPassword.value) { toast.error('两次密码不一致'); return }

  pwdLoading.value = true
  try {
    await changePassword({
      old_password: oldPassword.value,
      new_password: newPassword.value
    })
    toast.success('密码修改成功')
    oldPassword.value = ''
    newPassword.value = ''
    confirmNewPassword.value = ''
  } catch (e) {
    toast.error(e.msg || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}

onMounted(() => {
  fetchBalance()
})
</script>

<style scoped>
.profile-page {
  padding-bottom: 40px;
}

.balance-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .balance-row {
    grid-template-columns: 1fr;
  }
}

.balance-card {
  text-align: center;
  padding: 28px 20px;
  position: relative;
  overflow: hidden;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.balance-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #F97316, #FBBF24);
  opacity: 0;
  transition: opacity 0.3s;
}

.balance-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgba(249, 115, 22, 0.1);
  border-color: rgba(249, 115, 22, 0.12);
}

.balance-card:hover::before {
  opacity: 1;
}

.balance-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.balance-value {
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(135deg, #F97316, #EA580C);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.balance-value.spent {
  background: linear-gradient(135deg, #6B7280, #374151);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.btn-play-game {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 8px 20px;
  border-radius: 20px;
  background: linear-gradient(135deg, #7C3AED, #8B5CF6);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 10px rgba(124, 58, 237, 0.3);
}

.btn-play-game:hover {
  background: linear-gradient(135deg, #8B5CF6, #A78BFA);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(124, 58, 237, 0.4);
  color: #fff;
}

.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

@media (max-width: 768px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}

.profile-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}

.avatar-section {
  text-align: center;
}

.avatar-wrapper {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 16px;
  cursor: pointer;
  position: relative;
  border: 3px solid var(--primary-light);
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

.avatar-wrapper:hover {
  border-color: var(--primary);
  box-shadow: 0 8px 24px rgba(249, 115, 22, 0.2);
  transform: scale(1.03);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.avatar-wrapper:hover .avatar-img {
  transform: scale(1.05);
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  opacity: 0;
  transition: opacity var(--transition);
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.user-name-display {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-edit-nick {
  min-width: auto;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1.5px solid var(--border);
  border-radius: 50%;
  background: #fff;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-edit-nick:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

.nickname-section {
  margin-bottom: 4px;
}

.nickname-edit {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.nickname-input {
  width: 160px;
  height: 36px;
  font-size: 14px;
  text-align: center;
  border-radius: 8px;
}

.btn-save-nick {
  min-width: auto;
  padding: 0 14px;
  height: 36px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  background: var(--gradient-primary);
  color: #fff;
}

.btn-save-nick:disabled {
  opacity: 0.5;
}

.btn-cancel-nick {
  min-width: auto;
  padding: 0 14px;
  height: 36px;
  font-size: 13px;
  background: #F3F4F6;
  color: var(--text-secondary);
  border-radius: 8px;
}

.btn-cancel-nick:hover {
  background: #E5E7EB;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

.password-card {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text);
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 6px;
}

.password-card .btn-primary {
  margin-top: 8px;
  align-self: flex-start;
}

.error-msg {
  color: #EF4444;
  font-size: 14px;
  margin-bottom: 8px;
}

.success-msg {
  color: var(--accent);
  font-size: 14px;
  margin-bottom: 8px;
}
</style>

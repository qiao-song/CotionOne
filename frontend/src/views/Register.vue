<template>
  <div class="register-page">
    <div class="register-card">
      <!-- Logo -->
      <div class="logo-area">
        <router-link to="/" class="logo-text">Tbao</router-link>
        <p class="logo-subtitle">创建你的账号</p>
      </div>

      <!-- Register Form -->
      <div class="register-form">
        <div class="form-group">
          <input
            v-model="username"
            type="text"
            placeholder="用户名"
            @keyup.enter="handleRegister"
          />
        </div>
        <div class="form-group">
          <input
            v-model="phone"
            type="text"
            placeholder="手机号"
            maxlength="11"
            @keyup.enter="handleRegister"
          />
        </div>
        <div class="form-group">
          <input
            v-model="password"
            type="password"
            placeholder="密码（至少6位）"
            @keyup.enter="handleRegister"
          />
        </div>
        <div class="form-group">
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="确认密码"
            @keyup.enter="handleRegister"
          />
        </div>
        <button class="btn-primary btn-full" @click="handleRegister" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </div>

      <!-- Login link -->
      <p class="login-link">
        已有账号？<router-link to="/login">立即登录</router-link>
      </p>

      <!-- Error -->
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <!-- Footer -->
      <p class="footer-text">@XS赞助推出</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const username = ref('')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleRegister() {
  errorMsg.value = ''

  if (!username.value) { errorMsg.value = '请输入用户名'; return }
  if (username.value.length < 2) { errorMsg.value = '用户名至少2个字符'; return }
  if (!phone.value) { errorMsg.value = '请输入手机号'; return }
  if (!/^1\d{10}$/.test(phone.value)) { errorMsg.value = '手机号格式不正确'; return }
  if (!password.value) { errorMsg.value = '请输入密码'; return }
  if (password.value.length < 6) { errorMsg.value = '密码至少6位'; return }
  if (password.value !== confirmPassword.value) { errorMsg.value = '两次密码不一致'; return }

  loading.value = true

  try {
    await authStore.register({
      username: username.value,
      phone: phone.value,
      password: password.value
    })
    router.push('/')
  } catch (e) {
    toast.error(e.msg || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.register-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
}

.logo-area {
  text-align: center;
  margin-bottom: 32px;
}

.logo-text {
  font-size: 48px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -1px;
}

.logo-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  width: 100%;
}

.btn-full {
  width: 100%;
  min-width: auto;
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 20px;
}

.login-link a {
  color: var(--primary);
  font-weight: 500;
}

.error-msg {
  color: #EF4444;
  font-size: 14px;
  text-align: center;
  margin-top: 12px;
}

.footer-text {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}
</style>

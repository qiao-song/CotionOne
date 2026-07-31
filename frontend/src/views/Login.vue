<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="logo-area">
        <router-link to="/" class="logo-text">Tbao</router-link>
        <p class="logo-subtitle">精选好物，品质生活</p>
      </div>

      <!-- Login Form -->
      <div class="login-form">
        <!-- Password login mode -->
        <template v-if="loginMode === 'password'">
          <div class="form-group">
            <input
              v-model="username"
              type="text"
              placeholder="用户名"
              @keyup.enter="handleLogin"
            />
          </div>
          <div class="form-group">
            <input
              v-model="password"
              type="password"
              placeholder="密码"
              @keyup.enter="handleLogin"
            />
          </div>
          <button class="btn-primary btn-full" @click="handleLogin" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </template>

        <!-- SMS login mode -->
        <template v-else>
          <div class="form-group">
            <input
              v-model="phone"
              type="text"
              placeholder="手机号"
              maxlength="11"
              @keyup.enter="handleLogin"
            />
          </div>
          <div class="form-group code-row">
            <input
              v-model="code"
              type="text"
              placeholder="验证码"
              maxlength="6"
              style="flex:1;"
              @keyup.enter="handleLogin"
            />
            <button
              class="btn-outline btn-sm"
              style="min-width:120px;flex-shrink:0;"
              @click="handleSendCode"
              :disabled="countdown > 0"
            >
              {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
            </button>
          </div>
          <button class="btn-primary btn-full" @click="handleLogin" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </template>

        <!-- Toggle login mode -->
        <p class="toggle-text">
          <a href="#" @click.prevent="toggleMode">
            {{ loginMode === 'password' ? '使用验证码登录' : '使用密码登录' }}
          </a>
        </p>

        <!-- Register link -->
        <p class="register-link">
          还没有账号？<router-link to="/register">立即注册</router-link>
        </p>
      </div>

      <!-- Error -->
      <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

      <!-- Footer -->
      <p class="footer-text">@XS赞助推出</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { sendCode } from '../api/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toast = useToast()

const loginMode = ref('password')
const loading = ref(false)
const errorMsg = ref('')

// Password mode
const username = ref('')
const password = ref('')

// SMS mode
const phone = ref('')
const code = ref('')
const countdown = ref(0)

function toggleMode() {
  loginMode.value = loginMode.value === 'password' ? 'sms' : 'password'
  errorMsg.value = ''
}

async function handleSendCode() {
  if (!phone.value) {
    errorMsg.value = '请输入手机号'
    return
  }
  if (!/^1\d{10}$/.test(phone.value)) {
    errorMsg.value = '手机号格式不正确'
    return
  }
  try {
    await sendCode(phone.value)
    errorMsg.value = ''
    // Start countdown
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    toast.error(e.msg || '发送失败')
  }
}

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true

  try {
    let loginData = {}
    if (loginMode.value === 'password') {
      if (!username.value) { errorMsg.value = '请输入用户名'; loading.value = false; return }
      if (!password.value) { errorMsg.value = '请输入密码'; loading.value = false; return }
      loginData = { username: username.value, password: password.value }
    } else {
      if (!phone.value) { errorMsg.value = '请输入手机号'; loading.value = false; return }
      if (!code.value) { errorMsg.value = '请输入验证码'; loading.value = false; return }
      loginData = { phone: phone.value, code: code.value }
    }

    await authStore.login(loginData)

    // Redirect back
    const redirect = route.query.redirect
    router.push(redirect || '/')
  } catch (e) {
    toast.error(e.msg || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
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

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  width: 100%;
}

.code-row {
  display: flex;
  gap: 12px;
}

.btn-full {
  width: 100%;
  min-width: auto;
}

.toggle-text {
  text-align: center;
  font-size: 14px;
}

.toggle-text a {
  color: var(--primary);
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
}

.register-link a {
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

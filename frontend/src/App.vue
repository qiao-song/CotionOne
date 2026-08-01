<template>
  <Toast ref="toastRef" />
  <router-view />
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import Toast from './components/Toast.vue'
import { useAuthStore } from './stores/auth'

const toastRef = ref(null)
const authStore = useAuthStore()

provide('toast', {
  show: (msg, type, duration) => toastRef.value?.show(msg, type, duration),
  success: (msg, duration) => toastRef.value?.success(msg, duration),
  error: (msg, duration) => toastRef.value?.error(msg, duration)
})

// Restore login state on every page load via JWT cookie
onMounted(() => {
  authStore.fetchUser()
})
</script>

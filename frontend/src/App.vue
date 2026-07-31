<template>
  <Toast ref="toastRef" />
  <router-view />
</template>

<script setup>
import { ref, provide } from 'vue'
import Toast from './components/Toast.vue'

const toastRef = ref(null)

provide('toast', {
  show: (msg, type, duration) => toastRef.value?.show(msg, type, duration),
  success: (msg, duration) => toastRef.value?.success(msg, duration),
  error: (msg, duration) => toastRef.value?.error(msg, duration)
})
</script>

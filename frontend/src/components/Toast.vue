<template>
  <Teleport to="body">
    <div class="toast-container">
      <div
        v-for="t in toasts"
        :key="t.id"
        :class="['toast', `toast-${t.type}`]"
      >
        {{ t.message }}
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
let id = 0

function show(message, type = 'info', duration = 3000) {
  const toast = { id: ++id, message, type }
  toasts.value.push(toast)
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== toast.id)
  }, duration)
}

function success(message, duration) {
  show(message, 'success', duration)
}

function error(message, duration) {
  show(message, 'error', duration || 4000)
}

defineExpose({ show, success, error })
</script>

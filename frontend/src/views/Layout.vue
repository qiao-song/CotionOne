<template>
  <div class="layout">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue'
</script>

<style scoped>
.layout {
  min-height: 100vh;
  background: var(--bg);
}

.main-content {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}
</style>

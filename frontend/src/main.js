import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/global.css'
import { initTheme } from './config/themes'

// Apply saved theme before mounting to avoid flash
initTheme()

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

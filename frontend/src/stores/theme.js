import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { THEME_KEYS, THEMES, THEME_LABELS, getSavedTheme, applyTheme } from '../config/themes'

export const useThemeStore = defineStore('theme', () => {
  const current = ref(getSavedTheme())

  const currentTheme = computed(() => THEMES[current.value] || THEMES[THEME_KEYS.DEFAULT])
  const currentLabel = computed(() => THEME_LABELS[current.value] || THEME_LABELS[THEME_KEYS.DEFAULT])

  const themeOptions = computed(() =>
    Object.entries(THEMES).map(([key, theme]) => ({
      key,
      label: theme.label,
      description: theme.description,
      preview: theme.preview,
      active: key === current.value
    }))
  )

  function setTheme(key) {
    if (!THEMES[key]) return
    current.value = key
    applyTheme(key)
  }

  return { current, currentTheme, currentLabel, themeOptions, setTheme }
})

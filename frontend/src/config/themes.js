/**
 * Tbao 主题配置
 *
 * 三套主题风格完全不同，切换时视觉变化明显：
 *   经典橘橙色 — 温暖活力，电商经典配色
 *   清冷东方韵 — 冷色调，玉绿+墨蓝+雾灰，东方水墨意境
 *   松弛疗愈感 — 暖沙粉+鼠尾草绿+奶杏底，SPA疗愈氛围
 */

export const THEME_KEYS = {
  DEFAULT: 'default',
  SAGE_WINE: 'sageWine',
  TERRACOTTA_BLUE: 'terracottaBlue'
}

export const THEME_LABELS = {
  [THEME_KEYS.DEFAULT]: '经典橘橙色',
  [THEME_KEYS.SAGE_WINE]: '清冷东方韵',
  [THEME_KEYS.TERRACOTTA_BLUE]: '松弛疗愈感'
}

export const THEMES = {
  [THEME_KEYS.DEFAULT]: {
    label: THEME_LABELS[THEME_KEYS.DEFAULT],
    description: '活力橘橙为主，经典电商暖调配色',
    preview: ['#F97316', '#22C55E', '#FAFAF8'],
    css: {
      '--primary': '#F97316',
      '--primary-light': 'rgba(249, 115, 22, 0.1)',
      '--primary-dark': '#EA580C',
      '--accent': '#22C55E',
      '--accent-light': 'rgba(34, 197, 94, 0.1)',
      '--bg': '#FAFAF8',
      '--card-bg': '#FFFFFF',
      '--text': '#1F2937',
      '--text-secondary': '#6B7280',
      '--text-muted': '#9CA3AF',
      '--border': '#E5E7EB',
      '--border-light': '#F3F4F6',
      '--nav-bg': 'rgba(255, 255, 255, 0.85)',
      '--bg-glow-1': 'rgba(249,115,22,0.04)',
      '--bg-glow-2': 'rgba(139,92,246,0.03)',
      '--gradient-primary': 'linear-gradient(135deg, #F97316 0%, #EA580C 100%)',
      '--gradient-warm': 'linear-gradient(135deg, #F97316, #FBBF24)',
      '--shadow-btn': '0 2px 8px rgba(249,115,22,0.3)',
      '--shadow-btn-hover': '0 4px 16px rgba(249,115,22,0.4)',
      '--btn-outline-hover-bg': 'rgba(249,115,22,0.04)',
    }
  },

  /* ================================================================
   * 清冷东方韵 — Cool Eastern Elegance
   * 玉绿为骨，墨蓝为魂，雾灰为底
   * 冷色调搭配营造东方水墨的清冷高级感
   * ================================================================ */
  [THEME_KEYS.SAGE_WINE]: {
    label: THEME_LABELS[THEME_KEYS.SAGE_WINE],
    description: '玉绿+墨蓝+雾灰底，清冷东方水墨意境',
    preview: ['#4D9585', '#2E4057', '#EEF1F0'],
    css: {
      '--primary': '#4D9585',
      '--primary-light': 'rgba(77, 149, 133, 0.12)',
      '--primary-dark': '#397A6B',
      '--accent': '#2E4057',
      '--accent-light': 'rgba(46, 64, 87, 0.1)',
      '--bg': '#EEF1F0',
      '--card-bg': '#F7F9F8',
      '--text': '#1C2833',
      '--text-secondary': '#556270',
      '--text-muted': '#8494A0',
      '--border': '#D5DCD9',
      '--border-light': '#E4EAE7',
      '--nav-bg': 'rgba(247, 249, 248, 0.88)',
      '--bg-glow-1': 'rgba(77, 149, 133, 0.06)',
      '--bg-glow-2': 'rgba(46, 64, 87, 0.03)',
      '--gradient-primary': 'linear-gradient(135deg, #4D9585 0%, #397A6B 100%)',
      '--gradient-warm': 'linear-gradient(135deg, #4D9585, #7DB8A8)',
      '--shadow-btn': '0 2px 8px rgba(77, 149, 133, 0.3)',
      '--shadow-btn-hover': '0 4px 16px rgba(77, 149, 133, 0.4)',
      '--btn-outline-hover-bg': 'rgba(77, 149, 133, 0.06)',
    }
  },

  /* ================================================================
   * 松弛疗愈感 — Relaxed Healing
   * 暖沙粉为主，鼠尾草绿作辅，奶杏底包裹
   * 温暖大地色调营造 SPA 般松弛疗愈氛围
   * ================================================================ */
  [THEME_KEYS.TERRACOTTA_BLUE]: {
    label: THEME_LABELS[THEME_KEYS.TERRACOTTA_BLUE],
    description: '暖沙粉+鼠尾绿+奶杏底，SPA疗愈氛围',
    preview: ['#C0907A', '#6B9E85', '#F6F0EA'],
    css: {
      '--primary': '#C0907A',
      '--primary-light': 'rgba(192, 144, 122, 0.12)',
      '--primary-dark': '#A07662',
      '--accent': '#6B9E85',
      '--accent-light': 'rgba(107, 158, 133, 0.12)',
      '--bg': '#F6F0EA',
      '--card-bg': '#FFFCF9',
      '--text': '#3D322E',
      '--text-secondary': '#7A6A62',
      '--text-muted': '#A8958C',
      '--border': '#E0D6CC',
      '--border-light': '#EFE8DF',
      '--nav-bg': 'rgba(255, 252, 249, 0.90)',
      '--bg-glow-1': 'rgba(192, 144, 122, 0.06)',
      '--bg-glow-2': 'rgba(107, 158, 133, 0.04)',
      '--gradient-primary': 'linear-gradient(135deg, #C0907A 0%, #A07662 100%)',
      '--gradient-warm': 'linear-gradient(135deg, #C0907A, #DCC0A8)',
      '--shadow-btn': '0 2px 8px rgba(192, 144, 122, 0.3)',
      '--shadow-btn-hover': '0 4px 16px rgba(192, 144, 122, 0.4)',
      '--btn-outline-hover-bg': 'rgba(192, 144, 122, 0.06)',
    }
  }
}

export function getSavedTheme() {
  try {
    const saved = localStorage.getItem('tbao_theme')
    if (saved && THEMES[saved]) return saved
  } catch { /* ignore */ }
  return THEME_KEYS.DEFAULT
}

export function applyTheme(themeKey) {
  const theme = THEMES[themeKey] || THEMES[THEME_KEYS.DEFAULT]
  const root = document.documentElement

  Object.entries(theme.css).forEach(([prop, value]) => {
    root.style.setProperty(prop, value)
  })

  root.setAttribute('data-theme', themeKey)

  try {
    localStorage.setItem('tbao_theme', themeKey)
  } catch { /* ignore */ }
}

export function initTheme() {
  applyTheme(getSavedTheme())
}

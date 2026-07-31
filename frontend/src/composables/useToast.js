import { inject } from 'vue'

export function useToast() {
  const toast = inject('toast', null)
  if (!toast) {
    // Fallback when used outside provider (e.g., in router guard before app mounts)
    return {
      show: (msg, type = 'info') => console.log(`[Toast:${type}]`, msg),
      success: (msg) => console.log('[Toast:success]', msg),
      error: (msg) => console.log('[Toast:error]', msg)
    }
  }
  return toast
}

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useCartStore = defineStore('cart', () => {
  // Initialize from localStorage
  const stored = localStorage.getItem('tbao_cart')
  const items = ref(stored ? JSON.parse(stored) : [])

  // Persist to localStorage on every change
  watch(items, (val) => {
    localStorage.setItem('tbao_cart', JSON.stringify(val))
  }, { deep: true })

  // Getters
  const selectedItems = computed(() => items.value.filter(i => i.selected))
  const totalAmount = computed(() =>
    selectedItems.value.reduce((sum, i) => sum + parseFloat(i.price) * i.quantity, 0)
  )
  const selectedCount = computed(() =>
    selectedItems.value.reduce((sum, i) => sum + i.quantity, 0)
  )
  const cartCount = computed(() =>
    items.value.reduce((sum, i) => sum + i.quantity, 0)
  )
  const isAllSelected = computed(() =>
    items.value.length > 0 && items.value.every(i => i.selected)
  )

  // Actions
  function addItem(goods, quantity = 1) {
    const existing = items.value.find(i => i.goods_id === goods.id)
    if (existing) {
      existing.quantity += quantity
    } else {
      items.value.push({
        goods_id: goods.id,
        title: goods.title,
        price: goods.price,
        image: goods.images?.[0] || '',
        quantity,
        selected: true,
        seller_id: goods.seller_id,
        seller_name: goods.seller_name
      })
    }
  }

  function removeItem(goodsId) {
    items.value = items.value.filter(i => i.goods_id !== goodsId)
  }

  function updateQty(goodsId, qty) {
    const item = items.value.find(i => i.goods_id === goodsId)
    if (item) {
      item.quantity = Math.max(1, Math.min(99, qty))
    }
  }

  function toggleSelect(goodsId) {
    const item = items.value.find(i => i.goods_id === goodsId)
    if (item) {
      item.selected = !item.selected
    }
  }

  function toggleSelectAll() {
    const newVal = !isAllSelected.value
    items.value.forEach(i => { i.selected = newVal })
  }

  function clearCart() {
    items.value = []
  }

  function clearSelected() {
    items.value = items.value.filter(i => !i.selected)
  }

  return {
    items, selectedItems, totalAmount, selectedCount, cartCount, isAllSelected,
    addItem, removeItem, updateQty, toggleSelect, toggleSelectAll, clearCart, clearSelected
  }
})

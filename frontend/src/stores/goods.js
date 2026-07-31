import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getGoodsList } from '../api/goods'

export const useGoodsStore = defineStore('goods', () => {
  const items = ref([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)

  async function fetchGoods(p = 1) {
    try {
      loading.value = true
      page.value = p
      const res = await getGoodsList({ page: p, page_size: pageSize.value })
      if (p === 1) {
        items.value = res.data.items
      } else {
        items.value.push(...res.data.items)
      }
      total.value = res.data.total
    } catch {
      // ignore
    } finally {
      loading.value = false
    }
  }

  function reset() {
    items.value = []
    total.value = 0
    page.value = 1
  }

  return { items, total, page, pageSize, loading, fetchGoods, reset }
})

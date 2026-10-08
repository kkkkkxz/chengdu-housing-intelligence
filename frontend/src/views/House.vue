<template>
  <div class="p-4">
    <n-card>
      <HouseSearch v-model="q" @search="() => loadData(1)" />
    </n-card>

    <div class="mt-4">
      <n-grid :cols="2" x-gap="16" y-gap="16" responsive="screen">
        <n-gi v-for="item in (loading ? skeletonItems : items)" :key="item.id || item">
          <n-skeleton v-if="loading" :height="160" :sharp="false" animated />
          <HouseCard v-else :house="item" @detail="goDetail" @favorite="onFavorite" />
        </n-gi>
      </n-grid>
    </div>

    <div class="mt-4 flex items-center justify-end">
      <n-pagination
        :page="pagination.page"
        :page-size="pagination.pageSize"
        :page-count="pagination.pageCount"
        show-size-picker
        :page-sizes="pagination.pageSizes"
        @update:page="(p) => loadData(p)"
        @update:page-size="onUpdatePageSize"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listingsApi, type HouseQuery } from '../api/listings'

const router = useRouter()

const q = ref<HouseQuery>({
    page: 1,
    page_size: 12,
    search: '',
    rooms: undefined,
    price_min: undefined,
    halls: undefined,
    ordering: '-created_at'
})

const loading = ref(false)
const items = ref<any[]>([])
const total = ref(0)
const skeletonItems = Array.from({ length: 8 }).map((_, i) => i)

const pagination = reactive({
  page: 1,
  pageSize: 12,
  pageCount: 0,
  pageSizes: [8, 16, 32]
})

function onUpdatePageSize(size: number) {
  q.value.page_size = size
  pagination.pageSize = size
  loadData(1)
}

async function loadData(page = 1) {
  loading.value = true
  q.value.page = page
  try {
    const res: any = await listingsApi.getHouses(q.value)
    items.value = res.results || res.data || res
    total.value = res.count || items.value.length
    pagination.page = page
    pagination.pageCount = Math.ceil(total.value / (q.value.page_size || 12))
    
    // 调试：检查图片 URL
    if (items.value.length > 0) {
      console.log('房源数据示例:', {
        id: items.value[0].id,
        title: items.value[0].title,
        cover: items.value[0].cover,
        coverType: typeof items.value[0].cover
      })
    }
  } catch (error) {
    console.error('加载房源数据失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

function goDetail(house: any) {
  router.push(`/houses/${house.id}`)
}

async function onFavorite(house: any) {
  if (house.is_favorited) {
    await listingsApi.unfavorite(house.id)
    house.is_favorited = false
  } else {
    await listingsApi.favorite(house.id)
    house.is_favorited = true
  }
}
</script>
<style scoped>
</style>
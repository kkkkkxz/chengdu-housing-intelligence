<template>
  <div class="favorites-page">
    <n-card>
      <div class="filter-row">
        <n-input
          :value="q.search"
          class="w-280px"
          placeholder="搜索收藏(标题/小区/城市)"
          @keyup.enter="load(1)"
          @update:value="(v) => (q.search = v)"
        />
        <n-select
          :value="q.city"
          :options="cityOptions"
          class="w-160px"
          clearable
          placeholder="城市"
          @update:value="onUpdateCity"
        />
        <n-select
          :value="q.ordering"
          :options="orderingOptions"
          class="w-180px"
          clearable
          placeholder="排序"
          @update:value="onUpdateOrdering"
        />
        <n-button type="primary" @click="load(1)">查询</n-button>
      </div>
    </n-card>

    <div class="favorites-grid">
      <n-grid :cols="2" x-gap="16" y-gap="16" responsive="screen">
        <n-gi v-for="item in (loading ? skeletonItems : rows)" :key="item?.id || item">
          <n-skeleton v-if="loading" :height="160" :sharp="false" animated />
          <template v-else>
            <HouseCard
              v-if="item?.house"
              :house="item.house"
              @detail="goToDetail"
              @favorite="() => toggleFavorite(item)"
            />
          </template>
        </n-gi>
      </n-grid>
      <n-empty v-if="!loading && rows.length === 0" description="暂无收藏数据" />
    </div>

    <div class="favorites-pagination">
      <n-pagination
        :page="pagination.page"
        :page-size="pagination.pageSize"
        :page-count="pagination.pageCount"
        show-size-picker
        :page-sizes="pagination.pageSizes"
        @update:page="(p) => load(p)"
        @update:page-size="onUpdatePageSize"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listingsApi } from '@/api/listings'

const DEFAULT_PAGE_SIZE = 12

interface FavoriteQuery {
  page: number
  page_size: number
  search: string
  city: string | null
  ordering: string | null
}

interface CityOption {
  label: string
  value: string
  count?: number
}

const router = useRouter()
const loading = ref(false)
const rows = ref<any[]>([])

const pagination = ref({
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  pageCount: 0,
  pageSizes: [8, 12, 16, 24],
})

const q = ref<FavoriteQuery>({
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
  search: '',
  city: null,
  ordering: '-created_at',
})

const cityOptions = ref<{ label: string; value: string }[]>([])
const orderingOptions = [
  { label: '最新收藏', value: '-created_at' },
  { label: '价格升序', value: 'house__total_price' },
  { label: '价格降序', value: '-house__total_price' },
]

const skeletonItems = Array.from({ length: 8 }).map((_, i) => i)

function mapCityOptions(cities: CityOption[] | undefined) {
  if (!Array.isArray(cities)) {
    cityOptions.value = []
    return
  }
  cityOptions.value = cities
    .filter((item) => typeof item.value === 'string' && item.value.trim().length > 0)
    .map((item) => {
      const labelText = item.label?.trim().length ? item.label.trim() : item.value
      const countText = typeof item.count === 'number' ? ` (${item.count})` : ''
      return {
        label: `${labelText}${countText}`,
        value: item.value,
      }
    })
}

function onUpdatePageSize(size: number) {
  q.value.page_size = size
  pagination.value.pageSize = size
  load(1)
}

function onUpdateCity(v: unknown) {
  const value = (v as string) || ''
  q.value.city = value || null
  load(1)
}

function onUpdateOrdering(v: unknown) {
  q.value.ordering = (v as string) || null
  load(1)
}

async function load(page = 1) {
  loading.value = true
  q.value.page = page
  try {
    const res: any = await listingsApi.myFavorites({ ...q.value })
    const data = Array.isArray(res?.results)
      ? res.results
      : Array.isArray(res?.data)
      ? res.data
      : Array.isArray(res)
      ? res
      : []
    rows.value = data
    const total = typeof res?.count === 'number' ? res.count : data.length
    const pageSize = q.value.page_size || pagination.value.pageSize || DEFAULT_PAGE_SIZE
    pagination.value.page = page
    pagination.value.pageSize = pageSize
    pagination.value.pageCount = Math.max(1, Math.ceil((total || 0) / pageSize))
    mapCityOptions(res?.meta?.cities)
  } finally {
    loading.value = false
  }
}

async function toggleFavorite(item: any) {
  if (!item?.house) return
  await listingsApi.unfavorite(item.house.id)
  const currentPage = pagination.value.page
  const remainingAfterRemoval = rows.value.length - 1
  const nextPage = remainingAfterRemoval > 0 ? currentPage : Math.max(1, currentPage - 1)
  await load(nextPage)
}

onMounted(() => {
  load()
})

function goToDetail(h: any) {
  router.push(`/houses/${h.id}`)
}
</script>

<style scoped>
.favorites-page {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.favorites-grid {
  flex: 1;
  overflow: auto;
}

.favorites-pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
<template>
  <div class="recommend-page">
    <n-card>
      <div class="recommend-header">
        <div>
          <div class="header-title">为你精选的房源推荐</div>
          <div class="header-desc">
            推荐结果基于收藏行为进行协同过滤。若推荐不足，会自动补充随机房源供参考。
          </div>
        </div>
        <div class="summary-info">
          <n-statistic label="推荐数量" :value="summary.total" />
        </div>
        <n-button type="primary" @click="load">刷新推荐</n-button>
      </div>
    </n-card>

    <div class="recommend-grid">
      <template v-if="loading">
        <n-grid :cols="2" x-gap="16" y-gap="16" responsive="screen">
          <n-gi v-for="item in skeletonItems" :key="item">
            <n-skeleton :height="160" :sharp="false" animated />
          </n-gi>
        </n-grid>
      </template>
      <template v-else>
        <n-empty v-if="items.length === 0" description="暂无推荐结果，请稍后再试">
          <template #extra>
            <n-button @click="load">重新获取</n-button>
          </template>
        </n-empty>
        <n-grid v-else :cols="2" x-gap="24" y-gap="20" responsive="screen">
          <n-gi v-for="item in items" :key="item.house.id">
            <HouseCard
              :house="item.house"
              :meta="{ source: item.source, score: item.score }"
              @detail="(h) => router.push(`/houses/${h.id}`)"
              @favorite="() => toggleFavorite(item)"
            />
          </n-gi>
        </n-grid>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listingsApi } from '@/api/listings'

const router = useRouter()
const loading = ref(false)
const items = ref<any[]>([])
const summary = ref({ total: 0, collaborative: 0, random_fill: 0 })

const skeletonItems = Array.from({ length: 8 }).map((_, i) => i)

async function load() {
  loading.value = true
  try {
    const res: any = await listingsApi.getRecommendations()
    const data = res.items || []
    items.value = data.map((item: any) => ({
      ...item,
      house: item.house || {},
    }))
    summary.value = {
      total: res.summary?.total || data.length,
      collaborative: res.summary?.collaborative || 0,
      random_fill: res.summary?.random_fill || 0,
    }
  } finally {
    loading.value = false
  }
}

async function toggleFavorite(item: any) {
  if (!item?.house?.id) return
  if (item.house.is_favorited) {
    await listingsApi.unfavorite(item.house.id)
    item.house.is_favorited = false
  } else {
    await listingsApi.favorite(item.house.id)
    item.house.is_favorited = true
  }
}

onMounted(() => load())
</script>

<style scoped>
.recommend-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.recommend-header {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 16px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 6px;
}

.header-desc {
  font-size: 13px;
  color: var(--n-text-color-3);
}

.summary-info {
  display: flex;
  gap: 16px;
}

.recommend-grid {
  flex: 1;
  overflow: auto;
  padding: 12px 0;
}

.recommend-grid :deep(.n-grid) {
  box-sizing: border-box;
  width: 100%;
}

.recommend-page {
  padding-bottom: 12px;
}

/* ensure each grid item/card fills its column */
.recommend-grid :deep(.n-gi) {
  width: 100%;
}

.recommend-grid :deep(.house-card) {
  width: 100%;
}

@media screen and (max-width: 960px) {
  .recommend-header {
    grid-template-columns: 1fr;
    justify-items: flex-start;
  }

  .summary-info {
    width: 100%;
    padding: 8px 0;
  }
}
</style>
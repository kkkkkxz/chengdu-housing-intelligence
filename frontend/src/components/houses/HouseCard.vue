<template>
  <n-card hoverable class="house-card">
    <div class="house-card-body">
      <div class="meta-tags" v-if="metaTags.length">
        <n-tag v-for="item in metaTags" :key="item.label" size="small" :type="item.type" :bordered="false">
          {{ item.label }}
        </n-tag>
      </div>
      <div class="house-content">
      <div class="house-image">
        <img 
          v-if="house.cover && !imageError" 
          :src="house.cover" 
          class="image"
          @error="handleImageError"
          @load="handleImageLoad"
        />
        <div v-else class="image-placeholder">
          <span class="text-gray-400 text-12px">暂无图片</span>
        </div>
      </div>
      <div class="house-info">
        <div class="house-title">{{ house.title }}</div>
        <div class="house-location">{{ house.city }} · {{ house.community }}</div>
        <div class="house-details">{{ house.rooms }}室{{ house.halls }}厅 · {{ house.area }}㎡ · {{ house.orientation || '朝向不明' }}</div>
      </div>
      <div class="house-price">
        <div class="price-main">{{ house.total_price }}万</div>
        <div class="price-unit">单价 {{ house.unit_price || '-' }}</div>
      </div>
      </div>
    </div>
    <template #footer>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-12px text-gray-500">
          <span>关注 {{ house.followers }}</span>
          <span v-if="house.tags">| {{ house.tags }}</span>
        </div>
        <div class="flex items-center gap-2">
          <n-button size="small" tertiary @click="$emit('detail', house)">详情</n-button>
          <n-button size="small" :type="house.is_favorited ? 'success' : 'primary'" :secondary="!house.is_favorited" @click="$emit('favorite', house)">
            <span class="i-local:heart mr-4px" v-if="house.is_favorited" />{{ house.is_favorited ? '已收藏' : '收藏' }}
          </n-button>
        </div>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface HouseItem {
  id: number
  title: string
  city: string
  community?: string
  rooms?: number
  halls?: number
  area?: number
  orientation?: string
  total_price?: number
  unit_price?: number
  followers?: number
  tags?: string
  cover?: string
  is_favorited?: boolean
}

interface MetaInfo {
  source?: string
  score?: number | null
}

const props = defineProps<{
  house: HouseItem
  meta?: MetaInfo
}>()

const sourceMap: Record<string, { label: string; type: 'primary' | 'info' | 'success' | 'warning' | 'error' | 'default' }> = {
  collaborative: { label: '协同推荐', type: 'primary' },
  random_fill: { label: '随机补充', type: 'warning' },
}

const metaTags = computed(() => {
  const tags: Array<{ label: string; type: 'primary' | 'info' | 'success' | 'warning' | 'error' | 'default' }> = []
  if (props.meta?.source) {
    const meta = sourceMap[props.meta.source] || { label: props.meta.source, type: 'info' }
    tags.push(meta)
  }
  if (props.meta?.score !== undefined && props.meta?.score !== null) {
    const scoreValue = Math.max(0, Number(props.meta.score) || 0)
    tags.push({ label: `相似度 ${scoreValue.toFixed(2)}`, type: 'success' })
  }
  return tags
})

// 图片加载错误处理
const imageError = ref(false)
const handleImageError = (e: Event) => {
  imageError.value = true
  // 记录错误信息用于调试
  const img = e.target as HTMLImageElement
  console.warn('图片加载失败:', {
    url: img.src,
    houseId: props.house.id,
    houseTitle: props.house.title
  })
  // 阻止错误事件冒泡，避免在控制台显示错误
  e.stopPropagation()
}

const handleImageLoad = () => {
  imageError.value = false
}

// 当图片 URL 改变时，重置错误状态
watch(() => props.house.cover, (newUrl) => {
  imageError.value = false
  if (newUrl) {
    console.log('图片 URL 更新:', newUrl)
  }
}, { immediate: true })

defineEmits<{
  (e: 'detail', house: HouseItem): void
  (e: 'favorite', house: HouseItem): void
}>()
</script>

<style scoped>
.meta-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.house-card :deep(.n-card__content) {
  padding: 12px !important;
}

.house-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.house-card :deep(.n-card__footer) {
  padding-top: 10px;
  padding-bottom: 10px;
}

.house-content {
  display: flex !important;
  flex-direction: row !important;
  gap: 12px !important;
  align-items: flex-start !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  position: relative;
  box-sizing: border-box;
}

.house-image {
  flex-shrink: 0 !important;
  width: 160px !important;
  height: 120px !important;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f3f4f6;
  margin: 0;
  padding: 0;
  align-self: flex-start;
}

.house-image .image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.house-image .image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.house-info {
  flex: 1 1 auto !important;
  min-width: 0 !important;
  max-width: 100%;
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  padding: 0 !important;
  margin: 0 !important;
  align-self: flex-start !important;
  position: relative !important;
  box-sizing: border-box !important;
  gap: 0 !important;
  height: auto !important;
}

/* 限制信息区域宽度，留出价格区域空间，避免文字溢出到价格区域 */
.house-info {
  max-width: calc(100% - 140px) !important;
}

.house-info > * {
  display: block !important;
  position: relative !important;
  box-sizing: border-box !important;
}

.house-title {
  font-size: 16px !important;
  font-weight: 600 !important;
  color: var(--n-text-color) !important;
  margin: 0 0 8px 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  display: -webkit-box !important;
  -webkit-line-clamp: 2 !important;
  -webkit-box-orient: vertical !important;
  line-height: 20px !important;
  max-height: 40px !important;
  text-overflow: ellipsis !important;
}

.house-title {
  word-break: break-word !important;
}

.house-location {
  font-size: 13px !important;
  color: #6b7280 !important;
  margin: 0 0 6px 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  line-height: 18px !important;
}

.house-details {
  font-size: 13px !important;
  color: #6b7280 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  line-height: 18px !important;
}

.house-price {
  flex-shrink: 0 !important;
  width: 120px !important;
  text-align: right;
  display: flex !important;
  flex-direction: column !important;
  align-items: flex-end !important;
  justify-content: flex-start !important;
  padding: 0 !important;
  margin: 0 !important;
  align-self: flex-start !important;
  gap: 4px !important;
}

.price-main {
  font-size: 18px;
  font-weight: 700;
  color: #dc2626;
  line-height: 1.2;
  margin: 0;
  padding: 0;
}

.price-unit {
  font-size: 12px;
  color: #6b7280;
  margin: 4px 0 0 0;
  padding: 0;
  line-height: 1.2;
}
</style>
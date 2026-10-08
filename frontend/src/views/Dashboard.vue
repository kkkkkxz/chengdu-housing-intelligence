<template>
  <div class="dashboard-container">
    <NSpace vertical :size="16">
      <!-- 欢迎横幅 -->
      <NCard :bordered="false" class="header-banner">
        <div class="banner-content">
          <div class="welcome-text">
            <NH1 class="welcome-title">欢迎回来，{{ authStore.user?.username }}</NH1>
            <NP class="welcome-desc">这是专业的二手房数据分析平台，为您提供全面的市场分析和房源洞察</NP>
          </div>
          <div class="banner-stats">
            <div class="stat-item">
              <div class="stat-value">{{ statistics.totalHouses }}</div>
              <div class="stat-label">总房源</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ statistics.avgUnitPrice }}</div>
              <div class="stat-label">均价(元/㎡)</div>
            </div>
          </div>
        </div>
      </NCard>

      <!-- 统计卡片 -->
      <NCard :bordered="false" class="card-wrapper">
        <NGrid cols="s:1 m:2 l:4" responsive="screen" :x-gap="16" :y-gap="16">
          <NGi v-for="item in cardData" :key="item.key">
            <div class="stat-card" :style="{ backgroundImage: `linear-gradient(135deg, ${item.color.start}, ${item.color.end})` }">
              <div class="stat-content">
                <h3 class="stat-title">{{ item.title }}</h3>
                <div class="stat-main">
                  <SvgIcon :icon="item.icon" class="stat-icon" />
                  <div class="stat-number">{{ formatNumber(item.value) }}</div>
                </div>
                <div class="stat-unit">{{ item.unit }}</div>
              </div>
            </div>
          </NGi>
        </NGrid>
      </NCard>

      <!-- 图表区域 -->
      <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24 s:24 m:14">
          <NCard :bordered="false" class="card-wrapper">
            <div class="card-header">
              <h3>价格区间分布</h3>
              <n-tag type="info" size="small">总房源分析</n-tag>
            </div>
            <div ref="priceRangeRef" class="chart-container"></div>
          </NCard>
        </NGi>
        <NGi span="24 s:24 m:10">
          <NCard :bordered="false" class="card-wrapper">
            <div class="card-header">
              <h3>建筑类型分析</h3>
              <n-tag type="error" size="small">均价对比</n-tag>
            </div>
            <div ref="buildingTypeRef" class="chart-container"></div>
          </NCard>
        </NGi>
      </NGrid>

      <!-- 底部信息 -->
      <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24 s:24 m:12">
          <NCard :bordered="false" class="card-wrapper">
            <div class="card-header">
              <h3>最新房源</h3>
              <n-button text type="primary" @click="$router.push('/listings')">查看更多</n-button>
            </div>
            <div class="latest-listings">
              <div v-for="house in latestListings" :key="house.id" class="listing-item" @click="$router.push(`/listings/${house.id}`)">
                <div class="listing-image">
                  <img :src="house.cover || '/placeholder-house.jpg'" :alt="house.title" />
                </div>
                <div class="listing-info">
                  <div class="listing-title">{{ house.title }}</div>
                  <div class="listing-details">
                    <span>{{ house.rooms }}室{{ house.halls }}厅</span>
                    <span>{{ house.area }}㎡</span>
                    <span>{{ house.district || '未注明' }}</span>
                    <span>{{ house.community || '未注明' }}</span>
                  </div>
                  <div class="listing-price">
                    <span class="price">{{ house.total_price }}万</span>
                    <span class="unit-price" v-if="house.unit_price">{{ Math.round(house.unit_price) }}元/㎡</span>
                  </div>
                </div>
              </div>
            </div>
          </NCard>
        </NGi>
        <NGi span="24 s:24 m:12">
          <NCard :bordered="false" class="card-wrapper">
            <div class="card-header">
              <h3>房源统计</h3>
              <n-tag type="default" size="small">实时数据</n-tag>
            </div>
            <div class="statistics-detail">
              <div class="stat-row">
                <span class="stat-label">覆盖城市</span>
                <span class="stat-value">{{ statistics.cities }}个</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">覆盖区域</span>
                <span class="stat-value">{{ statistics.districts }}个</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">热门户型</span>
                <span class="stat-value">{{ statistics.popularHouseType }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">平均面积</span>
                <span class="stat-value">{{ statistics.avgArea }}㎡</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">最高关注</span>
                <span class="stat-value">{{ statistics.maxFollowers }}人</span>
              </div>
            </div>
          </NCard>
        </NGi>
      </NGrid>
    </NSpace>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { listingsApi } from '../api/listings'
import { NCard, NGrid, NGi, NSpace, NH1, NP, NTag, NButton } from 'naive-ui'
import * as echarts from 'echarts'
import SvgIcon from '@/components/custom/svg-icon.vue'

const authStore = useAuthStore()

// 图表引用
const priceRangeRef = ref<HTMLDivElement>()
const buildingTypeRef = ref<HTMLDivElement>()

// 图表实例
let priceRangeChart: echarts.ECharts | null = null
let buildingTypeChart: echarts.ECharts | null = null

// 统计数据
const statistics = reactive({
  totalHouses: 0,
  avgUnitPrice: 0,
  cities: 0,
  districts: 0,
  popularHouseType: '-',
  avgArea: 0,
  maxFollowers: 0
})

// 卡片数据
const unifiedStart = '#eae2ff'
const unifiedEnd = '#cfbcff'

const cardData = ref([
  {
    key: 'totalListings',
    title: '在售房源',
    value: 0,
    unit: '套',
    color: { start: unifiedStart, end: unifiedEnd },
    icon: 'mdi-home-outline'
  },
  {
    key: 'avgPrice',
    title: '平均单价',
    value: 0,
    unit: '元/㎡',
    color: { start: unifiedStart, end: unifiedEnd },
    icon: 'mdi-currency-cny'
  },
  {
    key: 'totalArea',
    title: '总面积',
    value: 0,
    unit: '万㎡',
    color: { start: unifiedStart, end: unifiedEnd },
    icon: 'mdi-home-group'
  },
  {
    key: 'avgTotalPrice',
    title: '平均总价',
    value: 0,
    unit: '万',
    color: { start: unifiedStart, end: unifiedEnd },
    icon: 'mdi-currency-cny'
  }
])

const latestListings = ref<any[]>([])

// 加载最新房源
async function loadLatestListings() {
  try {
    const response = await listingsApi.getHouses({ 
      page: 1, 
      page_size: 6, 
      ordering: '-created_at',
      search: '',
      rooms: undefined,
      price_min: undefined,
      halls: undefined
    })
    const res: any = response
    latestListings.value = res?.results || []
    // 填充统计信息的基础字段（使用返回的 count）
    try {
      statistics.totalHouses = res.count || latestListings.value.length || 0
      // 计算平均单价（使用最新房源的 unit_price 平均作为近似）
      const unitPrices = latestListings.value.map((h: any) => Number(h.unit_price) || 0).filter((v: number) => v > 0)
      statistics.avgUnitPrice = unitPrices.length ? Math.round(unitPrices.reduce((a: number, b: number) => a + b, 0) / unitPrices.length) : 0
      // 覆盖城市数与区域数的近似（基于最新房源）
      statistics.cities = new Set(latestListings.value.map((h: any) => h.city || '')).size
      statistics.districts = new Set(latestListings.value.map((h: any) => h.district || '')).size
      // 平均面积与最高关注
      const areas = latestListings.value.map((h: any) => Number(h.area) || 0).filter((v: number) => v > 0)
      statistics.avgArea = areas.length ? Math.round(areas.reduce((a: number, b: number) => a + b, 0) / areas.length) : 0
      statistics.maxFollowers = Math.max(...latestListings.value.map((h: any) => Number(h.followers) || 0), 0)

      // 更新卡片展示值
      const totalListingsCard = cardData.value.find(c => c.key === 'totalListings')
      if (totalListingsCard) totalListingsCard.value = statistics.totalHouses
      const avgPriceCard = cardData.value.find(c => c.key === 'avgPrice')
      if (avgPriceCard) avgPriceCard.value = statistics.avgUnitPrice
      const totalAreaCard = cardData.value.find(c => c.key === 'totalArea')
      if (totalAreaCard) {
        // 总面积以万㎡为单位展示
        const totalArea = areas.length ? areas.reduce((a: number, b: number) => a + b, 0) : 0
        totalAreaCard.value = totalArea ? Number((totalArea / 10000).toFixed(2)) : 0
      }
      const avgTotalPriceCard = cardData.value.find(c => c.key === 'avgTotalPrice')
      if (avgTotalPriceCard) {
        const prices = latestListings.value.map((h: any) => Number(h.total_price) || 0).filter((v: number) => v > 0)
        avgTotalPriceCard.value = prices.length ? Number((prices.reduce((a: number, b: number) => a + b, 0) / prices.length).toFixed(2)) : 0
      }
    } catch (e) {
      console.warn('计算统计信息失败', e)
    }
  } catch (error) {
    console.error('加载最新房源失败：', error)
  }
}

// 创建价格区间分布图
async function createPriceRangeChart() {
  if (!priceRangeRef.value) return

  priceRangeChart = echarts.init(priceRangeRef.value)

  try {
    const response = await listingsApi.statsPriceRange()
    const data = (response as unknown as any[]) || []

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.map(item => item.name),
        axisLabel: {
          color: '#666',
          fontSize: 11,
          rotate: 0
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          color: '#666',
          fontSize: 12
        }
      },
      series: [{
        name: '房源数量',
        type: 'bar',
        data: data.map(item => item.value),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#5379c1' },
              { offset: 1, color: '#4f6bd3' }
            ]
          },
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#6c8ee5' },
                { offset: 1, color: '#577ad0' }
              ]
            }
          }
        }
    }]
    }

    priceRangeChart.setOption(option)
  } catch (error) {
    console.error('创建价格区间图失败：', error)
  }
}

// 创建建筑类型分析图
async function createBuildingTypeChart() {
  if (!buildingTypeRef.value) return

  buildingTypeChart = echarts.init(buildingTypeRef.value)

  try {
    const response = await listingsApi.statsAvgPriceByBuildingType()
    const data = (response as unknown as any[]) || []

    // 取前6个建筑类型
    const topData = data.slice(0, 6)

    const chartColors = ['#4f6bd3', '#5379c1', '#4f7eda', '#5f8ee8', '#6c9ef0', '#79aeff']

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} 元/㎡'
      },
      series: [{
        type: 'pie',
        radius: ['30%', '70%'],
        center: ['50%', '50%'],
        roseType: 'radius',
        itemStyle: {
          borderRadius: 6
        },
        data: topData.map((item, index) => ({
          name: item.name,
          value: item.value,
          itemStyle: {
            color: chartColors[index % chartColors.length]
          }
        }))
      }]
    }

    buildingTypeChart.setOption(option)
  } catch (error) {
    console.error('创建建筑类型图失败：', error)
  }
}

// 格式化数字
function formatNumber(num: number) {
  if (!Number.isFinite(num)) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toLocaleString()
}

// 响应式处理
function handleResize() {
  priceRangeChart?.resize()
  buildingTypeChart?.resize()
}

// 加载全量汇总数据（用于仪表盘卡片与统计）
async function loadSummary() {
  try {
    const res: any = await listingsApi.getSummary()
    statistics.totalHouses = res.total_houses || 0
    statistics.avgUnitPrice = res.avg_unit_price || 0
    statistics.cities = res.cities || 0
    statistics.districts = res.districts || 0
    statistics.popularHouseType = res.popular_house_type || '-'
    statistics.avgArea = res.avg_area || 0
    statistics.maxFollowers = res.max_followers || 0

    const totalListingsCard = cardData.value.find(c => c.key === 'totalListings')
    if (totalListingsCard) totalListingsCard.value = statistics.totalHouses
    const avgPriceCard = cardData.value.find(c => c.key === 'avgPrice')
    if (avgPriceCard) avgPriceCard.value = statistics.avgUnitPrice
    const totalAreaCard = cardData.value.find(c => c.key === 'totalArea')
    if (totalAreaCard) totalAreaCard.value = res.total_area_wan_m2 || 0
    const avgTotalPriceCard = cardData.value.find(c => c.key === 'avgTotalPrice')
    if (avgTotalPriceCard) avgTotalPriceCard.value = res.avg_total_price || 0
  } catch (error) {
    console.error('加载汇总数据失败：', error)
  }
}

// 初始化
onMounted(async () => {
  await nextTick()
  // 加载数据
  // 先加载汇总统计（全量），再加载最新房源与图表
  await Promise.all([
    loadSummary(),
    loadLatestListings(),
  ])
  // 创建图表
  await Promise.all([
    createPriceRangeChart(),
    createBuildingTypeChart()
  ])
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  // 全局错误与未处理拒绝监听（用于调试 HMR/运行时问题）
  ;(window as any).__dashboard_global_error_handler = (e: ErrorEvent) => {
    // 将错误详细信息打印到控制台，方便复制粘贴
    // eslint-disable-next-line no-console
    console.error('[Dashboard] Global error:', e.error || e.message, e)
  }
  window.addEventListener('error', (window as any).__dashboard_global_error_handler)
  ;(window as any).__dashboard_unhandled_rejection_handler = (e: PromiseRejectionEvent) => {
    // eslint-disable-next-line no-console
    console.error('[Dashboard] Unhandled rejection:', e.reason || e)
  }
  window.addEventListener('unhandledrejection', (window as any).__dashboard_unhandled_rejection_handler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  priceRangeChart?.dispose()
  buildingTypeChart?.dispose()
  // 移除调试监听器
  if ((window as any).__dashboard_global_error_handler) {
    window.removeEventListener('error', (window as any).__dashboard_global_error_handler)
    delete (window as any).__dashboard_global_error_handler
  }
  if ((window as any).__dashboard_unhandled_rejection_handler) {
    window.removeEventListener('unhandledrejection', (window as any).__dashboard_unhandled_rejection_handler)
    delete (window as any).__dashboard_unhandled_rejection_handler
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 16px;
  min-height: 100vh;
  background: var(--page-bg-color);
}

.header-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
}

.welcome-title {
  color: white !important;
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.welcome-desc {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  margin: 0;
}

.banner-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-item .stat-value {
  font-size: 32px;
  font-weight: bold;
  color: white;
}

.stat-item .stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.card-wrapper {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.3s ease;
}

.card-wrapper:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-card {
  border-radius: 12px;
  padding: 20px;
  color: white;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  pointer-events: none;
}

.stat-content {
  position: relative;
  z-index: 1;
}

.stat-title {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 12px 0;
  opacity: 0.9;
}

.stat-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stat-icon {
  font-size: 32px;
  opacity: 0.8;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
}

.stat-unit {
  font-size: 12px;
  opacity: 0.8;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary-color);
}

.latest-listings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.listing-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: background-color 0.2s;
}

.listing-item:hover {
  background-color: var(--card-hover-bg);
}

.listing-image {
  width: 80px;
  height: 60px;
  border-radius: 0px;
  overflow: hidden;
  flex-shrink: 0;
}

.listing-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.listing-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.listing-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.listing-details {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary-color);
  flex-wrap: wrap;
}

.listing-price {
  display: flex;
  align-items: center;
  gap: 8px;
}

.price {
  font-size: 16px;
  font-weight: bold;
  color: var(--accent-danger-color);
}

.unit-price {
  font-size: 12px;
  color: var(--text-secondary-color);
}

.statistics-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--surface-border);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row .stat-label {
  font-size: 14px;
  color: var(--text-secondary-color);
}

.stat-row .stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .banner-stats {
    justify-content: center;
  }

  .welcome-title {
    font-size: 24px;
  }

  .dashboard-container {
    padding: 8px;
  }

  .listing-details {
    font-size: 11px;
  }

  .chart-container {
    height: 250px;
  }
}
</style>
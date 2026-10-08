<template>
  <div class="p-16">
    <!-- 页面标题 -->
    <div class="mb-16">
      <h1 class="text-2xl font-bold text-gray-800">户型与类型分析</h1>
      <p class="text-gray-600 mt-2">深度解析二手房户型分布与建筑类型特征</p>
    </div>

    <!-- 数据统计卡片 -->
    <div class="mb-16">
      <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24 s:24 m:8">
          <NCard :bordered="false" size="small" class="card-wrapper">
            <div class="rd-8px px-16px pb-4px pt-8px text-white" style="backgroundImage: linear-gradient(to bottom right, #f0ebff, #d8c8ff)">
              <h3 class="text-16px">总房源数量</h3>
              <div class="flex justify-between pt-12px">
                <span class="text-32px">🏠</span>
                <span class="text-30px text-white">{{ totalListings }}</span>
              </div>
            </div>
          </NCard>
        </NGi>
        <NGi span="24 s:24 m:8">
          <NCard :bordered="false" size="small" class="card-wrapper">
            <div class="rd-8px px-16px pb-4px pt-8px text-white" style="backgroundImage: linear-gradient(to bottom right, #f0ebff, #d8c8ff)">
              <h3 class="text-16px">平均单价</h3>
              <div class="flex justify-between pt-12px">
                <span class="text-32px">💰</span>
                <span class="text-30px text-white">{{ avgPrice }}</span>
              </div>
            </div>
          </NCard>
        </NGi>
        <NGi span="24 s:24 m:8">
          <NCard :bordered="false" size="small" class="card-wrapper">
            <div class="rd-8px px-16px pb-4px pt-8px text-white" style="backgroundImage: linear-gradient(to bottom right, #f0ebff, #d8c8ff)">
              <h3 class="text-16px">热门户型</h3>
              <div class="flex justify-between pt-12px">
                <span class="text-32px">🏘️</span>
                <span class="text-30px text-white">{{ popularTypes }}</span>
              </div>
            </div>
          </NCard>
        </NGi>
      </NGrid>
    </div>

    <!-- 图表区域 -->
    <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
      <!-- 户型占比饼图 -->
      <NGi span="24 s:24 m:12">
        <NCard :bordered="false" class="card-wrapper">
          <div class="px-16px py-12px border-b border-gray-200">
            <h3 class="text-16px font-semibold text-gray-800">户型占比分析</h3>
            <p class="text-12px text-gray-600 mt-1">各户型房源分布情况</p>
          </div>
          <div ref="refHouseType" class="h-360px"></div>
        </NCard>
      </NGi>

      <!-- 建筑类型雷达图 -->
      <NGi span="24 s:24 m:12">
        <NCard :bordered="false" class="card-wrapper">
          <div class="px-16px py-12px border-b border-gray-200">
            <h3 class="text-16px font-semibold text-gray-800">建筑类型均价</h3>
            <p class="text-12px text-gray-600 mt-1">不同建筑类型价格对比</p>
          </div>
          <div ref="refBuildingRadar" class="h-360px"></div>
        </NCard>
      </NGi>

      <!-- 房源标题词云 -->
      <NGi span="24 s:24 m:14">
        <NCard :bordered="false" class="card-wrapper">
          <div class="px-16px py-12px border-b border-gray-200">
            <h3 class="text-16px font-semibold text-gray-800">房源标题词云</h3>
            <p class="text-12px text-gray-600 mt-1">热门关键词可视化展示</p>
          </div>
          <div ref="refWordcloud" class="h-400px"></div>
        </NCard>
      </NGi>

      <!-- 户型趋势仪表盘 -->
      <NGi span="24 s:24 m:10">
        <NCard :bordered="false" class="card-wrapper">
          <div class="px-16px py-12px border-b border-gray-200">
            <h3 class="text-16px font-semibold text-gray-800">户型热度指数</h3>
            <p class="text-12px text-gray-600 mt-1">最受欢迎户型指标</p>
          </div>
          <div ref="refGauge" class="h-400px"></div>
        </NCard>
      </NGi>
    </NGrid>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import { onMounted, onBeforeUnmount, ref, nextTick } from 'vue'
import { listingsApi } from '../api/listings'

const refHouseType = ref<HTMLDivElement | null>(null)
const refBuildingRadar = ref<HTMLDivElement | null>(null)
const refWordcloud = ref<HTMLDivElement | null>(null)
const refGauge = ref<HTMLDivElement | null>(null)

let chartType: echarts.ECharts | null = null
let chartRadar: echarts.ECharts | null = null
let chartCloud: echarts.ECharts | null = null
let chartGauge: echarts.ECharts | null = null

// 统计数据
const totalListings = ref('-')
const avgPrice = ref('-')
const popularTypes = ref('-')

// soybean-admin风格的颜色方案
function getColorPalette() {
  return ['#5da8ff', '#8e9dff', '#fedc69', '#26deca', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24']
}

function resizeAll() {
  chartType?.resize()
  chartRadar?.resize()
  chartCloud?.resize()
  chartGauge?.resize()
}

async function renderTypePie() {
  if (!refHouseType.value) return
  chartType = echarts.init(refHouseType.value)
  const list = (await listingsApi.statsHouseTypeCount()) as unknown as any[]

  // 更新统计数据
  updateTypeStatistics(list)

  chartType.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}套 ({d}%)'
    },
    series: [{
      color: getColorPalette(),
      name: '户型占比',
      type: 'pie',
      radius: ['45%', '75%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        },
        labelLine: {
          show: false
        },
      },
      data: list as any
    }]
  })
}

// 更新户型统计数据的函数
function updateTypeStatistics(list: any[]) {
  if (list && list.length > 0) {
    // 总房源数量
    const totalCount = list.reduce((sum, item) => sum + item.value, 0)
    totalListings.value = totalCount.toLocaleString()

    // 找出最受欢迎的户型
    const mostPopular = list.reduce((max, item) => item.value > max.value ? item : max, list[0])
    popularTypes.value = mostPopular.name

    // 计算平均价格
    listingsApi.statsAvgPriceByDistrict().then((priceData: any) => {
      if (priceData && priceData.length > 0) {
        const prices = priceData.map((item: any) => item.value)
        const avgPriceValue = Math.round(prices.reduce((sum: number, price: number) => sum + price, 0) / prices.length)
        avgPrice.value = avgPriceValue.toLocaleString()
      }
    }).catch(() => {
      // 如果API调用失败，保持默认值
    })
  }
}

async function renderBuildingRadar() {
  if (!refBuildingRadar.value) return
  chartRadar = echarts.init(refBuildingRadar.value)
  const list = (await listingsApi.statsAvgPriceByBuildingType()) as unknown as any[]

  // 构造雷达图数据
  const indicators = list.map((item: any) => ({
    name: item.name,
    max: Math.max(...list.map((i: any) => i.value as number)) * 1.2
  }))

  const data = list.map((item: any) => item.value)

  chartRadar.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 元/㎡'
    },
    legend: {
      data: ['建筑类型均价'],
      bottom: '2%',
      itemStyle: {
        borderWidth: 0
      }
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      radius: '65%',
      splitNumber: 4,
      axisName: {
        color: 'rgb(31, 31, 31)',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: ['#e5e7eb']
        }
      },
      splitArea: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: '#e5e7eb'
        }
      }
    },
    series: [{
      name: '建筑类型分析',
      type: 'radar',
      data: [
        {
          value: data,
          name: '建筑类型均价',
          itemStyle: {
            color: '#8e9dff'
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0.25,
                  color: '#8e9dff'
                },
                {
                  offset: 1,
                  color: '#fff'
                }
              ]
            }
          }
        }
      ]
    }]
  })
}

async function renderWordcloud() {
  if (!refWordcloud.value) return
  chartCloud = echarts.init(refWordcloud.value)
  try {
    const list = (await listingsApi.statsTitleWordcloud({ top: 100 })) as unknown as any[]
    chartCloud.setOption({
    tooltip: {
      formatter: '{b}: {c}次'
    },
    series: [{
      type: 'wordCloud',
      gridSize: 8,
      sizeRange: [12, 60],
      rotationRange: [0, 0],
      shape: 'circle',
      textStyle: {
        color: () => {
          const colors = getColorPalette()
          return colors[Math.floor(Math.random() * colors.length)]
        }
      },
      emphasis: {
        focus: 'self'
      },
        data: list as any
      }]
    })
  } catch (error) {
    // 后端返回 500 时会到这里，避免未处理的 promise 导致页面崩溃
    // 打印错误并使用空数据渲染占位图表
    // eslint-disable-next-line no-console
    console.error('renderWordcloud failed:', error)
    chartCloud.setOption({
      title: { text: '词云数据不可用' },
      series: [{
        type: 'wordCloud',
        data: []
      }]
    })
  }
}

async function renderGauge() {
  if (!refGauge.value) return
  chartGauge = echarts.init(refGauge.value)
  // 获取户型数据来计算仪表盘数值
  const houseTypeData = await listingsApi.statsHouseTypeCount() as unknown as any[]

  let gaugeValue = 75
  let gaugeName = '户型热度指数'

  if (houseTypeData && houseTypeData.length > 0) {
    // 找出最受欢迎的户型
    const mostPopular = houseTypeData.reduce((max, item) => item.value > max.value ? item : max, houseTypeData[0])
    const totalCount = houseTypeData.reduce((sum, item) => sum + item.value, 0)
    const percentage = Math.round((mostPopular.value / totalCount) * 100)

    gaugeValue = percentage
    gaugeName = mostPopular.name + '占比'
  }

  chartGauge.setOption({
    tooltip: {
      formatter: '{a} <br/>{b} : {c}%'
    },
    series: [{
      name: '户型热度',
      type: 'gauge',
      progress: {
        show: true,
        width: 12
      },
      axisLine: {
        lineStyle: {
          width: 12,
          color: [[0.7, '#5da8ff'], [1, '#fdbc25']]
        }
      },
      axisTick: {
        show: false
      },
      splitLine: {
        length: 15,
        lineStyle: {
          width: 2,
          color: '#999'
        }
      },
      axisLabel: {
        distance: 20,
        color: '#999',
        fontSize: 12
      },
      anchor: {
        show: true,
        showAbove: true,
        size: 25,
        itemStyle: {
          borderWidth: 10,
          borderColor: '#5da8ff'
        }
      },
      title: {
        show: true,
        offsetCenter: [0, '50%'],
        fontSize: 14,
        color: '#666'
      },
      detail: {
        valueAnimation: true,
        fontSize: 20,
        offsetCenter: [0, '70%'],
        formatter: '{value}%',
        color: '#333'
      },
      data: [{
        value: gaugeValue,
        name: gaugeName
      }]
    }]
  })
}

onMounted(async () => {
  await nextTick()
  // 使用 allSettled 避免单个统计接口失败导致其它图表无法渲染
  await Promise.allSettled([renderTypePie(), renderBuildingRadar(), renderWordcloud(), renderGauge()])
  window.addEventListener('resize', resizeAll)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeAll)
  chartType?.dispose()
  chartRadar?.dispose()
  chartCloud?.dispose()
  chartGauge?.dispose()
})
</script>

<style scoped>
/* 简洁的样式，参照soybean-admin */
.card-wrapper {
  transition: all 0.3s ease;
}

.card-wrapper:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.h-360px {
  height: 360px;
}

.h-400px {
  height: 400px;
}

.rd-8px {
  border-radius: 8px;
}
</style>
<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center gap-3">
      <n-input
        class="w-280px"
        :value="localQuery.search"
        clearable
        placeholder="搜索(标题/小区/城市)"
        @update:value="(v) => updateField('search', v)"
        @keyup.enter="emitSearch"
      />
      <n-select
        class="w-120px"
        :value="localQuery.rooms"
        :options="roomOptions"
        clearable
        placeholder="室"
        @update:value="onUpdateRooms"
      />
      <n-select
        class="w-120px"
        :value="localQuery.halls"
        :options="hallOptions"
        clearable
        placeholder="厅"
        @update:value="onUpdateHalls"
      />
      <n-select
        class="w-180px"
        :value="localQuery.ordering"
        :options="orderingOptions"
        clearable
        placeholder="排序"
        @update:value="onUpdateOrdering"
      />
      <div class="ml-auto flex items-center gap-2">
        <n-button type="primary" @click="emitSearch">查询</n-button>
        <n-button tertiary @click="reset">重置</n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface HouseQuery {
  page?: number
  page_size?: number
  search?: string
  city?: string | undefined
  rooms?: number | undefined
  halls?: number | undefined
  ordering?: string | undefined
}

const props = defineProps<{
  modelValue: HouseQuery
  cityOptions?: { label: string; value: string }[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: HouseQuery): void
  (e: 'search'): void
}>()

const localQuery = computed({
  get: () => props.modelValue,
  set: (v: HouseQuery) => emit('update:modelValue', v)
})

const cityOptions = computed(() => props.cityOptions || [])

const roomOptions = Array.from({ length: 6 }, (_, i) => ({ label: `${i}室`, value: i }))
const hallOptions = Array.from({ length: 5 }, (_, i) => ({ label: `${i}厅`, value: i }))
const orderingOptions = [
  { label: '最新', value: '-created_at' },
  { label: '总价升序', value: 'total_price' },
  { label: '总价降序', value: '-total_price' },
  { label: '面积升序', value: 'area' },
  { label: '面积降序', value: '-area' }
]

function updateField<K extends keyof HouseQuery>(key: K, value: HouseQuery[K]) {
  const next = { ...localQuery.value, [key]: value }
  if (key !== 'page') next.page = 1
  localQuery.value = next
}

function emitSearch() {
  emit('search')
}

function reset() {
  localQuery.value = {
    page: 1,
    page_size: localQuery.value.page_size || 10,
    search: '',
    city: undefined,
    rooms: undefined,
    halls: undefined,
    ordering: '-created_at'
  }
  emit('search')
}

function onUpdateCity(v: unknown) {
  updateField('city', (v as string | undefined))
}
function onUpdateRooms(v: unknown) {
  updateField('rooms', (v as number | undefined))
}
function onUpdateHalls(v: unknown) {
  updateField('halls', (v as number | undefined))
}
function onUpdateOrdering(v: unknown) {
  updateField('ordering', (v as string | undefined))
}
</script>

<style scoped>
</style>
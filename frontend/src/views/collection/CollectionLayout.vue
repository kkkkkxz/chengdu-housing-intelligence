<template>
  <div class="collection-layout">
    <n-card class="collection-tabs" :bordered="false">
      <n-tabs type="line" :value="activeTab" @update:value="onUpdateTab">
        <n-tab-pane name="/collection/recommendations" tab="智能推荐" />
        <n-tab-pane name="/collection/favorites" tab="我的收藏" />
      </n-tabs>
    </n-card>
    <div class="collection-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

const defaultTab = '/collection/recommendations'
const allowTabs = ['/collection/recommendations', '/collection/favorites']

const activeTab = computed(() => {
  const path = route.meta?.activeMenu || route.path
  return allowTabs.includes(path as string) ? (path as string) : defaultTab
})

function onUpdateTab(value: string) {
  if (!allowTabs.includes(value)) return
  if (value !== route.path) {
    router.push(value)
  }
}
</script>

<style scoped>
.collection-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 10px;
}

.collection-tabs {
  flex-shrink: 0;
}

.collection-content {
  flex: 1;
  overflow: auto;
}
</style>
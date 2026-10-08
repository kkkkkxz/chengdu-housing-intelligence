<template>
  <div class="layout-wrapper">
    <n-layout has-sider>
      <n-layout-sider
        width="220"
        collapse-mode="width"
        :collapsed-width="64"
        bordered
        :collapsed="layoutStore.collapsed"
      >
        <div class="sider-logo">
          <SystemLogo class="logo" />
        </div>
        <n-menu
          :value="activeMenu"
          :options="menuOptions"
          :collapsed="layoutStore.collapsed"
          @update:value="onSelect"
        />
      </n-layout-sider>
      <n-layout>
        <n-layout-header class="layout-header" bordered>
          <div class="header-left">
            <n-button quaternary circle size="small" @click="layoutStore.toggleCollapsed">
              <n-icon size="18">
                <component :is="layoutStore.collapsed ? MenuOutline : ReorderTwoOutline" />
              </n-icon>
            </n-button>
            <div class="header-title">
              <span class="system-name">二手房数据分析平台</span>
              <n-breadcrumb separator="/">
                <n-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
                  <span>{{ item.title }}</span>
                </n-breadcrumb-item>
              </n-breadcrumb>
            </div>
          </div>
          <div class="header-right">
            <n-dropdown :options="userMenu" trigger="hover" @select="onUserSelect">
              <div class="user-trigger">
                <img
                  v-if="avatarUrl && !headerImgBroken"
                  :src="avatarUrl"
                  class="user-avatar"
                  @error="onHeaderImgError"
                />
                <n-avatar v-else :size="30" round>{{ userInitial }}</n-avatar>
                <span class="user-name">{{ userDisplayName }}</span>
              </div>
            </n-dropdown>
          </div>
        </n-layout-header>
        <LayoutTabs />
        <n-layout-content class="layout-content">
          <n-spin :show="layoutStore.reloadFlag" class="content-spin">
            <router-view :key="layoutStore.reloadKey" />
          </n-spin>
        </n-layout-content>
      </n-layout>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLayoutStore } from '@/stores/layout'
import SystemLogo from '@/components/common/system-logo.vue'
import LayoutTabs from '@/components/layout/LayoutTabs.vue'
import { NIcon } from 'naive-ui'
import {
  BarChart,
  Heart,
  HomeOutline,
  List,
  Map as MapIcon,
  People,
  PieChart,
  Settings,
  Sparkles,
  MenuOutline,
  ReorderTwoOutline,
  Book
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const layoutStore = useLayoutStore()
const headerImgBroken = ref(false)

const userDisplayName = computed(() => authStore.user?.nike_name || authStore.user?.username || '个人中心')

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = computed(() => {
  console.log('当前用户:', authStore.user, 'isAdmin:', authStore.isAdmin)
  const baseMenu = [
    { label: '主页', key: '/dashboard', icon: renderIcon(HomeOutline) },
    { label: '房源列表', key: '/houses', icon: renderIcon(List) },
    {
      label: '可视化分析',
      key: 'analytics',
      icon: renderIcon(BarChart),
      children: [
        { label: '价格分析', key: '/analytics/price', icon: renderIcon(PieChart) },
        {label: ' 户型与类别 ', key: '/analytics/type', icon: renderIcon (List) },
        {label: ' 区域分析 ', key: '/analytics/region', icon: renderIcon (MapIcon) },
      ]
    },
    {
      label: '推荐与收藏',
      key: 'collection',
      icon: renderIcon(Heart),
      children: [
        { label: '智能推荐', key: '/collection/recommendations', icon: renderIcon(Sparkles) },
        { label: '我的收藏', key: '/collection/favorites', icon: renderIcon(Heart) },
      ]
    },
    { label:'智能问答',key:'/assistant',icon:renderIcon(Sparkles)},
    { label: '房价预测', key: '/price-prediction',icon: renderIcon(PieChart) },
    { label: 'RAG问答', key: '/rag', icon: renderIcon(Book) },
  ]

    // 管理员额外添加“系统管理”菜单
    if (authStore.isAdmin) {
      baseMenu.push({
        label: '系统管理',
        key: 'admin-group',
        icon: renderIcon(Settings),
        children: [
          { label: '房源管理', key: '/admin/houses', icon: renderIcon(List) },
        ]
      })
    }
  return baseMenu
})

const activeMenu = computed(() => (route.meta?.activeMenu as string) || route.path)

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title)
  if (matched.length === 0) {
    return [{ title: '主页', path: '/houses' }]
  }
  return matched.map(item => ({
    title: item.meta?.title as string,
    path: item.path
  }))
})

const userMenu = [
  { label: '个人资料', key: 'profile' },
  { type: 'divider' as const },
  { label: '修改密码', key: 'password' },
  { label: '退出登录', key: 'logout' }
]

function onSelect(key: string) {
  if (key.startsWith('/')) {
    router.push(key)
  }
}

function onUserSelect(key: string) {
  switch (key) {
    case 'profile':
      router.push('/profile')
      break
    case 'favorites':
      router.push('/collection/favorites')
      break
    case 'password':
      router.push('/account/password')
      break
    case 'logout':
      authStore.logout()
      layoutStore.resetTabs()
      router.push('/login')
      break
  }
}

const avatarUrl = computed(() => {
  const raw = (authStore.user?.avatar || '').trim()
  if (!raw) return undefined
  const stamp = Date.now()
  let url = raw
  if (!/^https?:\/\//i.test(url)) {
    url = url.startsWith('/media/') ? url : `/media/${url.replace(/^\//, '')}`
  }
  return `${url}${url.includes('?') ? '&' : '?'}t=${stamp}`
})

const userInitial = computed(() => authStore.user?.username?.[0]?.toUpperCase() || 'U')

function onHeaderImgError() {
  headerImgBroken.value = true
}

watch(
  () => route.fullPath,
  () => {
    layoutStore.syncRouteTab(route)
  },
  { immediate: true }
)
</script>

<style scoped>
.layout-wrapper {
  height: 100vh;
  background-color: var(--tabs-bg-color);
}

.sider-logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--n-border-color);
}

.logo {
  display: flex;
  justify-content: center;
  width: 100%;
}

.layout-header {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background-color: var(--tabs-bg-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
  color: var(--n-text-color);
}

.system-name {
  font-size: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 999px;
  transition: background-color 0.2s ease;
}

.user-trigger:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.dark .user-trigger:hover {
  background-color: rgba(255, 255, 255, 0.08);
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.user-name {
  font-size: 13px;
}

.layout-content {
  height: calc(100vh - 56px - 44px);
  background-color: var(--n-color-body);
  padding: 16px;
  overflow: hidden;
}

.content-spin {
  height: 100%;
  width: 100%;
}

.content-spin :deep(.n-spin-content) {
  height: 100%;
}
</style>
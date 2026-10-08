import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RouteLocationNormalizedLoaded } from 'vue-router'

export interface LayoutTab {
  path: string
  name?: string | symbol
  title: string
  closable: boolean
}

export const DASHBOARD_PATH = '/dashboard'

export const useLayoutStore = defineStore('layout', () => {
  const collapsed = ref(false)
  const tabs = ref<LayoutTab[]>([])
  const activePath = ref('')
  const reloadKey = ref(Date.now())
  // 是否显示全局内容区域的 loading 动画
  // 默认不显示，避免首次进入主界面时一直看到加载动画
  const reloadFlag = ref(false)

  const toggleCollapsed = () => {
    collapsed.value = !collapsed.value
  }

  const setCollapsed = (value: boolean) => {
    collapsed.value = value
  }

  const syncRouteTab = (route: RouteLocationNormalizedLoaded) => {
    const tab = transformRouteToTab(route)
    const existed = tabs.value.find((item) => item.path === tab.path)

    if (!existed) {
      tabs.value.push(tab)
    } else {
      existed.title = tab.title
      existed.closable = tab.closable
    }

    activePath.value = tab.path
  }

  const transformRouteToTab = (route: RouteLocationNormalizedLoaded): LayoutTab => {
    const metaTitle = (route.meta?.tabTitle || route.meta?.title || route.name) as string | undefined
    const title = metaTitle || '未命名页面'
    const affix = Boolean(route.meta?.affix)
    const closable = typeof route.meta?.closable === 'boolean' ? route.meta.closable : !affix

    return {
      path: route.fullPath,
      name: route.name,
      title,
      closable
    }
  }

  const removeTab = (path: string) => {
    // 防止删除最后一个标签页
    if (tabs.value.length <= 1) {
      return activePath.value
    }

    // 查找要删除的标签页索引
    const index = tabs.value.findIndex((item) => item.path === path)
    if (index === -1) {
      return activePath.value
    }

    // 删除标签页
    tabs.value.splice(index, 1)

    // 如果删除的是当前激活的标签页，需要重新设置激活项
    if (activePath.value === path) {
      const nextTab = tabs.value[index] || tabs.value[index - 1] || tabs.value[0]
      activePath.value = nextTab ? nextTab.path : ''
    }

    return activePath.value
  }

  const refreshPage = (delay: number = 200) => {
    // 已经在刷新中就不重复触发
    if (reloadFlag.value) return
    // 显示 loading
    reloadFlag.value = true

    window.setTimeout(() => {
      // 触发 router-view 重新渲染
      reloadKey.value = Date.now()
      // 刷新结束，隐藏 loading
      reloadFlag.value = false
    }, delay)
  }

  const setActivePath = (path: string) => {
    activePath.value = path
  }

  const resetTabs = () => {
    tabs.value = []
    activePath.value = ''
    reloadKey.value = Date.now()
    reloadFlag.value = false
  }

  return {
    collapsed,
    tabs,
    activePath,
    reloadKey,
    reloadFlag,
    toggleCollapsed,
    setCollapsed,
    syncRouteTab,
    transformRouteToTab,
    removeTab,
    refreshPage,
    setActivePath,
    resetTabs
  }
})
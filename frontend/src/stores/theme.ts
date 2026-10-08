import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(false)
  const initialized = ref(false)

  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  const setTheme = (theme: 'light' | 'dark') => {
    isDark.value = theme === 'dark'
  }

  const initTheme = () => {
    if (initialized.value) return
    if (typeof window === 'undefined') return

    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    if (savedTheme) {
      isDark.value = savedTheme === 'dark'
    } else {
      // 默认设置为白色主题
      isDark.value = false
    }

    applyTheme(isDark.value)
    initialized.value = true
  }

  const applyTheme = (dark: boolean) => {
    const root = document.documentElement
    root.classList.toggle('dark', dark)
    document.body.setAttribute('data-theme', dark ? 'dark' : 'light')
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  const setLightTheme = () => {
    isDark.value = false
    applyTheme(false)
  }

  return {
    isDark,
    toggleTheme,
    setTheme,
    setLightTheme,
    initTheme
  }
})
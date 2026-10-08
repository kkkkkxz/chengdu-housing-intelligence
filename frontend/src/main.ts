import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import { useThemeStore } from './stores/theme'
import 'virtual:uno.css'
import '@styles/css/reset.css'
import '@styles/css/global.css'
import '@styles/css/transition.css'
import '@styles/css/nprogress.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// 将先初始化主题，避免首屏闪烁
const themeStore = useThemeStore(pinia)
themeStore.initTheme()
// 强制设置为白色主题
themeStore.setLightTheme()

app.mount('#app')
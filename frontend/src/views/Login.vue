<template>
  <div class="relative w-full h-screen flex items-center justify-center overflow-hidden" :style="{ backgroundColor: bgColor }">
    <n-card :bordered="false" class="relative z-4 rd-12px w-auto login-card">
      <div class="w-400px lt-sm:w-300px">
        <header class="flex items-center justify-center py-6">
          <h3 class="text-20px font-600 text-center lt-sm:text-18px login-title">二手房数据分析系统</h3>
        </header>
        <main class="pt-6">
          <h3 class="text-18px text-primary font-medium">密码登录</h3>
          <div class="pt-6">
            <n-form ref="formRef" :model="formData" :rules="rules" size="large" :show-label="false" @keyup.enter="handleLogin">
              <n-form-item path="username">
                <n-input :value="formData.username" @update:value="updateUsername" placeholder="请输入用户名" />
              </n-form-item>
              <n-form-item path="password">
                <n-input :value="formData.password" @update:value="updatePassword" type="password" show-password-on="click" placeholder="请输入密码" />
              </n-form-item>
              <n-space vertical :size="24">
                <div class="flex items-center justify-between">
                  <n-checkbox :checked="rememberMe" @update:checked="onUpdateRemember">记住我</n-checkbox>
                </div>
                <n-button type="primary" size="large" round block :loading="authStore.loading" @click="handleLogin">确认</n-button>
                <div class="flex items-center justify-between gap-3">
                  <n-button class="flex-1" block @click="goToRegister">注册</n-button>
                </div>
                <n-divider class="text-14px text-#666 !m-0">其他登录方式</n-divider>
                <div class="flex items-center justify-center gap-3">
                  <n-button @click="handleSocialLogin('wechat')">微信</n-button>
                  <n-button @click="handleSocialLogin('qq')">QQ</n-button>
                  <n-button @click="handleSocialLogin('github')">GitHub</n-button>
                </div>
              </n-space>
            </n-form>
          </div>
        </main>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import { 
  NForm, NFormItem, NInput, NButton, NCheckbox, NDivider, NCard, NSpace,
  FormInst, FormRules, FormValidationError
} from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()


const formRef = ref<FormInst | null>(null)
const rememberMe = ref(false)

const formData = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { 
      required: true, 
      message: '请输入用户名', 
      trigger: 'blur' 
    },
    { 
      min: 3, 
      max: 20, 
      message: '用户名长度为3到20个字符', 
      trigger: 'blur' 
    }
  ],
  password: [
    { 
      required: true, 
      message: '请输入密码', 
      trigger: 'blur' 
    },
    { 
      min: 6, 
      max: 20, 
      message: '密码长度为6到20个字符', 
      trigger: 'blur' 
    }
  ]
}

function updateUsername(val: string) {
  formData.username = val
}

function updatePassword(val: string) {
  formData.password = val
}

// 背景主题色
const themeColor = '#6366f1'
const bgThemeColor = themeColor
const bgColor = computed(() => {
  const COLOR_WHITE = '#ffffff'
  const ratio = 0.2
  function hexToRgb(hex: string) {
    const normalized = hex.replace('#', '')
    const bigint = parseInt(normalized.length === 3 
      ? normalized.split('').map(c => c + c).join('') 
      : normalized, 16)
    const r = (bigint >> 16) & 255
    const g = (bigint >> 8) & 255
    const b = bigint & 255
    return { r, g, b }
  }
  function rgbToHex(r: number, g: number, b: number) {
    const toHex = (v: number) => Math.min(Math.max(v, 0), 255).toString(16).padStart(2, '0')
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`
  }
  function mixColor(hex: string, other: string, ratio: number) {
    const a = hexToRgb(hex)
    const b = hexToRgb(other)
    const r = Math.round(a.r * (1 - ratio) + b.r * ratio)
    const g = Math.round(a.g * (1 - ratio) + b.g * ratio)
    const bl = Math.round(a.b * (1 - ratio) + b.b * ratio)
    return rgbToHex(r, g, bl)
  }
  return mixColor(COLOR_WHITE, themeColor, ratio)
})

const handleLogin = async (e: Event) => {
  e.preventDefault()
  formRef.value?.validate(async (errors: FormValidationError[] | undefined) => {
    if (!errors) {
      const success = await authStore.login(formData)
      if (success) {
        // 登录成功后进入仪表盘
        router.push('/dashboard')
      }
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}

const handleSocialLogin = (platform: string) => {
  console.log(`使用 ${platform} 登录`)
}

const onUpdateRemember = (val: boolean) => {
  rememberMe.value = val
}


</script>

<style scoped>
/* 简洁登录卡片样式 */
.login-card {
  background-color: #ffffff !important;
  color: #000000 !important;
  border-radius: 12px !important;
  border: 1px solid #e5e7eb !important;
}

/* 覆盖 Naive UI 卡片内部 body 的内边距 */
.login-card :deep(.n-card__body),
.login-card :deep(.n-card__content) {
  padding: 20px 28px !important;
}

.login-title {
  color: #000000 !important;
  margin: 0;
}

/* 登录页面文字颜色强制设置为黑色 */
.login-card h3 {
  color: #000000 !important;
}

.login-card .text-#666,
.login-card .text-gray-400,
.login-card .text-gray-600 {
  color: #666666 !important;
}

.login-card .text-primary {
  color: #000000 !important;
}

/* 调整确认按钮颜色以匹配白色主题 */
.login-card :deep(.n-button--primary) {
  background: linear-gradient(90deg, #4f46e5, #7c3aed) !important;
  border: none !important;
}
</style>
<template>
  <div class="relative w-full h-screen flex items-center justify-center overflow-hidden" :style="{ backgroundColor: bgColor }">
    <div :themeColor="bgThemeColor" />
    <WaveBg :themeColor="bgThemeColor" />
    <n-card :bordered="false" class="relative z-4 rd-12px w-auto px-6 py-6">
      <div class="w-640px lt-sm:w-320px">
        <header class="flex items-center justify-between">
          <SystemLogo class="text-64px text-primary lt-sm:text-48px" />
          <h3 class="text-28px text-primary font-500 lt-sm:text-22px">创建账号</h3>
          <div class="flex flex-col"></div>
        </header>
        <main class="pt-6">
          <div class="text-14px text-#666">完善信息，开启二手房数据分析之旅</div>
          <div class="pt-6">
            <n-form ref="formRef" :model="formData" :rules="rules" size="large" :show-label="false" @keyup.enter="handleRegister">
              <n-grid :cols="24" x-gap="16" y-gap="12">
                <n-gi :span="12">
                  <n-form-item
                    path="username"
                    :feedback="usernameCheck.message"
                    :validation-status="usernameCheck.status === null ? undefined : (usernameCheck.status ? 'success' : 'error')"
                  >
                    <n-input :value="formData.username" @update:value="updateUsername" placeholder="请输入用户名" @input="checkUsername" />
                  </n-form-item>
                </n-gi>
                <n-gi :span="12">
                  <n-form-item path="email">
                    <n-input :value="formData.email" @update:value="updateEmail" placeholder="请输入邮箱" />
                  </n-form-item>
                </n-gi>

                <n-gi :span="12">
                  <n-form-item path="nickname">
                    <n-input :value="formData.nickname" @update:value="updateNickname" placeholder="请输入昵称（可选）" />
                  </n-form-item>
                </n-gi>
                <n-gi :span="12">
                  <n-form-item path="phone">
                    <n-input :value="formData.phone" @update:value="updatePhone" placeholder="请输入手机号（可选）" />
                  </n-form-item>
                </n-gi>

                <n-gi :span="12">
                  <n-form-item path="password">
                    <n-input :value="formData.password" @update:value="updatePassword" type="password" show-password-on="click" placeholder="请输入密码" />
                  </n-form-item>
                </n-gi>
                <n-gi :span="12">
                  <n-form-item path="confirm_password">
                    <n-input :value="formData.confirm_password" @update:value="updateConfirmPassword" type="password" show-password-on="click" placeholder="请再次输入密码" />
                  </n-form-item>
                </n-gi>

                <n-gi :span="24">
                  <n-progress :percentage="passwordStrength" :color="passwordStrengthColor" :height="4" :show-indicator="false" />
                  <div class="password-hint text-sm text-gray-400 mt-1">密码强度：{{ passwordStrengthText }}</div>
                </n-gi>

                <n-gi :span="24">
                  <input type="hidden" :value="formData.user_type">
                  <n-form-item>
                    <n-checkbox :checked="agreeTerms" @update:checked="onUpdateAgree">
                      我已阅读并同意
                      <n-button text type="primary" @click="showTerms">用户协议</n-button>
                      和
                      <n-button text type="primary" @click="showPrivacy">隐私政策</n-button>
                    </n-checkbox>
                  </n-form-item>
                </n-gi>

                <n-gi :span="24">
                  <n-form-item>
                    <n-button type="primary" block :loading="authStore.loading" :disabled="!agreeTerms" round size="large" @click="handleRegister">注册</n-button>
                  </n-form-item>
                </n-gi>

                <n-gi :span="24">
                  <n-form-item>
                    <div class="login-link text-center text-gray-400 w-full">
                      已有账号？
                      <n-button text type="primary" @click="goToLogin">立即登录</n-button>
                    </div>
                  </n-form-item>
                </n-gi>
              </n-grid>
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
import { authApi } from '../api/auth'
import { 
  NForm, NFormItem, NInput, NButton, NCheckbox,
  NIcon, NProgress, FormInst, FormRules, FormValidationError, NCard, NGrid, NGi
} from 'naive-ui'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInst | null>(null)
const agreeTerms = ref(false)
const usernameCheck = ref({ status: null as boolean | null, message: '' })

const formData = reactive({
  username: '',
  email: '',
  phone: '',
  nickname: '',
  password: '',
  confirm_password: '',
  user_type: 'user'
})

const passwordStrength = computed(() => {
  const password = formData.password
  if (!password) return 0

  let strength = 0
  if (password.length >= 6) strength += 20
  if (password.length >= 8) strength += 20
  if (/[a-z]/.test(password)) strength += 20
  if (/[A-Z]/.test(password)) strength += 20
  if (/[0-9]/.test(password)) strength += 20

  return strength
})

const passwordStrengthColor = computed(() => {
  if (passwordStrength.value < 40) return '#ff4d4f'
  if (passwordStrength.value < 80) return '#faad14'
  return '#52c41a'
})

const passwordStrengthText = computed(() => {
  if (passwordStrength.value < 40) return '弱'
  if (passwordStrength.value < 80) return '中'
  return '强'
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3到20个字符', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '用户名只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ],
  email: [
    {
      pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      message: '请输入有效的邮箱地址',
      trigger: 'blur'
    }
  ],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '请输入有效的手机号',
      trigger: 'blur'
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为6到20个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value) => {
        if (value !== formData.password) {
          return new Error('两次密码输入不一致')
        }
        return true
      },
      trigger: 'blur'
    }
  ]
}

// 检查用户名是否可用
const checkUsername = async () => {
  if (!formData.username || formData.username.length < 3) {
    usernameCheck.value = { status: null, message: '' }
    return
  }

  try {
    const response: any = await authApi.checkUsername(formData.username)
    // 后端返回格式: { exists: boolean, username: string }
    if (response.exists) {
      usernameCheck.value = { status: false, message: '用户名已存在' }
    } else {
      usernameCheck.value = { status: true, message: '用户名可用' }
    }
  } catch (error) {
    usernameCheck.value = { status: false, message: '检查失败' }
  }
}

// 注册处理
const handleRegister = async (e: Event) => {
  e.preventDefault()
  formRef.value?.validate(async (errors: FormValidationError[] | undefined) => {
    if (!errors) {
      const success = await authStore.register(formData)
      if (success) {
        // 注册成功：清除用户名检查错误状态和表单验证错误
        usernameCheck.value = { status: null, message: '' }
        formRef.value?.restoreValidation()
        router.push('/dashboard')
      }
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}

const showTerms = () => {
  console.log('用户协议功能开发中')
}

const showPrivacy = () => {
  console.log('隐私政策功能开发中')
}

function updateUsername(val: string) {
  formData.username = val
}

function updateEmail(val: string) {
  formData.email = val
}

function updatePhone(val: string) {
  formData.phone = val
}

function updateNickname(val: string) {
  formData.nickname = val
}

function updatePassword(val: string) {
  formData.password = val
}

function updateConfirmPassword(val: string) {
  formData.confirm_password = val
}

function onUpdateAgree(val: boolean) {
  agreeTerms.value = val
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
</script>

<style scoped>
.check-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
  font-size: 0.875rem;
}

.n-card {
  color: #000000 !important;
}

.n-card h3 {
  color: #000000 !important;
}

.n-card .text-#666,
.n-card .text-gray-400,
.n-card .text-gray-600 {
  color: #666666 !important;
}

.n-card .login-link {
  color: #666666 !important;
}

.n-card .password-hint {
  color: #666666 !important;
}

@media (max-width: 768px) {
  .flex {
    flex-direction: column;
  }
}
</style>
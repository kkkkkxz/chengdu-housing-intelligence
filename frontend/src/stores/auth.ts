import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@api/auth'

export interface User {
  id: number
  username: string
  email: string
  phone: string
  nike_name: string
  avatar?: string
  gender?: string
  birthday?: string | null
  user_type: string
  is_verified: boolean
  date_joined?: string
  last_login: string
}

export const useAuthStore = defineStore('auth', () => {
    const router = useRouter()
    // const message = useMessage()

    const token = ref<string | null>(localStorage.getItem('token'))
    const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))
    const user = ref<User | null>(null)
    const isAdmin = computed(() => user.value?.user_type === 'admin')
    const isUser = computed(() => user.value?.user_type === 'user')
    const loading = ref(false)

  // Consider user authenticated only when user info is available.
  // This prevents automatic redirect when a raw token exists in localStorage
  // but user info hasn't been refreshed yet (e.g. on page reload).
  const isAuthenticated = computed(() => !!user.value)

// 登录
const login = async (loginData: { username: string; password: string }) => {
  try {
    loading.value = true
    const response: any = await authApi.login(loginData)

    // 兼容多种后端返回结构：直接 body、{data: ...}、以及 access/token 命名差异
    const body = response?.data ?? response
    console.log('login response body:', body)

    const access = body?.access ?? body?.token ?? body?.data?.access ?? body?.data?.token
    const refresh = body?.refresh ?? body?.refresh_token ?? body?.data?.refresh
    const respUser = body?.user ?? body?.data?.user ?? body?.data?.user_info ?? body?.data

    if (!access) {
      console.error('登录返回未包含 access/token 字段，response =', body)
      return false
    }

    token.value = access
    refreshToken.value = refresh ?? null
    user.value = respUser ?? null

    localStorage.setItem('token', access)
    if (refresh) localStorage.setItem('refreshToken', refresh)

    console.log('登录成功')
    return true
  } catch (error: any) {
    console.error('登录失败：', error.response?.data?.message || '登录失败')
    return false
  } finally {
    loading.value = false
  }
}

// 注册
const register = async (registerData: {
  username: string
  email?: string
  password: string
  confirm_password: string
  phone?: string
  nickname?: string
  user_type: string
}) => {
  try {
    loading.value = true
    // ensure payload matches RegisterRequest expected fields
    const payload = {
      ...registerData,
      // some backends expect config_password and nike_name
      config_password: registerData.confirm_password,
      nike_name: registerData.nickname ?? '',
      // ensure required string fields are present (avoid TS complaints)
      email: registerData.email ?? '',
      phone: registerData.phone ?? ''
    }
  const response: any = await authApi.register(payload)

  token.value = response.access
  refreshToken.value = response.refresh
  user.value = response.user

  localStorage.setItem('token', response.access)
  localStorage.setItem('refreshToken', response.refresh)

    console.log('注册成功')
    return true
  } catch (error: any) {
    console.error('注册失败：', error.response?.data?.message || '注册失败')
    throw error
  } finally {
    loading.value = false
  }
}

// 登出
const logout = () => {
  token.value = null
  refreshToken.value = null
  user.value = null

  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')

  console.log('已退出登录')
}

// 刷新用户信息
// const refreshUserInfo = async () => {
//   if (!token.value) return

//   try {
//     const response = await authApi.getUserInfo()
//     user.value = response.user
//     // 持久化头像等变更
//     if (user.value?.avatar) {
//       // no-op 占位，确保响应式更新
//       user.value.avatar = response.user.avatar
//     }
//   } catch (error) {
//     console.error('刷新用户信息失败：', error)
//   }
// }
const refreshUserInfo = async () => {
  if (!token.value) return

  try {
  const response: any = await authApi.getUserInfo()
  user.value = response.user
    // 持久化头像等变更
    if (user.value?.avatar) {
      // no-op 占位，确保响应式更新
      user.value.avatar = response.user.avatar
    }
  } catch (error) {
    console.error('刷新用户信息失败：', error)
  }
}


// 初始化用户状态
const initAuth = async () => {
  const savedToken = localStorage.getItem('token')
  if (savedToken) {
    token.value = savedToken
    refreshToken.value = localStorage.getItem('refreshToken')
    await refreshUserInfo()
  }
}

return {
  token,
  refreshToken,
  user,
  loading,
  isAuthenticated,
  login,
  register,
  logout,
  isAdmin,        // 新增
  isUser, 
  refreshUserInfo,
  initAuth
}
})
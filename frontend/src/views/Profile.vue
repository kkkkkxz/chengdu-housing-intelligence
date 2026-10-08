<template>
  <div class="p-4">
    <n-grid :cols="4" x-gap="16" y-gap="16">
      <n-gi :span="1">
        <n-card title="头像" :segmented="{ content: true }">
          <div class="flex flex-col items-center gap-3">
            <img v-if="profileAvatarUrl && !profileImgBroken" :src="profileAvatarUrl" class="w-96px h-96px rd-9999 object-cover border border-#e5e7eb" @error="onProfileImgError" />
            <n-avatar v-else :size="96" round>{{ authStore.user?.username?.[0]?.toUpperCase() || 'U' }}</n-avatar>
            <n-upload :max="1" :show-file-list="false" accept="image/*" :default-upload="true" :custom-request="handleAvatarUpload">
              <n-button>上传头像</n-button>
            </n-upload>
          </div>
        </n-card>
      </n-gi>
      <n-gi :span="3">
        <n-card title="基本信息" :segmented="{ content: true }">
          <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="120">
            <n-form-item label="用户名" path="username">
              <n-input :value="formData.username" disabled />
            </n-form-item>
            <n-form-item label="邮箱" path="email">
              <n-input :value="formData.email" @update:value="(v)=>formData.email=v" placeholder="请输入邮箱" />
            </n-form-item>
            <n-form-item label="手机号" path="phone">
              <n-input :value="formData.phone" @update:value="(v)=>formData.phone=v" placeholder="请输入手机号" />
            </n-form-item>
            <n-form-item label="昵称" path="nickname">
              <n-input :value="formData.nickname" @update:value="(v)=>formData.nickname=v" placeholder="请输入昵称" />
            </n-form-item>
            <n-form-item label="性别" path="gender">
              <n-radio-group :value="formData.gender" @update:value="onUpdateGender">
                <n-radio-button value="male">男</n-radio-button>
                <n-radio-button value="female">女</n-radio-button>
                <n-radio-button value="other">其他</n-radio-button>
              </n-radio-group>
            </n-form-item>
            <n-form-item label="生日" path="birthday">
              <n-date-picker :value="formData.birthday" type="date" @update:value="onUpdateBirthday" placeholder="请选择生日" />
            </n-form-item>

            <n-form-item>
              <n-button type="primary" @click="handleSave">保存修改</n-button>
            </n-form-item>
          </n-form>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

import { NCard, NGrid, NGi, NForm, NFormItem, NInput, NButton, NRadioGroup, NRadioButton, NDatePicker, NAvatar, NUpload, FormInst, FormRules, FormValidationError, UploadCustomRequestOptions } from 'naive-ui'
import { authApi } from '../api/auth'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
// const message = useMessage()

const formRef = ref<FormInst | null>(null)
// const showCropper = ref(false)

const formData = reactive({
  username: '',
  email: '',
  phone: '',
  nickname: '',
  gender: '',
  birthday: null,
})

const rules: FormRules = {
  email: [
    {
      pattern: /^[\s\S]+@[\s\S]+\.[\s\S]+$/,
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
  ]
}

const handleSave = async () => {
  formRef.value?.validate((errors: FormValidationError[] | undefined) => {
    if (!errors) {
      const payload: Record<string, any> = {
        nickname: formData.nickname,
        gender: formData.gender || undefined,
        birthday: (function(v: any){
          if (!v) return null
          if (typeof v === 'number') {
            const d = new Date(v)
            const yyyy = d.getFullYear()
            const mm = String(d.getMonth() + 1).padStart(2, '0')
            const dd = String(d.getDate()).padStart(2, '0')
            return `${yyyy}-${mm}-${dd}`
          }
          if (v instanceof Date) {
            const yyyy = v.getFullYear()
            const mm = String(v.getMonth() + 1).padStart(2, '0')
            const dd = String(v.getDate()).padStart(2, '0')
            return `${yyyy}-${mm}-${dd}`
          }
          return String(v)
        })(formData.birthday),
        email: formData.email,
        phone: formData.phone
      }
      authApi.updateProfile(payload).then(async () => {
        await authStore.refreshUserInfo()
      })
    }
  })
}

async function handleAvatarUpload(options: UploadCustomRequestOptions) {
  const file = (options.file as any)?.file as File
  if (!file) {
    options.onError && options.onError()
    return
  }
  try {
    const res: any = await authApi.updateAvatar(file)
    if (res?.user) {
      authStore.user = res.user
    } else {
      await authStore.refreshUserInfo()
    }
    options.onFinish && options.onFinish()
  } catch (err) {
    options.onError && options.onError()
  }
}

function onUpdateGender(v: unknown) { formData.gender = v as any }
function onUpdateBirthday(v: unknown) { formData.birthday = v as any }

const loadUserData = () => {
  if (authStore.user) {
    formData.username = authStore.user.username || ''
    formData.email = authStore.user.email || ''
    formData.phone = authStore.user.phone || ''
    formData.nickname = authStore.user.nike_name || ''  // 修复：将 nickname 改为 nike_name
    formData.gender = (authStore.user.gender as any) || ''
    formData.birthday = authStore.user.birthday ? (new Date(authStore.user.birthday as string).getTime() as any) : null
  }
}

onMounted(() => {
  loadUserData()
})

const profileImgBroken = ref(false)
const profileAvatarUrl = computed(() => {
  const raw = (authStore.user?.avatar || '').trim()
  if (!raw) return undefined
  const stamp = Date.now()
  let url = raw
  if (!/^https?:\/\/./i.test(url)) {
    url = url.startsWith('/media/') ? url : `/media/${url.replace(/^\//, '')}`
  }
  return `${url}${url.includes('?') ? '&' : '?'}t=${stamp}`
})

function onProfileImgError() {
  profileImgBroken.value = true
}
</script>

<style scoped>
.content {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
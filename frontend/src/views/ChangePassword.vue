<template>
  <div class="password-page p-6 md:p-10">
    <div class="max-w-1100px mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-16">
        <div class="md:col-span-2">
          <n-card title="修改密码" :segmented="{ content: true }">
            <n-alert type="info" show-icon class="mb-4 tip-text">
              为保障账号安全，建议定期更换密码，并确保新密码与旧密码不同。
            </n-alert>
            <n-form :model="form" :rules="rules" ref="formRef" label-placement="left" label-width="120">
              <n-form-item label="当前密码" path="old_password">
                <n-input
                  :value="form.old_password"
                  type="password"
                  show-password-on="click"
                  placeholder="请输入当前密码"
                  @update:value="(v) => (form.old_password = v)"
                />
              </n-form-item>
              <n-form-item label="新密码" path="new_password">
                <div class="w-full flex flex-col gap-3">
                  <n-input
                    :value="form.new_password"
                    type="password"
                    show-password-on="click"
                    placeholder="至少 6 位，建议 8 位以上"
                    @update:value="(v) => (form.new_password = v)"
                  />
                  <div class="w-full">
                    <n-progress :percentage="passwordStrength" :color="passwordStrengthColor" :height="4" :show-indicator="false" />
                    <div class="strength-text">密码强度：{{ passwordStrengthText }}</div>
                  </div>
                </div>
              </n-form-item>
              <n-form-item label="确认新密码" path="confirm_password">
                <n-input
                  :value="form.confirm_password"
                  type="password"
                  show-password-on="click"
                  placeholder="再次输入新密码"
                  @update:value="(v) => (form.confirm_password = v)"
                />
              </n-form-item>

              <div class="security-advice">
                建议使用 8-20 位字符，并包含大小写字母与数字的组合，避免使用与账号相关的个人信息或连续、重复字符。
              </div>

              <n-form-item>
                <div class="flex items-center gap-3 justify-end w-full">
                  <n-button quaternary :disabled="submitting" @click="onCancel">取消</n-button>
                  <n-button type="primary" strong :loading="submitting" @click="onSubmit">保存修改</n-button>
                </div>
              </n-form-item>
            </n-form>
          </n-card>
        </div>

        <div class="md:col-span-1">
          <n-card title="安全提示" :segmented="{ content: true }" class="sticky top-16">
            <ul class="suggestion-list">
              <li>使用 8 位以上长度，包含大小写字母与数字。</li>
              <li>避免使用生日、手机号、连续或重复字符。</li>
              <li>不同网站使用不同密码，定期更新。</li>
            </ul>
          </n-card>
          <div class="h-4"></div>
          <n-card title="温馨提醒" :segmented="{ content: true }">
            <div class="reminder-text">若你在公共设备上操作，请确保操作完成后及时退出登录。</div>
          </n-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import type { FormInst, FormRules } from 'naive-ui'

const router = useRouter()
const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const form = ref({ old_password: '', new_password: '', confirm_password: '' })

const passwordStrength = computed(() => {
  const password = form.value.new_password
  if (!password) return 0
  let strength = 0
  if (password.length >= 6) strength += 20
  if (password.length >= 8) strength += 20
  if (/[a-z]/.test(password)) strength += 20
  if (/[A-Z]/.test(password)) strength += 20
  if (/[0-9]/.test(password)) strength += 20
  return Math.min(strength, 100)
})

const passwordStrengthColor = computed(() => {
  if (passwordStrength.value < 40) return '#ff4d4f'
  if (passwordStrength.value < 80) return '#faad14'
  return '#18a058'
})

const passwordStrengthText = computed(() => {
  if (passwordStrength.value < 40) return '弱'
  if (passwordStrength.value < 80) return '中'
  return '强'
})

const rules: FormRules = {
  old_password: { required: true, message: '请输入当前密码', trigger: 'blur' },
  new_password: { required: true, min: 6, message: '至少 6 位新密码', trigger: 'blur' },
  confirm_password: {
    validator: () => form.value.new_password === form.value.confirm_password,
    message: '两次输入不一致',
    trigger: 'blur'
  }
}

function onSubmit() {
  formRef.value?.validate(async (err) => {
    if (err) return
    submitting.value = true
    try {
      await authApi.changePassword(form.value)
      router.back()
    } finally {
      submitting.value = false
    }
  })
}

function onCancel() {
  router.back()
}
</script>

<style scoped>
.password-page {
  background-color: var(--page-bg-color);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.max-w-1100px {
  max-width: 1100px;
}

.tip-text {
  color: var(--text-secondary-color);
}

.strength-text {
  font-size: 12px;
  margin-top: 4px;
  color: var(--text-secondary-color);
}

.security-advice {
  font-size: 12px;
  color: var(--text-secondary-color);
  margin-bottom: 24px;
  line-height: 1.6;
}

.suggestion-list {
  padding-left: 18px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary-color);
}

.reminder-text {
  font-size: 13px;
  color: var(--text-secondary-color);
  line-height: 1.7;
}
</style>
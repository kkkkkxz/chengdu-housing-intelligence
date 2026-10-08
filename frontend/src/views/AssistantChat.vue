<template>
  <div class="assistant-chat-page">
    <n-card class="assistant-card" :bordered="false">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <n-icon size="20">
              <Sparkles />
            </n-icon>
            <span class="header-title">智能问答助手</span>
          </div>
          <n-space size="small">
            <n-button tertiary size="small" @click="refreshContext" :disabled="loading">
              <template #icon>
                <n-icon>
                  <Refresh />
                </n-icon>
              </template>
              清空上下文
            </n-button>
          </n-space>
        </div>
      </template>

      <n-space vertical :size="16">
        <n-alert type="info" class="assistant-tip" :show-icon="false">
          <div class="tip-title">使用建议</div>
          <ul class="tip-list">
            <li>围绕二手房数据分析、价格预测、区域对比、收藏偏好等场景提问。</li>
            <li>可直接引用仪表盘、价格分析页中的指标，如“总价区间”“户型分布”等。</li>
            <li>支持多轮追问，若需重置会话请点击右上角的“清空上下文”。</li>
          </ul>
        </n-alert>

        <n-space size="small" wrap>
          <n-button
            v-for="preset in presets"
            :key="preset"
            size="small"
            tertiary
            @click="handlePreset(preset)"
            :disabled="loading"
          >
            {{ preset }}
          </n-button>
        </n-space>

        <n-card class="chat-container" bordered :content-style="{ padding: '0', height: '100%' }">
          <n-scrollbar ref="scrollbarRef" style="height: 100%;">
            <div class="chat-messages">
              <transition-group name="fade" tag="div">
                <div
                  v-for="(item, index) in messages"
                  :key="item.id"
                  class="chat-item"
                  :class="{ 'is-self': item.role === 'user' }"
                >
                  <div class="avatar">
                    <n-avatar round size="small" v-if="item.role === 'assistant'">
                      <n-icon>
                        <Sparkles />
                      </n-icon>
                    </n-avatar>
                    <n-avatar round size="small" v-else>
                      <n-icon>
                        <PersonCircle />
                      </n-icon>
                    </n-avatar>
                  </div>
                  <div class="bubble">
                    <div class="bubble-header">
                      <span class="name">
                        {{ item.role === 'assistant' ? '小屋智能助手' : displayName }}
                      </span>
                      <span class="time">{{ formatTime(item.createdAt) }}</span>
                    </div>
                    <div class="bubble-content">
                      <markdown-render :content="item.content" />
                    </div>
                  </div>
                </div>
              </transition-group>
              <div v-if="loading" class="chat-loading">
                <n-spin size="small" />
                <span>助手正在思考...</span>
              </div>
            </div>
          </n-scrollbar>
        </n-card>

        <div class="chat-input">
          <n-input
            v-model:value="inputValue"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="请输入想咨询的问题，支持 Ctrl + Enter 快捷发送"
            @keydown="handleKeydown"
            :disabled="loading"
          />
          <div class="input-actions">
            <span class="shortcut-hint">按 Ctrl + Enter 快捷发送</span>
            <n-button type="primary" :loading="loading" :disabled="!inputValue.trim()" @click="handleSend">
              <template #icon>
                <n-icon>
                  <Send />
                </n-icon>
              </template>
              发送
            </n-button>
          </div>
        </div>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { NAlert, NAvatar, NButton, NCard, NIcon, NInput, NScrollbar, NSpin, NSpace } from 'naive-ui'
import type { ScrollbarInst } from 'naive-ui'
import { Send, Sparkles, Refresh, PersonCircle } from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { assistantApi, type ChatHistoryItem } from '@/api/assistant'
import MarkdownRender from '@/components/common/MarkdownRender.vue'
import { useMessage } from 'naive-ui'

interface ChatMessage extends ChatHistoryItem {
  id: string
  createdAt: number
}

const authStore = useAuthStore()
const message = useMessage()
const scrollbarRef = ref<ScrollbarInst | null>(null)

const createId = () =>
  typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `msg-${Date.now()}-${Math.random().toString(16).slice(2)}`

const messages = ref<ChatMessage[]>([
  {
    id: createId(),
    role: 'assistant',
    content:
      '你好！我是小屋智能助手，可以为你解读二手房市场指标、仪表盘图表，以及预测模型的含义。可以问我：“近三个月成交价格走势如何？”或“如何筛主城区三居室房源？”',
    createdAt: Date.now(),
  },
])

const presets = [
  '帮我分析一下成都二手房价格差异',
  '如何使用价格分析页判断成交热点区域？',
  '收藏夹中的房源可以给出投资建议吗？',
  '如果我要预测未来两个月价格走势，需要注意哪些数据？',
]

const inputValue = ref('')
const loading = ref(false)

const displayName = computed(() => authStore.user?.nike_name || authStore.user?.username || '我')

function formatTime(timestamp: number) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    const scrollbar = scrollbarRef.value
    if (scrollbar) {
      try {
        scrollbar.scrollTo({
          top: Number.MAX_SAFE_INTEGER,
          behavior: 'smooth',
        })
      } catch (error) {
        const scrollContainer = document.querySelector('.n-scrollbar-content')
        if (scrollContainer) {
          scrollContainer.scrollTop = scrollContainer.scrollHeight
        }
      }
    }
  })
}

function addMessage(role: ChatMessage['role'], content: string) {
  const item: ChatMessage = {
    id: createId(),
    role,
    content,
    createdAt: Date.now(),
  }
  messages.value.push(item)
  scrollToBottom()
}

// ... existing code ...
async function handleSend() {
  const text = inputValue.value.trim()
  if (!text || loading.value) return

  addMessage('user', text)
  inputValue.value = ''

  loading.value = true
  try {
    const history = messages.value
      .slice(0, -1)
      .map(({ id, role, content }) => ({ id, role, content }))
    const response = await assistantApi.chat({ message: text, history })
    addMessage('assistant', response.reply || '暂时没能获取到详细信息，请稍后再试。')
  } catch (error: any) {
  console.error('=== 完整错误对象 ===', error)
  console.error('error.message:', error.message)
  console.error('error.code:', error.code)
  console.error('error.response:', error.response)
  console.error('error.request:', error.request)
  const errText = error.response?.data?.message || error.message || '服务暂时不可用，请稍后再试。'
  message.error(errText)
  addMessage('assistant', `抱歉，调用智能助手失败，原因：${errText}`)
  } finally {
    loading.value = false
  }
}
// ... existing code ...
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault()
    handleSend()
  }
}

function handlePreset(text: string) {
  inputValue.value = text
  handleSend()
}

function refreshContext() {
  if (loading.value) return
  messages.value = messages.value.slice(0, 1)
  message.success('会话上下文已清空')
  scrollToBottom()
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.assistant-chat-page {
  padding: 16px;
  min-height: calc(100vh - 120px);
  background-color: var(--page-bg-color);
  display: flex;
  justify-content: center;
}

.assistant-card {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.assistant-tip {
  border-radius: 6px;
}

.tip-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.tip-list {
  padding-left: 20px;
  margin: 0;
}

.chat-container {
  height: 400px;
}

.chat-messages {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
}

.chat-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.chat-item.is-self {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
}

.bubble {
  max-width: 80%;
}

.is-self .bubble {
  text-align: right;
}

.bubble-header {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}

.is-self .bubble-header {
  justify-content: flex-end;
}

.bubble-content {
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.bubble-content :deep(p) {
  margin: 0 0 10px 0;
}

.bubble-content :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-item:not(.is-self) .bubble-content {
  background-color: #f5f5f5;
}

.is-self .bubble-content {
  background-color: #18a058;
  color: white;
}

.chat-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  color: #666;
}

.chat-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.shortcut-hint {
  font-size: 12px;
  color: #999;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .assistant-chat-page {
    padding: 12px;
  }
  
  .assistant-card {
    box-shadow: none;
  }
  
  .bubble {
    max-width: 75%;
  }
}
</style>
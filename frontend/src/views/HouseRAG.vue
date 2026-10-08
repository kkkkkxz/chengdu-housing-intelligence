<!-- src/views/assistant/AssistantChat.vue -->
<template>
  <div class="assistant-container">
    <n-card :bordered="false" class="chat-card">
      <template #header>
        <div class="chat-header">
          <n-icon size="24" color="#18a058">
            <Sparkles />
          </n-icon>
          <span class="title">智能问答助手</span>
          <n-button size="small" quaternary @click="clearHistory">
            <template #icon>
              <n-icon><TrashOutline /></n-icon>
            </template>
            清除历史
          </n-button>
        </div>
      </template>
      <div class="chat-messages-wrapper">
        <n-scrollbar ref="scrollbarRef" class="chat-messages">
          <div v-for="(msg, idx) in messages" :key="idx" class="message-item">
            <div :class="['message', msg.role]">
              <div class="avatar">
                <n-avatar v-if="msg.role === 'assistant'" round size="small" :src="assistantAvatar" />
                <n-avatar v-else round size="small" :src="userAvatar" />
              </div>
              <div class="content" v-html="formatMessage(msg.content)"></div>
            </div>
          </div>
          <div v-if="loading" class="message-item">
            <div class="message assistant">
              <div class="avatar">
                <n-avatar round size="small" :src="assistantAvatar" />
              </div>
              <div class="content typing">
                <n-spin size="small" />
                <span style="margin-left: 8px">思考中...</span>
              </div>
            </div>
          </div>
        </n-scrollbar>
      </div>
      <div class="input-area">
        <n-input
          v-model:value="question"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="输入您的问题，例如：成都市锦江区有哪些房源？"
          @keydown.enter.exact.prevent="sendQuestion"
          :disabled="loading"
        />
        <n-button
          type="primary"
          :loading="loading"
          :disabled="!question.trim()"
          @click="sendQuestion"
          style="margin-left: 12px"
        >
          发送
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import axios from 'axios'
import { Sparkles, TrashOutline } from '@vicons/ionicons5'

const message = useMessage()
const question = ref('')
const loading = ref(false)
const messages = ref<Array<{ role: 'user' | 'assistant', content: string }>>([])
const scrollbarRef = ref<any>(null)

// 头像（可替换为真实图片）
const assistantAvatar = 'https://api.dicebear.com/7.x/bottts/svg?seed=assistant'
const userAvatar = 'https://api.dicebear.com/7.x/avataaars/svg?seed=user'

// 会话ID（存储在 localStorage 中，保持同一浏览器对话历史）
const sessionId = ref('')

// 获取或生成 session_id
const getSessionId = () => {
  let sid = localStorage.getItem('rag_session_id')
  if (!sid) {
    sid = crypto.randomUUID ? crypto.randomUUID() : Date.now() + '-' + Math.random()
    localStorage.setItem('rag_session_id', sid)
  }
  return sid
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (scrollbarRef.value) {
      const scrollEl = scrollbarRef.value.$el?.querySelector('.n-scrollbar-container')
      if (scrollEl) {
        scrollEl.scrollTop = scrollEl.scrollHeight
      }
    }
  })
}

// 格式化消息（支持换行和简单 markdown）
const formatMessage = (text: string) => {
  return text.replace(/\n/g, '<br>')
}

// 发送问题
const sendQuestion = async () => {
  const q = question.value.trim()
  if (!q) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: q })
  question.value = ''
  scrollToBottom()
  loading.value = true

  try {
    const response = await axios.post('/api/rag/ask/', {
      question: q,
      session_id: sessionId.value
    })
    const answer = response.data.answer
    messages.value.push({ role: 'assistant', content: answer })
    scrollToBottom()
  } catch (error: any) {
    console.error('请求失败', error)
    message.error(error.response?.data?.error || '网络错误，请稍后再试')
    // 可选：添加错误提示消息
    messages.value.push({ role: 'assistant', content: '抱歉，出了点问题，请稍后再试。' })
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

// 清除历史
const clearHistory = async () => {
  try {
    await axios.post('/api/rag/clear/', { session_id: sessionId.value })
    messages.value = []
    message.success('对话历史已清除')
  } catch (error) {
    console.error('清除历史失败', error)
    message.error('清除历史失败')
  }
}

onMounted(() => {
  sessionId.value = getSessionId()
})
</script>

<style scoped lang="scss">
.assistant-container {
  height: 100%;
  width: 100%;
  padding: 0;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  :deep(.n-card__content) {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    padding: 0;
  }
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  .title {
    font-size: 18px;
    font-weight: 500;
    flex: 1;
  }
}

.chat-messages-wrapper {
  flex: 1;
  overflow: hidden;
  background: var(--n-color-body);
  border-radius: 8px;
  margin: 8px 0;
}

.chat-messages {
  height: 100%;
  padding: 16px;
}

.message-item {
  margin-bottom: 16px;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  .avatar {
    flex-shrink: 0;
  }
  .content {
    max-width: 80%;
    background: var(--n-color);
    padding: 10px 14px;
    border-radius: 12px;
    line-height: 1.5;
    word-break: break-word;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  }
  &.assistant .content {
    background: #f0f2f5;
    border-top-left-radius: 4px;
  }
  &.user {
    flex-direction: row-reverse;
    .content {
      background: #18a058;
      color: white;
      border-top-right-radius: 4px;
    }
  }
  .typing {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.input-area {
  display: flex;
  align-items: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--n-border-color);
  :deep(.n-input) {
    flex: 1;
  }
}
</style>
import request from './request'

export interface ChatHistoryItem {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequestPayload {
  message: string
  history?: ChatHistoryItem[]
}

export interface ChatResponse {
  reply: string
}

export const assistantApi = {
  /** 发送问题至 AI 助手 */
  async chat(data: ChatRequestPayload): Promise<ChatResponse> {
    // request.post 实际返回的是 response.data（因为拦截器解包了）
    // 但 TypeScript 类型定义仍是 AxiosResponse，所以用 as 断言
    const result = await request.post<ChatResponse>('/assistant/chat/', data)
    return result as unknown as ChatResponse
  }
}
/**
 * SSE 流式处理 Composable
 * 职责：封装 Server-Sent Events 流式数据处理逻辑
 */
import { ref } from 'vue'

export interface SSEMessage {
  type: string
  [key: string]: any
}

export interface SSEStreamOptions {
  onMessage?: (data: SSEMessage) => void
  onComplete?: (data: SSEMessage) => void
  onError?: (data: SSEMessage) => void
}

export function useSSEStream() {
  const connecting = ref(false)
  const error = ref<string | null>(null)

  const connect = async (
    url: string,
    body: any,
    options: SSEStreamOptions = {}
  ): Promise<void> => {
    connecting.value = true
    error.value = null

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6)) as SSEMessage

            // 分发事件
            if (data.type === 'log' && options.onMessage) {
              options.onMessage(data)
            } else if (data.type === 'complete' && options.onComplete) {
              options.onComplete(data)
            } else if (data.type === 'error' && options.onError) {
              options.onError(data)
            }
          }
        }
      }
    } catch (err) {
      error.value = (err as Error).message
      if (options.onError) {
        options.onError({ type: 'error', message: error.value })
      }
      throw err
    } finally {
      connecting.value = false
    }
  }

  return {
    connecting,
    error,
    connect
  }
}

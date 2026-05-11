/**
 * WebSocket Composable - 用于接收任务进度推送
 */
import { ref } from 'vue'

export interface WSMessage {
  type: string
  [key: string]: any
}

export interface WSOptions {
  onProgress?: (data: WSMessage) => void
  onComplete?: (data: WSMessage) => void
  onError?: (data: WSMessage) => void
}

export function useWebSocket() {
  const connecting = ref(false)
  const error = ref<string | null>(null)

  const connect = async (
    executionId: string,
    options: WSOptions = {}
  ): Promise<void> => {
    connecting.value = true
    error.value = null

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/chat/ws/${executionId}`

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(wsUrl)
      let isConnected = false

      ws.onopen = () => {
        connecting.value = false
        isConnected = true
        // 不要在这里 resolve，等待 complete 或 error 消息
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage

          if (data.type === 'progress' && options.onProgress) {
            options.onProgress(data)
          } else if (data.type === 'complete' && options.onComplete) {
            options.onComplete(data)
            ws.close()
            resolve()
          } else if (data.type === 'error' && options.onError) {
            options.onError(data)
            ws.close()
            reject(new Error(data.message))
          }
        } catch (err) {
          console.error('[WebSocket] Parse error:', err)
        }
      }

      ws.onerror = (err) => {
        error.value = 'WebSocket 连接错误'
        connecting.value = false
        console.error('[WebSocket] Connection error:', err)
        if (options.onError) {
          options.onError({ type: 'error', message: error.value })
        }
        reject(err)
      }

      ws.onclose = () => {
        connecting.value = false
        if (!isConnected) {
          reject(new Error('WebSocket 连接在建立前就关闭了'))
        }
      }

      // 连接超时检测
      setTimeout(() => {
        if (!isConnected) {
          console.error('[WebSocket] Connection timeout (5s)')
          ws.close()
          reject(new Error('WebSocket 连接超时'))
        }
      }, 5000)
    })
  }

  return {
    connecting,
    error,
    connect
  }
}

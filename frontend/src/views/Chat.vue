<template>
  <div class="page-container">
    <div class="gradient-header">
      <h2>🤖 AI Crew 生成器</h2>
      <p class="subtitle">描述你的需求，AI 将自动为你创建 Crew、Tasks 和 Agents</p>
    </div>

    <div class="chat-container">
      <div class="messages-container" ref="messagesArea">
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="message-avatar">
            <el-icon v-if="msg.role === 'user'" :size="24"><User /></el-icon>
            <el-icon v-else :size="24"><Cpu /></el-icon>
          </div>
          <div class="message-content">
            <div v-if="msg.role === 'assistant' && msg.result" class="result-card">
              <h3>✅ {{ msg.result.topic }}</h3>
              <p class="summary">{{ msg.result.summary }}</p>
              <div class="result-details">
                <el-tag type="success">{{ msg.result.agent_ids.length }} Agents</el-tag>
                <el-tag type="primary">{{ msg.result.task_ids.length }} Tasks</el-tag>
              </div>
              <div class="result-actions">
                <el-button type="primary" size="small" @click="runCrew(msg.result.crew_id)">
                  <el-icon><VideoPlay /></el-icon>立即运行
                </el-button>
                <el-button size="small" @click="viewCrew">查看详情</el-button>
              </div>
            </div>
            <div v-else>{{ msg.text }}</div>
          </div>
        </div>

      </div>

      <div class="input-area">
        <!-- 已选文档标签 -->
        <div v-if="selectedDoc" class="doc-tag">
          <el-icon><Document /></el-icon>
          <span>{{ selectedDoc }}</span>
          <el-button type="danger" link size="small" @click="selectedDoc = ''">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>

        <el-input
          v-model="userInput"
          type="textarea"
          :rows="4"
          placeholder="描述你的项目场景或需求，例如：&#10;&#10;我想开发一个 AI 编程教育平台，需要进行市场调研、产品设计、技术架构规划..."
          @keydown.ctrl.enter="sendMessage"
        />
        <div class="input-actions">
          <el-button type="primary" @click="sendMessage" :disabled="!userInput.trim() || loading">
            <el-icon><Promotion /></el-icon>发送 (Ctrl+Enter)
          </el-button>
          <el-upload
            :show-file-list="false"
            :before-upload="handleDocUpload"
            accept=".md,.txt,.pdf,.docx"
          >
            <el-button>
              <el-icon><UploadFilled /></el-icon>上传文档
            </el-button>
          </el-upload>
          <el-button @click="clearChat" :disabled="messages.length === 0">清空对话</el-button>
        </div>
      </div>
    </div>

    <RunCrewDialog v-model="showRunDialog" :crew="selectedCrew" @executed="onExecuted" />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { UploadFilled, Close } from '@element-plus/icons-vue'
import { api } from '@/api'
import type { Crew } from '@/api'
import RunCrewDialog from '@/components/crews/RunCrewDialog.vue'
import { useSSEStream } from '@/composables/useSSEStream'

const router = useRouter()
const { connect } = useSSEStream()

interface Message {
  role: 'user' | 'assistant'
  text: string
  result?: {
    topic: string
    crew_id: string
    agent_ids: string[]
    task_ids: string[]
    summary: string
  }
}

const messages = ref<Message[]>([])
const userInput = ref('')
const loading = ref(false)
const messagesArea = ref<HTMLElement>()
const selectedDoc = ref('')

const handleDocUpload = async (file: File) => {
  try {
    ElMessage.info('上传中...')
    const result = await api.files.uploadDoc(file)
    selectedDoc.value = result.filename
    ElMessage.success(`文档已上传：${result.filename}`)
  } catch (e: any) {
    ElMessage.error(`上传失败：${e.message}`)
  }
  return false // 阻止 el-upload 默认上传行为
}

const showRunDialog = ref(false)
const selectedCrew = ref<Crew | null>(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesArea.value) {
      messagesArea.value.scrollTop = messagesArea.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  const userMessage = userInput.value.trim()
  messages.value.push({ role: 'user', text: userMessage })
  userInput.value = ''
  scrollToBottom()

  const logMessage = {
    role: 'assistant' as const,
    text: '🤖 后台正在生成 Crew，请稍候...\n\n',
    isGenerating: true
  }
  messages.value.push(logMessage)
  scrollToBottom()

  ElMessage.info({ message: '已提交生成任务，正在后台处理...', duration: 3000 })

  loading.value = true
  try {
    await connect(
      '/api/chat/generate-crew-stream',
      {
        scenario: userMessage,
        context: '',
        doc_filename: selectedDoc.value || null
      },
      {
        onMessage: (data) => {
          logMessage.text += `[${data.level}] ${data.message}\n`
          scrollToBottom()
        },
        onComplete: (data) => {
          logMessage.isGenerating = false
          messages.value.pop()
          messages.value.push({
            role: 'assistant',
            text: '',
            result: data.result
          })
          ElNotification.success({
            title: '✅ Crew 创建成功',
            message: data.result.summary,
            duration: 5000,
            position: 'top-right'
          })
          scrollToBottom()
        },
        onError: (data) => {
          logMessage.isGenerating = false
          logMessage.text += `\n❌ 错误：${data.message}`
          ElNotification.error({
            title: '❌ 生成失败',
            message: data.message,
            duration: 5000,
            position: 'top-right'
          })
          scrollToBottom()
        }
      }
    )
  } catch (error) {
    // Error already handled in composable
  } finally {
    loading.value = false
  }
}

const clearChat = () => {
  messages.value = []
  userInput.value = ''
}

const runCrew = async (crewId: string) => {
  try {
    const crew = await api.crews.get(crewId)
    selectedCrew.value = crew
    showRunDialog.value = true
  } catch {
    ElMessage.error('加载 Crew 失败')
  }
}

const viewCrew = () => {
  router.push('/crews')
}

const onExecuted = () => {
  ElMessage.success('执行已启动，可前往执行历史查看进度')
  router.push('/executions')
}

onMounted(() => {
  messages.value.push({
    role: 'assistant',
    text: '你好！我是 AI Crew 生成助手。请描述你的项目需求或场景，我会为你自动创建合适的 Crew、Tasks 和 Agents。',
  })
})
</script>

<style scoped>
/* Chat 特有样式 */

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.message-content {
  white-space: pre-wrap;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  max-height: 600px;
  overflow-y: auto;
}

.message.user .message-content {
  font-family: inherit;
  font-size: 14px;
}

.result-card {
  padding: 8px 0;
}

.result-card h3 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 18px;
}

.summary {
  color: #606266;
  margin: 0 0 16px 0;
}

.result-details {
  margin-bottom: 16px;
}

.result-details .el-tag {
  margin-right: 8px;
}

.result-actions {
  display: flex;
  gap: 8px;
}


.doc-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  margin-bottom: 8px;
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 13px;
  color: #409eff;
}


.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

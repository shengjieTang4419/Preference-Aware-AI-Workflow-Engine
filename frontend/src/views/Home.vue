<template>
  <div class="creative-workshop">
    <!-- Hero 区域 -->
    <div class="hero-section">
      <h1 class="hero-title">🎨 创意工坊</h1>
      <p class="hero-subtitle">一个想法，无限可能</p>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <!-- 已选文件标签 -->
          <div v-if="uploadedFiles.length > 0" class="file-tags-container">
            <div v-for="(file, index) in uploadedFiles" :key="index" class="file-tag">
              <el-icon><Document /></el-icon>
              <span>{{ file.name }}</span>
              <el-button type="danger" link size="small" @click="removeFile(index)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="input-row">
            <el-input
              v-model="inputText"
              :placeholder="selectedScene ? (selectedScene.placeholder || `描述你的${selectedScene.title}需求...`) : '选择场景后输入想法...'"
              size="large"
              class="main-input"
              @keyup.enter="handleCreate"
            >
              <template #prefix>
                <el-icon size="18"><Edit /></el-icon>
              </template>
            </el-input>
            <el-upload
              :show-file-list="false"
              :before-upload="handleFileUpload"
              accept=".csv,.xlsx,.docx,.pdf,.txt,.md"
            >
              <el-button size="large" class="upload-btn" :icon="Paperclip">📎</el-button>
            </el-upload>
            <el-button type="primary" size="large" class="create-btn" :loading="creating" @click="handleCreate">
              开始创造
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 热门场景 -->
    <div class="section">
      <h2 class="section-title">🔥 热门场景</h2>
      <template v-if="scenes.length > 0">
        <el-row :gutter="16" class="scene-grid">
          <el-col
            v-for="scene in scenes"
            :key="scene.id"
            :xs="12" :sm="8" :md="6"
          >
            <div
              class="scene-card"
              :class="{ active: selectedScene?.id === scene.id }"
              @click="selectScene(scene)"
            >
              <div class="scene-icon">{{ scene.icon }}</div>
              <div class="scene-title">{{ scene.title }}</div>
              <div class="scene-subtitle">{{ scene.subtitle }}</div>
              <div class="scene-badges">
                <el-tag
                  v-if="scene.price_tier"
                  :type="getPriceTierType(scene.price_tier)"
                  size="small"
                  class="badge-tag"
                >
                  {{ getPriceTierLabel(scene.price_tier) }}
                </el-tag>
                <el-tag
                  v-if="scene.exec_mode"
                  :type="scene.exec_mode === 'auto' ? 'success' : 'warning'"
                  size="small"
                  class="badge-tag"
                >
                  {{ scene.exec_mode === 'auto' ? '自动' : '人工审核' }}
                </el-tag>
              </div>
              <div class="scene-tags">
                <el-tag
                  v-for="tag in scene.tags.slice(0, 2)"
                  :key="tag"
                  size="small"
                  :type="getTagType(tag)"
                  class="scene-tag"
                >{{ tag }}</el-tag>
              </div>
            </div>
          </el-col>
        </el-row>
      </template>
      <div v-else class="no-scenes-tip">
        <el-empty description="暂无可用场景">
          <el-button type="primary" @click="$router.push('/market')">前往模版市场安装</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 我的创作 -->
    <div class="section" v-if="recentCreations.length > 0">
      <h2 class="section-title">📋 我的创作</h2>
      <div class="creations-list">
        <div
          v-for="creation in recentCreations"
          :key="creation.id"
          class="creation-item"
        >
          <span class="creation-icon">{{ creation.scene_icon || '✨' }}</span>
          <div class="creation-info">
            <div class="creation-title">{{ creation.scene_title || '创意任务' }}</div>
            <div class="creation-text">{{ creation.input_text }}</div>
          </div>
          <div class="creation-meta">
            <el-tag :type="getStatusType(creation.status)" size="small">
              {{ getStatusText(creation.status) }}
            </el-tag>
            <span class="creation-time">{{ formatTime(creation.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Close, Document } from '@element-plus/icons-vue'
import { api } from '@/api'
import type { SceneConfig, Creation } from '@/api'

const route = useRoute()
const router = useRouter()
const scenes = ref<SceneConfig[]>([])
const recentCreations = ref<Creation[]>([])
const selectedScene = ref<SceneConfig | null>(null)
const inputText = ref('')
const creating = ref(false)
const uploadedFiles = ref<Array<{ name: string; path: string }>>([])
const installedScenes = ref<string[]>([])

onMounted(async () => {
  try {
    const [configList, creationList, installed] = await Promise.all([
      api.sceneConfigs.list(),
      api.creations.list().catch(() => []),
      api.membership.installedScenes().catch(() => []),
    ])
    installedScenes.value = installed
    scenes.value = configList
      .filter(s => s.enabled && s.visible !== false && installed.includes(s.id))
      .sort((a, b) => a.sort_order - b.sort_order)
    recentCreations.value = (creationList as Creation[]).slice(0, 3)

    // 从模版市场跳转过来时，自动选中指定场景
    const sceneQuery = route.query.scene as string
    if (sceneQuery) {
      const found = scenes.value.find(s => s.id === sceneQuery)
      if (found) selectedScene.value = found
    }
  } catch (err) {
    console.error('加载场景失败:', err)
  }
})

function selectScene(scene: SceneConfig) {
  selectedScene.value = scene
}

const handleFileUpload = async (file: File) => {
  try {
    ElMessage.info('上传中...')
    const result = await api.files.uploadDoc(file)
    uploadedFiles.value.push({ name: result.filename, path: result.path })
    ElMessage.success(`文件已上传：${result.filename}`)
  } catch (e: any) {
    ElMessage.error(`上传失败：${e.message}`)
  }
  return false // 阻止 el-upload 默认上传行为
}

function removeFile(index: number) {
  uploadedFiles.value.splice(index, 1)
}

async function handleCreate() {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入你的想法')
    return
  }
  // 如果没有选择场景，用第一个默认场景
  const sceneId = selectedScene.value?.id || scenes.value[0]?.id
  if (!sceneId) {
    ElMessage.warning('暂无可用场景')
    return
  }
  creating.value = true
  try {
    const result = await api.creativity.execute({
      scene_id: sceneId,
      input_text: inputText.value.trim(),
      input_files: uploadedFiles.value.length > 0 ? uploadedFiles.value.map(f => f.path) : undefined,
    })
    ElMessage.success('创作任务已提交！正在跳转...')
    inputText.value = ''
    selectedScene.value = null
    uploadedFiles.value = []
    // 跳转到执行流程页面
    if (result.execution_id) {
      router.push(`/flow/${result.execution_id}`)
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '提交失败，请重试')
  } finally {
    creating.value = false
  }
}

function getPriceTierType(tier: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    free: 'success',
    basic: '',
    premium: 'warning',
  }
  return map[tier] || 'info'
}

function getPriceTierLabel(tier: string) {
  const map: Record<string, string> = {
    free: '免费',
    basic: '基础',
    premium: '高级',
  }
  return map[tier] || tier
}

function getTagType(tag: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    '热门': 'danger',
    '推荐': 'success',
    '新上线': '',
    '即将上线': 'info',
  }
  return map[tag] || 'info'
}

function getStatusType(status: string) {
  const map: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    success: 'success',
    running: 'warning',
    pending: 'info',
    failed: 'danger',
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    success: '已完成',
    running: '进行中',
    pending: '等待中',
    failed: '失败',
  }
  return map[status] || status
}

function formatTime(time: string) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}
</script>

<style scoped>
.creative-workshop {
  max-width: 960px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  padding: 40px 20px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  margin-bottom: 30px;
  color: #fff;
}

.hero-title {
  font-size: 32px;
  margin: 0 0 8px;
  font-weight: 700;
}

.hero-subtitle {
  font-size: 16px;
  opacity: 0.85;
  margin: 0 0 24px;
}

.input-area {
  max-width: 640px;
  margin: 0 auto;
}

.input-wrapper {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 12px;
}

.file-tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.file-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 4px;
  font-size: 13px;
  color: #303133;
}

.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.main-input {
  flex: 1;
}

.main-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 4px 12px;
  font-size: 15px;
}

.upload-btn {
  border-radius: 8px;
  font-size: 16px;
  padding: 0 12px;
}

.create-btn {
  border-radius: 8px;
  font-size: 15px;
  padding: 0 24px;
  font-weight: 600;
}

.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px;
}

.scene-grid {
  display: flex;
  flex-wrap: wrap;
}

.scene-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 2px solid transparent;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.scene-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
}

.scene-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
}

.scene-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.scene-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.scene-subtitle {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.scene-badges {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 8px;
}

.badge-tag {
  font-size: 11px;
}

.scene-tags {
  display: flex;
  justify-content: center;
  gap: 6px;
}

.scene-tag {
  font-size: 11px;
}

.creations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.creation-item {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.creation-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.creation-info {
  flex: 1;
  min-width: 0;
}

.creation-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.creation-text {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.creation-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.creation-time {
  font-size: 12px;
  color: #c0c4cc;
}
</style>

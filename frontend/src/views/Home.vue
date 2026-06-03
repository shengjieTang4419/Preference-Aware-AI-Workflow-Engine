<template>
  <div class="creative-workshop">
    <!-- Hero 区域 -->
    <HeroSection
      v-model:inputText="inputText"
      v-model:uploadedFiles="uploadedFiles"
      v-model:uploadedImages="uploadedImages"
      :selectedScene="selectedScene"
      :creating="creating"
      @create="handleCreate"
    />

    <!-- 热门场景 -->
    <SceneGrid
      :scenes="scenes"
      :selectedScene="selectedScene"
      @select="selectScene"
    />

    <!-- 我的创作 -->
    <CreationsList :creations="recentCreations" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { SceneConfig, Creation } from '@/api'
import HeroSection from '@/components/home/HeroSection.vue'
import SceneGrid from '@/components/home/SceneGrid.vue'
import CreationsList from '@/components/home/CreationsList.vue'
import type { UploadedFile, UploadedImage } from '@/components/home/FileUploader.vue'

const route = useRoute()
const router = useRouter()
const scenes = ref<SceneConfig[]>([])
const recentCreations = ref<Creation[]>([])
const selectedScene = ref<SceneConfig | null>(null)
const inputText = ref('')
const creating = ref(false)
const uploadedFiles = ref<UploadedFile[]>([])
const uploadedImages = ref<UploadedImage[]>([])
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

async function handleCreate() {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入你的想法')
    return
  }
  const sceneId = selectedScene.value?.id || scenes.value[0]?.id
  if (!sceneId) {
    ElMessage.warning('暂无可用场景')
    return
  }
  creating.value = true
  try {
    const ocrTexts = uploadedImages.value.map(img => img.ocrText).filter(t => t.trim())

    // 直接走 Crew Pipeline（Pipeline 第 8 步会根据 scene_config 自动执行 artifact skills）
    const scene = scenes.value.find(s => s.id === sceneId)
    const scenario = scene ? `[${scene.title}] ${inputText.value.trim()}` : inputText.value.trim()
    const result = await api.chat.generateCrew(scenario, sceneId, uploadedFiles.value.map(f => f.name), ocrTexts)

    ElMessage.success('任务已提交！正在跳转...')
    inputText.value = ''
    selectedScene.value = null
    uploadedFiles.value = []
    uploadedImages.value = []

    if (result.execution_id) {
      router.push(`/pipeline/${result.execution_id}`)
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '提交失败，请重试')
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
.creative-workshop {
  max-width: 960px;
  margin: 0 auto;
}
</style>

<template>
  <div class="hero-section">
    <h1 class="hero-title">🎨 创意工坊</h1>
    <p class="hero-subtitle">一个想法，无限可能</p>

    <div class="input-area">
      <div class="input-wrapper">
        <FileUploader v-model:files="uploadedFiles" v-model:images="uploadedImages" />

        <div class="input-row">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            :placeholder="selectedScene ? (selectedScene.placeholder || `描述你的${selectedScene.title}需求...`) : '选择场景后输入想法...'"
            size="large"
            class="main-input"
          />
          <el-upload
            :show-file-list="false"
            :before-upload="handleFileUpload"
            accept=".csv,.xlsx,.docx,.pdf,.txt,.md,.jpg,.jpeg,.png,.gif,.bmp,.webp,.svg"
          >
            <el-button size="large" class="upload-btn"><el-icon><Upload /></el-icon></el-button>
          </el-upload>
          <el-button type="primary" size="large" class="create-btn" :loading="creating" @click="$emit('create')">
            开始创造
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { api } from '@/api'
import type { SceneConfig } from '@/api'
import FileUploader from './FileUploader.vue'
import type { UploadedFile, UploadedImage } from './FileUploader.vue'

const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']

const inputText = defineModel<string>('inputText', { default: '' })
const uploadedFiles = defineModel<UploadedFile[]>('uploadedFiles', { default: () => [] })
const uploadedImages = defineModel<UploadedImage[]>('uploadedImages', { default: () => [] })

const props = defineProps<{
  selectedScene: SceneConfig | null
  creating: boolean
}>()

defineEmits<{
  create: []
}>()

function isImageFile(filename: string): boolean {
  const lower = filename.toLowerCase()
  return IMAGE_EXTENSIONS.some(ext => lower.endsWith(ext))
}

const handleFileUpload = async (file: File) => {
  try {
    ElMessage.info('上传中...')
    if (isImageFile(file.name)) {
      // 图片走独立上传接口，后端已自动 OCR
      const result = await api.files.uploadImage(file)
      // 后端 upload-image 已内置 OCR，直接使用返回结果
      const ocrText = result.ocr_text || ''
      const ocrSuccess = result.ocr_success || false
      const imgEntry: UploadedImage = {
        name: result.filename,
        path: result.path,
        ocrText,
        ocrLoading: false,
        ocrDone: true,
      }
      uploadedImages.value.push(imgEntry)
      if (ocrSuccess && ocrText.trim()) {
        ElMessage.success(`图片已上传，识别到 ${ocrText.length} 字`)
      } else if (ocrSuccess) {
        ElMessage.warning('图片已上传，未识别到文字')
      } else {
        ElMessage.info('图片已上传（OCR 未启用）')
      }
    } else {
      // 文档走原接口
      const result = await api.files.uploadDoc(file)
      uploadedFiles.value.push({ name: result.filename, path: result.path })
      ElMessage.success(`文档已上传：${result.filename}`)
    }
  } catch (e: any) {
    ElMessage.error(`上传失败：${e?.response?.data?.detail || e.message}`)
  }
  return false // 阻止 el-upload 默认上传行为
}
</script>

<style scoped>
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

.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.main-input {
  flex: 1;
}

.main-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 8px 12px;
  font-size: 15px;
  resize: none;
}

.upload-btn {
  border-radius: 8px;
  font-size: 16px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.el-upload) {
  display: inline-block;
  line-height: 1;
}

.create-btn {
  border-radius: 8px;
  font-size: 15px;
  padding: 0 24px;
  font-weight: 600;
}
</style>

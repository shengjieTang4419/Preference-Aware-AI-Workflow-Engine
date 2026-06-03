<template>
  <div class="file-uploader">
    <!-- 已选文件标签 -->
    <div v-if="files.length > 0" class="file-tags-container">
      <div v-for="(file, index) in files" :key="'doc-' + index" class="file-tag">
        <el-icon><Document /></el-icon>
        <span>{{ file.name }}</span>
        <el-button type="danger" link size="small" @click="removeFile(index)">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>
    <!-- 已选图片标签（含 OCR 状态） -->
    <div v-if="images.length > 0" class="file-tags-container">
      <div v-for="(img, index) in images" :key="'img-' + index" class="file-tag image-tag">
        <el-icon><PictureFilled /></el-icon>
        <span class="img-name">{{ img.name }}</span>
        <el-tag v-if="img.ocrLoading" type="warning" size="small">识别中...</el-tag>
        <el-tag v-else-if="img.ocrDone && img.ocrText.trim()" type="success" size="small">
          已识别 {{ img.ocrText.length }} 字
        </el-tag>
        <el-tag v-else-if="img.ocrDone && !img.ocrText.trim()" type="info" size="small">无文字</el-tag>
        <el-button type="danger" link size="small" @click="removeImage(index)">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <!-- OCR 结果预览 -->
      <div v-if="images.some(i => i.ocrDone && i.ocrText)" class="ocr-preview">
        <div class="ocr-preview-title">图片 OCR 识别结果</div>
        <div v-for="(img, idx) in images.filter(i => i.ocrDone && i.ocrText)" :key="idx" class="ocr-item">
          <div class="ocr-item-name">{{ img.name }}</div>
          <pre class="ocr-item-text">{{ img.ocrText }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Close, Document, PictureFilled } from '@element-plus/icons-vue'

export interface UploadedFile {
  name: string
  path: string
}

export interface UploadedImage {
  name: string
  path: string
  ocrText: string
  ocrLoading: boolean
  ocrDone: boolean
}

const files = defineModel<UploadedFile[]>('files', { default: () => [] })
const images = defineModel<UploadedImage[]>('images', { default: () => [] })

function removeFile(index: number) {
  files.value.splice(index, 1)
}

function removeImage(index: number) {
  images.value.splice(index, 1)
}
</script>

<style scoped>
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

.image-tag {
  background: rgba(255, 245, 230, 0.9);
  border: 1px solid #f5c776;
}

.img-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ocr-preview {
  width: 100%;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
  border: 1px solid #e4e7ed;
}

.ocr-preview-title {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.ocr-item {
  margin-bottom: 8px;
}

.ocr-item:last-child {
  margin-bottom: 0;
}

.ocr-item-name {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.ocr-item-text {
  font-size: 12px;
  color: #606266;
  background: #f5f7fa;
  border-radius: 4px;
  padding: 8px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 120px;
  overflow-y: auto;
  margin: 0;
  font-family: inherit;
}
</style>

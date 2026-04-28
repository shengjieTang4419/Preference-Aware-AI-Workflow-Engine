<template>
  <div>
    <div style="margin-bottom: 10px;">
      <el-button size="small" @click="loadFiles" :loading="loading">刷新</el-button>
    </div>
    <div v-loading="loading" style="height: 60vh; display: flex; gap: 15px;">
      <!-- 文件树 -->
      <div style="width: 300px; border-right: 1px solid #dcdfe6; padding-right: 15px; overflow-y: auto;">
        <div style="margin-bottom: 10px; color: #909399; font-size: 12px;">
          输出目录: {{ outputDir }}
        </div>
        <el-tree
          :data="fileTree"
          :props="{ label: 'name', children: 'children' }"
          @node-click="handleFileClick"
          node-key="path"
          highlight-current
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <span class="tree-node-label">
                <el-icon v-if="data.is_dir"><Folder /></el-icon>
                <el-icon v-else><Document /></el-icon>
                {{ node.label }}
              </span>
              <el-button
                v-if="!data.is_dir"
                size="small"
                type="primary"
                link
                class="tree-node-download"
                @click.stop="downloadFile(data.path, data.name)"
              >
                <el-icon><Download /></el-icon>
              </el-button>
            </span>
          </template>
        </el-tree>
      </div>

      <!-- 文件内容 -->
      <div style="flex: 1; overflow-y: auto;">
        <div v-if="!selectedFile" style="text-align: center; padding: 40px; color: #909399;">
          <el-icon :size="48"><Document /></el-icon>
          <p>点击左侧文件查看内容</p>
        </div>
        <div v-else>
          <div style="margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: bold;">{{ selectedFile.name }}</span>
            <el-button
              size="small"
              type="primary"
              @click="downloadFile(selectedFile.path, selectedFile.name)"
            >
              <el-icon><Download /></el-icon> 下载
            </el-button>
          </div>
          <MarkdownViewer v-if="isMarkdown(selectedFile.name)" :content="fileContent" />
          <pre
            v-else
            style="background: #f5f7fa; padding: 15px; border-radius: 4px; font-size: 12px; line-height: 1.5; white-space: pre-wrap;"
          >{{ fileContent }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { api } from '@/api'
import MarkdownViewer from '@/components/common/MarkdownViewer.vue'

const props = defineProps<{
  executionId: string
  outputDir: string
}>()

const downloadFile = (filePath: string, filename: string) => {
  const url = api.executions.getFileDownloadUrl(props.executionId, filePath)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
}

const loading = ref(false)
const fileTree = ref<any[]>([])
const selectedFile = ref<any>(null)
const fileContent = ref('')

const isMarkdown = (filename: string) => filename.toLowerCase().endsWith('.md')

const buildFileTree = (files: any[]) => {
  const tree: any[] = []
  const map: Record<string, any> = {}

  files.forEach((file: any) => {
    const parts = file.path.split('/')
    let current = tree
    let path = ''

    parts.forEach((part: string, index: number) => {
      path = path ? `${path}/${part}` : part

      if (!map[path]) {
        const node = {
          name: part,
          path: file.path,
          is_dir: index < parts.length - 1 || file.is_dir,
          children: [],
        }
        map[path] = node
        current.push(node)
        current = node.children
      } else {
        current = map[path].children
      }
    })
  })

  return tree
}

const loadFiles = async () => {
  if (!props.executionId) return
  loading.value = true
  try {
    const result: any = await api.executions.getFiles(props.executionId)
    fileTree.value = buildFileTree(result.files || [])
    selectedFile.value = null
    fileContent.value = ''
  } catch (error) {
    console.error('加载文件失败', error)
  } finally {
    loading.value = false
  }
}

const handleFileClick = async (data: any) => {
  if (data.is_dir) return
  selectedFile.value = data
  try {
    const result: any = await api.executions.getFileContent(props.executionId, data.path)
    fileContent.value = result.content || ''
  } catch {
    ElMessage.error('读取文件失败')
  }
}

watch(
  () => props.executionId,
  (id) => {
    if (id) loadFiles()
  },
  { immediate: true },
)

defineExpose({ refresh: loadFiles })
</script>

<style scoped>
.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}
.tree-node-label {
  display: flex;
  align-items: center;
  gap: 4px;
}
.tree-node-download {
  opacity: 0;
  transition: opacity 0.2s;
  margin-left: 4px;
}
.el-tree-node__content:hover .tree-node-download {
  opacity: 1;
}
</style>

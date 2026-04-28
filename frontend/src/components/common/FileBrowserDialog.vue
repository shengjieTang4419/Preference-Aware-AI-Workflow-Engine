<template>
  <el-dialog v-model="visible" title="选择输出目录" width="700px">
    <div v-loading="loading">
      <div style="margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
        <el-tag>当前路径:</el-tag>
        <span style="flex: 1; font-family: monospace;">{{ currentPath }}</span>
        <el-button v-if="parentPath" size="small" @click="browsePath(parentPath!)">
          <el-icon><Top /></el-icon>上级目录
        </el-button>
      </div>

      <div v-if="directories.length === 0" style="text-align: center; padding: 40px; color: #909399;">
        <el-icon :size="48"><Folder /></el-icon>
        <p>当前目录为空</p>
      </div>
      <el-table
        v-else
        :data="directories"
        @row-click="handleDirClick"
        style="cursor: pointer;"
        highlight-current-row
      >
        <el-table-column label="目录名称" prop="name">
          <template #default="{ row }">
            <el-icon style="margin-right: 8px;"><Folder /></el-icon>
            <span>{{ row.name }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="selectCurrentPath">选择此目录</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'select': [path: string]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const loading = ref(false)
const currentPath = ref('')
const parentPath = ref<string | null>(null)
const directories = ref<any[]>([])
const allowedRoots = ref<string[]>([])

const loadRoots = async () => {
  try {
    const result = await api.files.getRoots()
    if (result.roots && result.roots.length > 0) {
      allowedRoots.value = result.roots.map((r) => r.path)
      await browsePath(result.roots[0].path)
    }
  } catch {
    ElMessage.error('加载目录根失败')
  }
}

const browsePath = async (path: string) => {
  loading.value = true
  try {
    const result = await api.files.browse(path)
    currentPath.value = result.current
    if (result.parent) {
      const isAllowed = allowedRoots.value.some(
        (root) => result.parent === root || result.parent?.startsWith(root + '/'),
      )
      parentPath.value = isAllowed ? result.parent : null
    } else {
      parentPath.value = null
    }
    directories.value = result.directories
  } catch (error) {
    ElMessage.error('浏览目录失败: ' + (error as any).message)
  } finally {
    loading.value = false
  }
}

const handleDirClick = (row: any) => {
  browsePath(row.path)
}

const selectCurrentPath = () => {
  emit('select', currentPath.value)
  visible.value = false
  ElMessage.success('已选择目录')
}

watch(
  () => props.modelValue,
  (val) => {
    if (val && allowedRoots.value.length === 0) {
      loadRoots()
    }
  },
)
</script>

<template>
  <el-dialog v-model="visible" :title="`运行 Crew: ${crew?.name}`" width="600px">
    <el-form :model="runForm" label-width="120px">
      <el-alert
        v-if="placeholders.length === 0"
        title="此 Crew 没有占位符"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <div v-if="placeholders.length > 0">
        <el-alert
          title="请填写占位符"
          description="这些占位符会替换 Agent 和 Task 配置中的 {变量名}"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />
        <el-form-item
          v-for="placeholder in placeholders"
          :key="placeholder"
          :label="placeholder"
        >
          <el-input
            v-model="runForm.inputs[placeholder]"
            type="textarea"
            :rows="3"
            :placeholder="`请输入 ${placeholder}（支持多行）`"
          />
        </el-form-item>
      </div>

      <el-form-item label="输出目录">
        <el-input v-model="runForm.output_dir" placeholder="留空则自动生成" readonly>
          <template #append>
            <el-button @click="showFileBrowser = true">
              <el-icon><Folder /></el-icon>浏览
            </el-button>
          </template>
        </el-input>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="executeRun" :loading="executing">开始执行</el-button>
    </template>
  </el-dialog>

  <FileBrowserDialog v-model="showFileBrowser" @select="onPathSelected" />
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { Crew, Execution } from '@/api'
import FileBrowserDialog from '@/components/common/FileBrowserDialog.vue'

const props = defineProps<{
  modelValue: boolean
  crew: Crew | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'executed': [execution: Execution]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const placeholders = ref<string[]>([])
const executing = ref(false)
const showFileBrowser = ref(false)
const runForm = ref({
  inputs: {} as Record<string, string>,
  output_dir: '',
})

const loadPlaceholders = async () => {
  if (!props.crew) return
  try {
    placeholders.value = await api.crews.getPlaceholders(props.crew.id)
    runForm.value = { inputs: {}, output_dir: '' }
    placeholders.value.forEach((p) => {
      runForm.value.inputs[p] = ''
    })
  } catch {
    ElMessage.error('加载占位符失败')
  }
}

const executeRun = async () => {
  if (!props.crew) return
  for (const p of placeholders.value) {
    if (!runForm.value.inputs[p]) {
      ElMessage.warning(`请填写 ${p}`)
      return
    }
  }
  executing.value = true
  try {
    const requirement =
      placeholders.value.length > 0 ? runForm.value.inputs[placeholders.value[0]] : '执行任务'
    const output_dir =
      runForm.value.output_dir || `outputs/${requirement.substring(0, 20)}_${new Date().getTime()}`
    const execution = await api.executions.create({
      crew_id: props.crew.id,
      requirement,
      output_dir,
      inputs: runForm.value.inputs,
    })
    ElMessage.success('执行已启动！')
    visible.value = false
    emit('executed', execution)
  } catch {
    ElMessage.error('启动执行失败')
  } finally {
    executing.value = false
  }
}

const onPathSelected = (path: string) => {
  runForm.value.output_dir = path
}

watch(
  () => props.modelValue,
  (val) => {
    if (val && props.crew) {
      loadPlaceholders()
    }
  },
)
</script>

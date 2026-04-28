<template>
  <el-dialog
    v-model="visible"
    :title="`执行详情 - ${execution?.id}`"
    width="80%"
    top="5vh"
  >
    <el-tabs v-model="activeTab">
      <el-tab-pane label="执行日志" name="logs">
        <LogsPanel v-if="execution" :execution-id="execution.id" />
      </el-tab-pane>
      <el-tab-pane label="输出文件" name="files">
        <FileExplorer
          v-if="execution"
          :execution-id="execution.id"
          :output-dir="execution.output_dir"
        />
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Execution } from '@/api'
import LogsPanel from '@/components/executions/LogsPanel.vue'
import FileExplorer from '@/components/executions/FileExplorer.vue'

const props = defineProps<{
  modelValue: boolean
  execution: Execution | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})

const activeTab = ref('logs')

watch(
  () => props.execution,
  () => {
    activeTab.value = 'logs'
  },
)
</script>

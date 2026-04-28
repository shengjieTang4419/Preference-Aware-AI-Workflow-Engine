<template>
  <div class="executions-page">
    <div class="page-header">
      <h2>执行历史</h2>
    </div>

    <el-timeline>
      <el-timeline-item
        v-for="exec in executions"
        :key="exec.id"
        :type="getStatusType(exec.status)"
        :timestamp="formatDate(exec.created_at)"
        placement="top"
      >
        <el-card>
          <h4>Crew: {{ exec.crew_id }}</h4>
          <p>需求: {{ exec.requirement }}</p>
          <p>状态: <el-tag :type="getStatusType(exec.status)">{{ exec.status }}</el-tag></p>
          <p v-if="exec.output_dir">输出目录: {{ exec.output_dir }}</p>
          <div class="exec-actions">
            <el-button size="small" @click="viewDetails(exec)">查看详情</el-button>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>

    <ExecutionDetailDialog v-model="showDetails" :execution="currentExec" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { Execution } from '@/api'
import ExecutionDetailDialog from '@/components/executions/ExecutionDetailDialog.vue'

const executions = ref<Execution[]>([])
const showDetails = ref(false)
const currentExec = ref<Execution | null>(null)

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    completed: 'success',
  }
  return map[status] || 'info'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const loadExecutions = async () => {
  try {
    executions.value = await api.executions.list()
  } catch {
    ElMessage.error('加载失败')
  }
}

const viewDetails = (exec: Execution) => {
  currentExec.value = exec
  showDetails.value = true
}

onMounted(loadExecutions)
</script>

<style scoped>
/* Executions 特有样式 */

.exec-actions {
  margin-top: 15px;
}
</style>

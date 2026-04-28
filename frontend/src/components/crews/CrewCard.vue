<template>
  <el-card class="crew-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span>{{ crew.name }}</span>
        <el-tag size="small">{{ crew.process_type }}</el-tag>
      </div>
    </template>
    <p class="crew-desc">{{ crew.description }}</p>
    <div class="crew-stats">
      <el-tag size="small" type="info">{{ crew.agent_ids?.length || 0 }} Agents</el-tag>
      <el-tag size="small" type="info">{{ crew.task_ids?.length || 0 }} Tasks</el-tag>
    </div>
    <div class="crew-actions">
      <el-button type="primary" size="small" @click="emit('run', crew)">
        <el-icon><VideoPlay /></el-icon>运行
      </el-button>
      <el-button size="small" @click="emit('edit', crew)">编辑</el-button>
      <el-button type="danger" size="small" @click="emit('delete', crew.id)">删除</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { Crew } from '@/api'

const props = defineProps<{
  crew: Crew
}>()

const emit = defineEmits<{
  run: [crew: Crew]
  edit: [crew: Crew]
  delete: [id: string]
}>()
</script>

<style scoped>
.crew-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.crew-desc {
  color: #606266;
  margin-bottom: 15px;
  min-height: 40px;
}

.crew-stats {
  margin-bottom: 15px;
}

.crew-stats .el-tag {
  margin-right: 8px;
}

.crew-actions {
  display: flex;
  gap: 8px;
}
</style>

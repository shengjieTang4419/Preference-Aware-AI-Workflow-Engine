<template>
  <div class="home">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <span>🚀 欢迎使用 CrewAI Web</span>
        </div>
      </template>
      <p>一人公司智能助手 —— 多 Agent 协作编排平台</p>
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="Agents" :value="stats.agents" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="Tasks" :value="stats.tasks" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="Crews" :value="stats.crews" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="Executions" :value="stats.executions" />
        </el-col>
      </el-row>
    </el-card>

    <el-row :gutter="20" class="action-row">
      <el-col :span="12">
        <el-card>
          <template #header>快速开始</template>
          <el-button type="primary" @click="$router.push('/agents')">
            管理 Agents
          </el-button>
          <el-button @click="$router.push('/crews')">
            配置 Crew
          </el-button>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>系统状态</template>
          <el-tag :type="healthStatus.type">{{ healthStatus.text }}</el-tag>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'

const stats = ref({
  agents: 0,
  tasks: 0,
  crews: 0,
  executions: 0,
})

const healthStatus = ref<{ type: 'success' | 'info' | 'warning' | 'danger', text: string }>({ 
  type: 'info', 
  text: '检查中...' 
})

onMounted(async () => {
  try {
    const health: any = await api.health.check()
    healthStatus.value = { type: 'success', text: `运行正常 (${health.version || 'v1.0'})` }
    
    // 并行获取统计数据
    const [agents, tasks, crews, executions] = await Promise.all([
      api.agents.list(),
      api.tasks.list(),
      api.crews.list(),
      api.executions.list(),
    ])
    
    stats.value = {
      agents: agents.length,
      tasks: tasks.length,
      crews: crews.length,
      executions: executions.length,
    }
  } catch (error) {
    healthStatus.value = { type: 'danger', text: '后端服务未启动' }
  }
})
</script>

<style scoped>
.welcome-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.stats-row {
  margin-top: 20px;
}

.action-row {
  margin-top: 20px;
}
</style>

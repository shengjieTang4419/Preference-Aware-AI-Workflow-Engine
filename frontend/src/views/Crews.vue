<template>
  <div class="crews-page">
    <div class="page-header">
      <h2>Crew 配置</h2>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新建 Crew
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8" v-for="crew in crews" :key="crew.id">
        <CrewCard :crew="crew" @run="openRun" @edit="openEdit" @delete="deleteCrew" />
      </el-col>
    </el-row>

    <CrewFormDialog
      v-model="showForm"
      :crew="editingCrew"
      :agents="agents"
      :tasks="tasks"
      @saved="loadCrews"
    />

    <RunCrewDialog v-model="showRun" :crew="runningCrew" @executed="onExecuted" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import type { Crew, Agent, Task, Execution } from '@/api'
import CrewCard from '@/components/crews/CrewCard.vue'
import CrewFormDialog from '@/components/crews/CrewFormDialog.vue'
import RunCrewDialog from '@/components/crews/RunCrewDialog.vue'

const crews = ref<Crew[]>([])
const agents = ref<Agent[]>([])
const tasks = ref<Task[]>([])

const showForm = ref(false)
const editingCrew = ref<Crew | null>(null)

const showRun = ref(false)
const runningCrew = ref<Crew | null>(null)

const loadCrews = async () => {
  try {
    crews.value = await api.crews.list()
  } catch {
    ElMessage.error('加载失败')
  }
}

const loadAgents = async () => {
  try {
    agents.value = await api.agents.list()
  } catch {
    ElMessage.error('加载 Agent 列表失败')
  }
}

const loadTasks = async () => {
  try {
    tasks.value = await api.tasks.list()
  } catch {
    ElMessage.error('加载 Task 列表失败')
  }
}

const openCreate = () => {
  editingCrew.value = null
  showForm.value = true
}

const openEdit = (crew: Crew) => {
  editingCrew.value = crew
  showForm.value = true
}

const openRun = (crew: Crew) => {
  runningCrew.value = crew
  showRun.value = true
}

const deleteCrew = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除该 Crew？', '提示', { type: 'warning' })
    await api.crews.delete(id)
    ElMessage.success('删除成功')
    loadCrews()
  } catch {
    // 取消
  }
}

const onExecuted = (execution: Execution) => {
  console.log('Execution created:', execution)
}

onMounted(() => {
  loadCrews()
  loadAgents()
  loadTasks()
})
</script>

<style scoped>
/* Crews 特有样式 */
</style>

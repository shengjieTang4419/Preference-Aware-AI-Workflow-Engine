<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2>Task 管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建 Task
      </el-button>
    </div>

    <!-- 分组统计卡片 -->
    <div class="stats-cards">
      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-label">总任务数</div>
          <div class="stat-value">{{ tasks.length }}</div>
        </div>
      </el-card>
      <el-card shadow="hover">
        <div class="stat-item">
          <div class="stat-label">项目数</div>
          <div class="stat-value">{{ groupedTasks.length }}</div>
        </div>
      </el-card>
    </div>

    <!-- 按 Topic 分组的表格 -->
    <div v-loading="loading" class="grouped-tables">
      <el-collapse v-model="activeGroups" accordion>
        <el-collapse-item 
          v-for="group in groupedTasks" 
          :key="group.topic" 
          :name="group.topic"
        >
          <template #title>
            <div class="group-header">
              <el-icon class="group-icon"><Folder /></el-icon>
              <span class="group-title">{{ group.topic || '未分组任务' }}</span>
              <el-tag size="small" type="info" style="margin-left: 12px">
                {{ group.tasks.length }} 个任务
              </el-tag>
              <el-tag v-if="group.crew_id" size="small" type="success" style="margin-left: 8px">
                Crew: {{ group.crew_id }}
              </el-tag>
            </div>
          </template>
          
          <el-table :data="group.tasks" style="width: 100%">
            <el-table-column prop="name" label="任务名称" width="200" />
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="role_type" label="角色类型" width="140">
              <template #default="{ row }">
                <el-tag v-if="row.role_type" size="small">{{ row.role_type }}</el-tag>
                <span v-else style="color: #909399">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="agent_id" label="执行 Agent" width="150" />
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="editTask(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="deleteTask(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
      
      <!-- 如果没有任务 -->
      <el-empty v-if="tasks.length === 0 && !loading" description="暂无任务" />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editingId ? '编辑 Task' : '新建 Task'" width="600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="form.name" placeholder="例如：市场调研" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="任务描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="详细描述任务内容和目标" />
        </el-form-item>
        <el-form-item label="执行 Agent">
          <el-select v-model="form.agent_id" placeholder="选择执行该任务的 Agent" style="width: 100%">
            <el-option v-for="agent in agents" :key="agent.id" :label="agent.role" :value="agent.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="期望输出">
          <el-input v-model="form.expected_output" type="textarea" :rows="3" placeholder="描述期望的输出格式和内容" />
        </el-form-item>
        <el-form-item label="前置任务">
          <el-select v-model="form.context_task_ids" multiple placeholder="选择该任务依赖的前置任务（可选）" style="width: 100%">
            <el-option v-for="task in tasks.filter(t => t.id !== editingId)" :key="task.id" :label="task.name" :value="task.id" />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            前置任务的输出会作为上下文传递给当前任务
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTask">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder } from '@element-plus/icons-vue'
import { api } from '@/api'
import type { Task, Agent } from '@/api'

const tasks = ref<Task[]>([])
const agents = ref<Agent[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editingId = ref<string | null>(null)
const activeGroups = ref<string[]>([]) // 当前展开的分组
const form = ref({
  name: '',
  description: '',
  agent_id: '',
  expected_output: '',
  context_task_ids: [] as string[],
})

// 按 topic 分组任务
const groupedTasks = computed(() => {
  const groups = new Map<string, { topic: string; crew_id?: string; tasks: Task[] }>()
  
  tasks.value.forEach(task => {
    const topic = task.topic || '未分组任务'
    if (!groups.has(topic)) {
      groups.set(topic, {
        topic,
        crew_id: task.crew_id,
        tasks: []
      })
    }
    groups.get(topic)!.tasks.push(task)
  })
  
  // 转换为数组并按任务数量排序
  return Array.from(groups.values()).sort((a, b) => b.tasks.length - a.tasks.length)
})

const loadTasks = async () => {
  loading.value = true
  try {
    tasks.value = await api.tasks.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadAgents = async () => {
  try {
    agents.value = await api.agents.list()
  } catch (error) {
    ElMessage.error('加载 Agent 列表失败')
  }
}

const saveTask = async () => {
  if (!form.value.name || !form.value.description || !form.value.agent_id || !form.value.expected_output) {
    ElMessage.warning('请填写所有必填项')
    return
  }
  
  try {
    if (editingId.value) {
      await api.tasks.update(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.tasks.create(form.value)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    loadTasks()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const editTask = (task: Task) => {
  editingId.value = task.id
  form.value = {
    name: task.name,
    description: task.description,
    agent_id: task.agent_id,
    expected_output: task.expected_output,
    context_task_ids: task.context_task_ids || [],
  }
  showCreateDialog.value = true
}

const resetForm = () => {
  editingId.value = null
  form.value = {
    name: '',
    description: '',
    agent_id: '',
    expected_output: '',
    context_task_ids: [],
  }
}

const deleteTask = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除该 Task？', '提示', { type: 'warning' })
    await api.tasks.delete(id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch {
    // 取消
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTasks()
  loadAgents()
})
</script>

<style scoped>
.tasks-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 8px 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

/* 分组表格 */
.grouped-tables {
  min-height: 400px;
}

.group-header {
  display: flex;
  align-items: center;
  flex: 1;
  padding: 4px 0;
}

.group-icon {
  margin-right: 8px;
  font-size: 18px;
  color: #409eff;
}

.group-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

/* 折叠面板样式优化 */
:deep(.el-collapse-item__header) {
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 8px;
}

:deep(.el-collapse-item__header:hover) {
  background-color: #ecf5ff;
}

:deep(.el-collapse-item__wrap) {
  border: none;
  margin-bottom: 16px;
}

:deep(.el-collapse-item__content) {
  padding: 0 16px 16px;
}
</style>

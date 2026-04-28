<template>
  <div class="agents-page">
    <div class="page-header">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建 Agent
      </el-button>
    </div>

    <el-table :data="agents" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="role" label="角色" width="180" />
      <el-table-column prop="goal" label="目标" show-overflow-tooltip />
      <el-table-column prop="backstory" label="背景" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="editAgent(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="deleteAgent(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editingId ? '编辑 Agent' : '新建 Agent'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如：ceo, product_manager" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="角色">
          <el-input v-model="form.role" placeholder="例如：产品经理" />
        </el-form-item>
        <el-form-item label="目标">
          <el-input v-model="form.goal" type="textarea" :rows="3" placeholder="Agent 的核心目标" />
        </el-form-item>
        <el-form-item label="背景故事">
          <el-input v-model="form.backstory" type="textarea" :rows="4" placeholder="Agent 的背景设定" />
        </el-form-item>
        
        <el-divider content-position="left">Skills 配置（可选）</el-divider>
        
        <el-form-item label="AI 推荐">
          <el-button 
            @click="requestAIRecommendation" 
            :loading="aiRecommending"
            :disabled="!form.role || !form.goal"
          >
            让 AI 推荐 Skills
          </el-button>
          <el-text type="info" size="small" style="margin-left: 10px">
            根据角色和目标自动推荐
          </el-text>
        </el-form-item>
        
        <el-form-item label="Skills 模式">
          <el-select v-model="form.skills_config.mode" placeholder="选择模式">
            <el-option label="自动匹配（推荐）" value="auto" />
            <el-option label="手动指定" value="manual" />
            <el-option label="混合模式" value="hybrid" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先 Skills">
          <el-select
            v-model="form.skills_config.preferred"
            multiple
            filterable
            placeholder="选择优先使用的 Skills"
          >
            <el-option
              v-for="skill in availableSkills"
              :key="skill.name"
              :label="skill.name"
              :value="skill.name"
            >
              <span>{{ skill.name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ skill.has_scripts ? '✓ Tools' : 'Skills' }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAgent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import type { Agent, Skill } from '@/api'

const agents = ref<Agent[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editingId = ref<string | null>(null)
const availableSkills = ref<Skill[]>([])
const aiRecommending = ref(false)

const form = ref({
  name: '',
  role: '',
  goal: '',
  backstory: '',
  skills_config: {
    mode: 'auto',
    preferred: [] as string[],
    auto_match: true,
    include_patterns: [] as string[],
    exclude_patterns: [] as string[]
  }
})

const loadAgents = async () => {
  loading.value = true
  try {
    agents.value = await api.agents.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const saveAgent = async () => {
  if (!form.value.name || !form.value.role || !form.value.goal || !form.value.backstory) {
    ElMessage.warning('请填写所有必填项')
    return
  }
  
  try {
    if (editingId.value) {
      await api.agents.update(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.agents.create(form.value)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetForm()
    loadAgents()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const loadSkills = async () => {
  try {
    availableSkills.value = await api.skills.list()
  } catch (error) {
    console.error('Failed to load skills:', error)
  }
}

const requestAIRecommendation = async () => {
  if (!form.value.role || !form.value.goal) {
    ElMessage.warning('请先填写角色和目标')
    return
  }
  
  aiRecommending.value = true
  try {
    const recommendation = await api.skills.aiRecommend({
      role: form.value.role,
      goal: form.value.goal,
      backstory: form.value.backstory,
      task_context: ''
    })
    
    // 应用 AI 推荐的配置
    form.value.skills_config = {
      mode: recommendation.mode || 'auto',
      preferred: recommendation.preferred || [],
      auto_match: recommendation.auto_match !== false,
      include_patterns: recommendation.include_patterns || [],
      exclude_patterns: recommendation.exclude_patterns || []
    }
    
    ElMessage.success(`AI 推荐了 ${recommendation.preferred?.length || 0} 个 Skills`)
  } catch (error: any) {
    ElMessage.error('AI 推荐失败: ' + (error.message || '未知错误'))
  } finally {
    aiRecommending.value = false
  }
}

const editAgent = (agent: Agent) => {
  editingId.value = agent.id
  form.value = {
    name: agent.name,
    role: agent.role,
    goal: agent.goal,
    backstory: agent.backstory,
    skills_config: (agent as any).skills_config || {
      mode: 'auto',
      preferred: [],
      auto_match: true,
      include_patterns: [],
      exclude_patterns: []
    }
  }
  showCreateDialog.value = true
}

const resetForm = () => {
  editingId.value = null
  form.value = {
    name: '',
    role: '',
    goal: '',
    backstory: '',
    skills_config: {
      mode: 'auto',
      preferred: [],
      auto_match: true,
      include_patterns: [],
      exclude_patterns: []
    }
  }
}

const deleteAgent = async (id: string) => {
  try {
    await ElMessageBox.confirm('确定删除该 Agent？', '提示', { type: 'warning' })
    await api.agents.delete(id)
    ElMessage.success('删除成功')
    loadAgents()
  } catch {
    // 用户取消
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadAgents()
  loadSkills()
})
</script>

<style scoped>
/* Agents 特有样式 */
</style>

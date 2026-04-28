<template>
  <el-dialog v-model="visible" :title="crew ? '编辑 Crew' : '新建 Crew'" width="700px">
    <el-form :model="form" label-width="120px">
      <el-form-item label="Crew 名称">
        <el-input v-model="form.name" placeholder="例如：产品开发团队" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述该 Crew 的职责和目标" />
      </el-form-item>
      <el-form-item label="执行流程">
        <el-select v-model="form.process_type" placeholder="选择执行流程" style="width: 100%">
          <el-option label="顺序执行 (Sequential)" value="sequential" />
          <el-option label="层级执行 (Hierarchical)" value="hierarchical" />
        </el-select>
      </el-form-item>
      <el-form-item label="Agents">
        <el-select v-model="form.agent_ids" multiple placeholder="选择参与的 Agents" style="width: 100%">
          <el-option v-for="agent in agents" :key="agent.id" :label="agent.role" :value="agent.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="Tasks">
        <el-select v-model="form.task_ids" multiple placeholder="选择要执行的 Tasks" style="width: 100%">
          <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
        </el-select>
      </el-form-item>
      
      <!-- 模型等级分配 - 使用独立组件 -->
      <el-form-item label="模型分配">
        <ModelAssignment
          v-model="form.agent_model_assignments"
          :agent-ids="form.agent_ids"
          :agents="agents"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { Crew, Agent, Task } from '@/api'
import ModelAssignment from './ModelAssignment.vue'

const props = defineProps<{
  modelValue: boolean
  crew: Crew | null
  agents: Agent[]
  tasks: Task[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const form = ref({
  name: '',
  description: '',
  agent_ids: [] as string[],
  task_ids: [] as string[],
  process_type: 'sequential' as 'sequential' | 'hierarchical',
  agent_model_assignments: {} as Record<string, 'basic' | 'standard' | 'advanced'>,
})

// 监听 agent_ids 变化，自动初始化模型分配（默认 standard）
watch(
  () => form.value.agent_ids,
  (newAgentIds) => {
    // 为新添加的 Agent 设置默认模型等级
    newAgentIds.forEach(agentId => {
      if (!form.value.agent_model_assignments[agentId]) {
        form.value.agent_model_assignments[agentId] = 'standard'
      }
    })
    // 移除已删除的 Agent 的模型分配
    Object.keys(form.value.agent_model_assignments).forEach(agentId => {
      if (!newAgentIds.includes(agentId)) {
        delete form.value.agent_model_assignments[agentId]
      }
    })
  },
  { deep: true }
)

watch(
  () => props.crew,
  (crew) => {
    if (crew) {
      form.value = {
        name: crew.name,
        description: crew.description || '',
        agent_ids: crew.agent_ids || [],
        task_ids: crew.task_ids || [],
        process_type: crew.process_type,
        agent_model_assignments: crew.agent_model_assignments || {},
      }
    } else {
      form.value = {
        name: '',
        description: '',
        agent_ids: [],
        task_ids: [],
        process_type: 'sequential',
        agent_model_assignments: {},
      }
    }
  },
  { immediate: true },
)

const save = async () => {
  if (!form.value.name || !form.value.description) {
    ElMessage.warning('请填写必填项')
    return
  }
  try {
    if (props.crew) {
      await api.crews.update(props.crew.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.crews.create(form.value)
      ElMessage.success('创建成功')
    }
    visible.value = false
    emit('saved')
  } catch {
    ElMessage.error('保存失败')
  }
}
</script>

<template>
  <div class="skills-page">
    <div class="page-header">
      <div class="header-left">
        <h2>🛠️ Skills 管理</h2>
        <p class="subtitle">查看和管理所有可用的 Skills</p>
      </div>
      <div class="header-right">
        <el-statistic title="总 Skills" :value="statistics.total_skills" />
        <el-statistic title="带脚本" :value="statistics.skills_with_scripts" />
      </div>
    </div>

    <el-card class="content-card">
      <el-table
        :data="skills"
        v-loading="loading"
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="name" label="名称" width="200">
          <template #default="{ row }">
            <div class="skill-name">
              <el-icon v-if="row.has_scripts" color="#67C23A"><Tools /></el-icon>
              <el-icon v-else color="#909399"><Document /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="metadata.description" label="描述" min-width="300">
          <template #default="{ row }">
            <span class="description">{{ row.metadata.description }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="metadata.version" label="版本" width="100" />

        <el-table-column prop="metadata.author" label="作者" width="150" />

        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.has_scripts" type="success" size="small">
              Skills + Tools
            </el-tag>
            <el-tag v-else type="info" size="small">
              Skills Only
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click.stop="viewDetail(row.name)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`Skill: ${currentSkill?.name}`"
      width="70%"
      destroy-on-close
    >
      <div v-if="currentSkill" class="skill-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="名称">
            {{ currentSkill.metadata.name }}
          </el-descriptions-item>
          <el-descriptions-item label="版本">
            {{ currentSkill.metadata.version || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="作者">
            {{ currentSkill.metadata.author || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag v-if="currentSkill.has_scripts" type="success">
              Skills + Tools
            </el-tag>
            <el-tag v-else type="info">Skills Only</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentSkill.metadata.description }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="currentSkill.scripts && currentSkill.scripts.length > 0" class="scripts-section">
          <h3>关联的 Tools</h3>
          <el-table :data="currentSkill.scripts" size="small">
            <el-table-column prop="name" label="脚本名称" />
            <el-table-column prop="size" label="大小">
              <template #default="{ row }">
                {{ formatSize(row.size) }}
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="content-section">
          <h3>Skill 内容</h3>
          <el-input
            v-model="currentSkill.content"
            type="textarea"
            :rows="20"
            readonly
            class="content-textarea"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Tools } from '@element-plus/icons-vue'
import { api } from '@/api'
import type { Skill, SkillsStatistics } from '@/api/types'

const loading = ref(false)
const skills = ref<Skill[]>([])
const statistics = ref<SkillsStatistics>({
  total_skills: 0,
  skills_with_scripts: 0,
  skills_by_directory: {}
})

const detailDialogVisible = ref(false)
const currentSkill = ref<Skill | null>(null)

const loadSkills = async () => {
  loading.value = true
  try {
    const [skillsData, statsData] = await Promise.all([
      api.skills.list(),
      api.skills.getStatistics()
    ])
    skills.value = skillsData
    statistics.value = statsData
  } catch (error: any) {
    ElMessage.error('加载 Skills 失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const viewDetail = async (skillName: string) => {
  try {
    currentSkill.value = await api.skills.getDetail(skillName)
    detailDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error('加载 Skill 详情失败: ' + (error.message || '未知错误'))
  }
}

const handleRowClick = (row: Skill) => {
  viewDetail(row.name)
}

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

onMounted(() => {
  loadSkills()
})
</script>

<style scoped>
/* Skills 特有样式 */

.skill-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.description {
  color: #606266;
  font-size: 14px;
}

.skill-detail {
  padding: 10px 0;
}

.scripts-section,
.content-section {
  margin-top: 20px;
}

.scripts-section h3,
.content-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.content-textarea :deep(textarea) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>

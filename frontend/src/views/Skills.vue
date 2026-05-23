<template>
  <div class="skills-page">
    <!-- 顶部渐变 Banner -->
    <div class="page-banner">
      <div class="banner-content">
        <h1>🔧 技能发现与管理</h1>
        <p class="banner-desc">从 skills.sh 发现热门技能，一键安装，AI 自动生成技能说明</p>
        <div class="banner-stats">
          <el-tag type="info" size="large" effect="dark" round>
            🌐 发现 {{ discoverSkills.length }} 个可用技能
          </el-tag>
          <el-tag type="success" size="large" effect="dark" round>
            📦 已安装 {{ installedSkills.length }} 个技能
          </el-tag>
        </div>
      </div>
    </div>

    <!-- Section 1: 热门技能发现 -->
    <div class="section">
      <div class="section-header">
        <h2>🔥 热门技能发现</h2>
        <el-input
          v-model="searchQuery"
          placeholder="搜索技能..."
          clearable
          style="width: 300px"
          @input="debouncedSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div v-loading="discoverLoading" class="skill-grid">
        <el-empty v-if="!discoverLoading && discoverSkills.length === 0" description="暂无发现的技能" />
        <el-card
          v-for="skill in discoverSkills"
          :key="skill.name"
          class="skill-card discover-card"
          shadow="hover"
        >
          <div class="card-header">
            <span class="skill-name">{{ skill.name }}</span>
            <el-tag size="small" type="info">{{ skill.source }}</el-tag>
          </div>
          <p class="skill-desc">{{ skill.description || '暂无描述' }}</p>
          <div class="card-footer">
            <span class="install-count">
              <el-icon><Download /></el-icon>
              {{ skill.installs }} 次安装
            </span>
            <el-button
              v-if="!isInstalled(skill.name)"
              type="primary"
              size="small"
              :loading="installingSkills.has(skill.name)"
              @click="handleInstall(skill)"
            >
              安装
            </el-button>
            <el-button
              v-else
              type="success"
              size="small"
              disabled
            >
              已安装 ✓
            </el-button>
          </div>
        </el-card>
      </div>
    </div>

    <!-- Section 2: 已安装技能 -->
    <div class="section">
      <div class="section-header">
        <h2>📦 已安装技能</h2>
      </div>

      <div v-loading="installedLoading" class="skill-grid">
        <el-empty v-if="!installedLoading && installedSkills.length === 0" description="暂未安装任何技能" />
        <el-card
          v-for="skill in installedSkills"
          :key="skill.name"
          class="skill-card installed-card"
          shadow="hover"
        >
          <div class="card-header">
            <span class="skill-name">{{ skill.name }}</span>
            <el-button
              type="danger"
              size="small"
              plain
              :loading="uninstallingSkills.has(skill.name)"
              @click="handleUninstall(skill)"
            >
              卸载
            </el-button>
          </div>
          <p class="skill-summary">{{ skill.summary }}</p>

          <!-- 详细说明折叠区域 -->
          <el-collapse v-model="expandedSkills" class="detail-collapse">
            <el-collapse-item :name="skill.name">
              <template #title>
                <span class="detail-toggle">📋 详细说明</span>
              </template>
              <div class="detail-content">
                <div v-if="skill.what_it_does" class="detail-block">
                  <h4>🔍 详细说明</h4>
                  <p>{{ skill.what_it_does }}</p>
                </div>
                <div v-if="skill.when_to_use && skill.when_to_use.length" class="detail-block">
                  <h4>🎯 使用场景</h4>
                  <ul>
                    <li v-for="(item, idx) in skill.when_to_use" :key="idx">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="skill.key_features && skill.key_features.length" class="detail-block">
                  <h4>⭐ 核心功能</h4>
                  <ul>
                    <li v-for="(item, idx) in skill.key_features" :key="idx">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="skill.example" class="detail-block">
                  <h4>💡 使用示例</h4>
                  <pre class="example-code">{{ skill.example }}</pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { api } from '@/api'
import type { DiscoverSkill, InstalledSkill } from '@/api/types'

// --- State ---
const searchQuery = ref('')
const discoverLoading = ref(false)
const installedLoading = ref(false)
const discoverSkills = ref<DiscoverSkill[]>([])
const installedSkills = ref<InstalledSkill[]>([])
const installingSkills = ref<Set<string>>(new Set())
const uninstallingSkills = ref<Set<string>>(new Set())
const expandedSkills = ref<string[]>([])

let searchTimer: ReturnType<typeof setTimeout> | null = null

// --- Computed ---
const installedNameSet = computed(() => new Set(installedSkills.value.map(s => s.name)))

const isInstalled = (name: string) => installedNameSet.value.has(name)

// --- Methods ---
const loadDiscover = async (q?: string) => {
  discoverLoading.value = true
  try {
    const result = await api.skillsMarket.discover(q)
    discoverSkills.value = result
  } catch (error: any) {
    console.error('[Skills] discover error:', error)
    ElMessage.error('加载发现技能失败: ' + (error.message || '未知错误'))
  } finally {
    discoverLoading.value = false
  }
}

const loadInstalled = async () => {
  installedLoading.value = true
  try {
    installedSkills.value = await api.skillsMarket.installed()
  } catch (error: any) {
    ElMessage.error('加载已安装技能失败: ' + (error.message || '未知错误'))
  } finally {
    installedLoading.value = false
  }
}

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadDiscover(searchQuery.value)
  }, 300)
}

const handleInstall = async (skill: DiscoverSkill) => {
  installingSkills.value.add(skill.name)
  try {
    await api.skillsMarket.install(skill.name)
    ElMessage.success(`技能 "${skill.name}" 安装成功！`)
    await loadInstalled()
  } catch (error: any) {
    ElMessage.error('安装失败: ' + (error.message || '未知错误'))
  } finally {
    installingSkills.value.delete(skill.name)
  }
}

const handleUninstall = async (skill: InstalledSkill) => {
  try {
    await ElMessageBox.confirm(
      `确定要卸载技能 "${skill.name}" 吗？卸载后将无法使用该技能。`,
      '确认卸载',
      { confirmButtonText: '确认卸载', cancelButtonText: '取消', type: 'warning' }
    )
    uninstallingSkills.value.add(skill.name)
    await api.skillsMarket.uninstall(skill.name)
    ElMessage.success(`技能 "${skill.name}" 已卸载`)
    await loadInstalled()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('卸载失败: ' + (error.message || '未知错误'))
    }
  } finally {
    uninstallingSkills.value.delete(skill.name)
  }
}

// --- Init ---
onMounted(() => {
  loadDiscover()
  loadInstalled()
})
</script>

<style scoped>
.skills-page {
  min-height: 100vh;
  background: #f5f7fa;
}

/* Banner */
.page-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 40px 32px;
  color: #fff;
}

.banner-content h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
}

.banner-desc {
  margin: 0 0 16px;
  font-size: 15px;
  opacity: 0.9;
}

.banner-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Section */
.section {
  padding: 24px 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

/* Grid */
.skill-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  min-height: 100px;
}

@media (max-width: 1200px) {
  .skill-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .skill-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .section {
    padding: 20px 16px;
  }
  .page-banner {
    padding: 24px 16px;
  }
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

/* Cards */
.skill-card {
  transition: transform 0.2s;
}

.skill-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.skill-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
  min-height: 40px;
  margin: 0 0 12px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.skill-summary {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  margin: 0 0 12px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.install-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

/* Installed card collapse */
.detail-collapse {
  border: none;
}

.detail-collapse :deep(.el-collapse-item__header) {
  background: transparent;
  border: none;
  height: 32px;
  line-height: 32px;
  font-size: 14px;
}

.detail-collapse :deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

.detail-toggle {
  color: #409eff;
  font-size: 13px;
}

.detail-content {
  padding: 4px 0;
}

.detail-block {
  margin-bottom: 12px;
}

.detail-block h4 {
  margin: 0 0 6px;
  font-size: 14px;
  color: #303133;
}

.detail-block p {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.detail-block ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.example-code {
  background: #f4f4f5;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  color: #303133;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
</style>

<template>
  <div class="market-page">
    <!-- 顶部 Banner -->
    <div class="market-banner">
      <div class="banner-content">
        <h1>🏪 模版市场</h1>
        <p>浏览、使用、分享创意模版。选择一个模版，快速开始你的创作。</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-radio-group v-model="activeCategory" size="default">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="document">文档</el-radio-button>
        <el-radio-button label="data">数据</el-radio-button>
        <el-radio-button label="code">代码</el-radio-button>
        <el-radio-button label="media">多媒体</el-radio-button>
      </el-radio-group>
      <div class="filter-right">
        <el-tag v-if="activeCategory !== 'all'" closable @close="activeCategory = 'all'">
          {{ categoryLabel }}
        </el-tag>
        <span class="result-count">{{ filteredConfigs.length }} 个模版</span>
      </div>
    </div>

    <!-- 模版卡片网格 -->
    <el-row :gutter="16" class="card-grid">
      <el-col
        v-for="config in filteredConfigs"
        :key="config.id"
        :xs="24" :sm="12" :md="8" :lg="6"
      >
        <el-card class="template-card" shadow="hover" @click="handleUse(config)">
          <!-- 卡片头部：图标 + 标题 -->
          <div class="card-header">
            <span class="card-icon">{{ config.icon }}</span>
            <div class="card-title-group">
              <h3>{{ config.title }}</h3>
              <p>{{ config.subtitle }}</p>
            </div>
          </div>

          <!-- 标签区 -->
          <div class="card-tags">
            <el-tag v-if="config.price_tier === 'free'" type="success" size="small">免费</el-tag>
            <el-tag v-else-if="config.price_tier === 'basic'" type="primary" size="small">基础</el-tag>
            <el-tag v-else type="warning" size="small">高级</el-tag>

            <el-tag v-if="config.exec_mode === 'auto'" type="success" size="small" effect="plain">自动</el-tag>
            <el-tag v-else type="warning" size="small" effect="plain">人工审核</el-tag>

            <el-tag
              v-for="tag in config.tags"
              :key="tag"
              :type="tagType(tag)"
              size="small"
              effect="dark"
            >{{ tag }}</el-tag>
          </div>

          <!-- 输出格式 -->
          <div class="card-meta">
            <span>输出: .{{ config.output_format }}</span>
            <span>{{ categoryName(config.category) }}</span>
          </div>

          <!-- 操作按钮 -->
          <div class="card-actions">
            <template v-if="isInstalled(config.id)">
              <el-tag type="success" size="small" effect="dark">已安装</el-tag>
              <el-button type="primary" size="small" @click.stop="handleUse(config)">
                使用模版
              </el-button>
            </template>
            <template v-else>
              <el-button
                type="warning"
                size="small"
                :loading="installingScene === config.id"
                @click.stop="handleInstall(config)"
              >
                安装
              </el-button>
            </template>
            <el-button size="small" @click.stop="handlePreview(config)">
              详情
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="filteredConfigs.length === 0" description="暂无模版" />

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="selectedConfig?.title" size="400px">
      <template v-if="selectedConfig">
        <div class="drawer-icon">{{ selectedConfig.icon }}</div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="标题">{{ selectedConfig.title }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedConfig.subtitle }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ categoryName(selectedConfig.category) }}</el-descriptions-item>
          <el-descriptions-item label="输出格式">.{{ selectedConfig.output_format }}</el-descriptions-item>
          <el-descriptions-item label="收费层级">
            <el-tag :type="selectedConfig.price_tier === 'free' ? 'success' : selectedConfig.price_tier === 'basic' ? 'primary' : 'warning'">
              {{ priceLabel(selectedConfig.price_tier) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行模式">
            <el-tag :type="selectedConfig.exec_mode === 'auto' ? 'success' : 'warning'">
              {{ selectedConfig.exec_mode === 'auto' ? '自动触达' : '人工审核' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedConfig.output_dir" label="输出目录">
            {{ selectedConfig.output_dir }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedConfig.placeholder" label="输入示例">
            {{ selectedConfig.placeholder }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="drawer-actions">
          <template v-if="isInstalled(selectedConfig.id)">
            <el-button type="primary" size="large" @click="handleUse(selectedConfig)">
              使用此模版
            </el-button>
          </template>
          <template v-else>
            <el-button
              type="warning"
              size="large"
              :loading="installingScene === selectedConfig.id"
              @click="handleInstall(selectedConfig)"
            >
              安装此模版
            </el-button>
          </template>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { SceneConfig } from '@/api/types'

const router = useRouter()

const configs = ref<SceneConfig[]>([])
const activeCategory = ref('all')
const drawerVisible = ref(false)
const selectedConfig = ref<SceneConfig | null>(null)
const installedScenes = ref<string[]>([])
const installingScene = ref<string | null>(null)

const categoryLabel = computed(() => {
  const map: Record<string, string> = {
    document: '文档', data: '数据', code: '代码', media: '多媒体',
  }
  return map[activeCategory.value] || ''
})

const filteredConfigs = computed(() => {
  if (activeCategory.value === 'all') return configs.value
  return configs.value.filter(c => c.category === activeCategory.value)
})

function tagType(tag: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
    '热门': 'danger', '推荐': 'success', '新上线': '', '即将上线': 'info',
  }
  return map[tag] ?? 'info'
}

function categoryName(category: string): string {
  const map: Record<string, string> = {
    document: '文档类', data: '数据类', code: '代码类', media: '多媒体类',
  }
  return map[category] ?? category
}

function priceLabel(tier: string): string {
  const map: Record<string, string> = { free: '免费', basic: '基础版', premium: '高级版' }
  return map[tier] ?? tier
}

function handleUse(config: SceneConfig) {
  // 跳转到创意工坊，并携带选中的场景 ID
  router.push({ path: '/', query: { scene: config.id } })
}

function isInstalled(sceneId: string) {
  return installedScenes.value.includes(sceneId)
}

async function handleInstall(config: SceneConfig) {
  installingScene.value = config.id
  try {
    await api.membership.installScene(config.id)
    installedScenes.value.push(config.id)
    ElMessage.success(`已安装「${config.title}」`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '安装失败，请重试')
  } finally {
    installingScene.value = null
  }
}

function handlePreview(config: SceneConfig) {
  selectedConfig.value = config
  drawerVisible.value = true
}

onMounted(async () => {
  try {
    const [configList, installed] = await Promise.all([
      api.sceneConfigs.list(),
      api.membership.installedScenes().catch(() => []),
    ])
    configs.value = configList
    installedScenes.value = installed
  } catch (e) {
    console.error('加载模版失败:', e)
  }
})
</script>

<style scoped>
.market-page {
  max-width: 1200px;
  margin: 0 auto;
}

.market-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 20px;
  color: #fff;
}

.banner-content h1 {
  margin: 0 0 8px;
  font-size: 28px;
}

.banner-content p {
  margin: 0;
  font-size: 15px;
  opacity: 0.9;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-count {
  font-size: 13px;
  color: #909399;
}

.card-grid {
  margin-bottom: 24px;
}

.template-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
  border-radius: 10px;
}

.template-card:hover {
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.card-icon {
  font-size: 36px;
  line-height: 1;
  flex-shrink: 0;
}

.card-title-group h3 {
  margin: 0 0 4px;
  font-size: 16px;
  color: #303133;
}

.card-title-group p {
  margin: 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.4;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #c0c4cc;
  margin-bottom: 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.drawer-icon {
  font-size: 64px;
  text-align: center;
  margin-bottom: 20px;
}

.drawer-actions {
  margin-top: 24px;
  text-align: center;
}
</style>

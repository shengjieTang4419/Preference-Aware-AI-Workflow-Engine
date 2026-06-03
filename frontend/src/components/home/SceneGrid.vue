<template>
  <div class="section">
    <h2 class="section-title">🔥 热门场景</h2>
    <template v-if="scenes.length > 0">
      <div class="scene-grid">
        <div
          v-for="scene in scenes"
          :key="scene.id"
          class="scene-card"
          :class="{ active: selectedScene?.id === scene.id }"
          @click="$emit('select', scene)"
        >
          <div class="scene-icon">{{ scene.icon }}</div>
          <div class="scene-title">{{ scene.title }}</div>
          <div class="scene-subtitle">{{ scene.subtitle }}</div>
          <div class="scene-badges">
            <el-tag
              v-if="scene.price_tier"
              :type="getPriceTierType(scene.price_tier)"
              size="small"
              class="badge-tag"
            >
              {{ getPriceTierLabel(scene.price_tier) }}
            </el-tag>
            <el-tag
              v-if="scene.exec_mode"
              :type="scene.exec_mode === 'auto' ? 'success' : 'warning'"
              size="small"
              class="badge-tag"
            >
              {{ scene.exec_mode === 'auto' ? '自动' : '人工审核' }}
            </el-tag>
          </div>
          <div class="scene-tags">
            <el-tag
              v-for="tag in scene.tags.slice(0, 2)"
              :key="tag"
              size="small"
              :type="getTagType(tag)"
              class="scene-tag"
            >{{ tag }}</el-tag>
          </div>
        </div>
      </div>
    </template>
    <div v-else class="no-scenes-tip">
      <el-empty description="暂无可用场景">
        <el-button type="primary" @click="$router.push('/market')">前往模版市场安装</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SceneConfig } from '@/api'

defineProps<{
  scenes: SceneConfig[]
  selectedScene: SceneConfig | null
}>()

defineEmits<{
  select: [scene: SceneConfig]
}>()

function getPriceTierType(tier: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    free: 'success', basic: '', premium: 'warning',
  }
  return map[tier] || 'info'
}

function getPriceTierLabel(tier: string) {
  const map: Record<string, string> = {
    free: '免费', basic: '基础', premium: '高级',
  }
  return map[tier] || tier
}

function getTagType(tag: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    '热门': 'danger', '推荐': 'success', '新上线': '', '即将上线': 'info',
  }
  return map[tag] || 'info'
}
</script>

<style scoped>
.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 992px) {
  .scene-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 768px) {
  .scene-grid { grid-template-columns: repeat(2, 1fr); }
}

.scene-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
  border: 2px solid transparent;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.scene-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
}

.scene-card.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
}

.scene-icon {
  font-size: 36px;
  margin-bottom: 10px;
}

.scene-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.scene-subtitle {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  flex: 1;
}

.scene-badges {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 8px;
}

.badge-tag {
  font-size: 11px;
}

.scene-tags {
  display: flex;
  justify-content: center;
  gap: 6px;
}

.scene-tag {
  font-size: 11px;
}

.no-scenes-tip {
  padding: 40px 0;
}
</style>

<template>
  <el-card class="provider-card">
    <template #header>
      <div class="provider-header">
        <div class="provider-title">
          <span class="provider-icon">{{ providerIcon }}</span>
          <span>{{ provider.display_name }}</span>
        </div>
        <el-tag :type="provider.is_configured ? 'success' : 'warning'" size="small">
          {{ provider.is_configured ? '已配置' : '未配置' }}
        </el-tag>
      </div>
    </template>

    <el-form label-position="top">
      <!-- API Key -->
      <el-form-item label="API Key">
        <el-input
          :model-value="modelValue.api_key"
          @update:model-value="updateField('api_key', $event)"
          :type="showApiKey ? 'text' : 'password'"
          :placeholder="apiKeyPlaceholder"
        >
          <template #suffix>
            <el-icon @click="showApiKey = !showApiKey" style="cursor: pointer">
              <View v-if="!showApiKey" />
              <Hide v-else />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>

      <!-- Base URL -->
      <el-form-item label="Base URL">
        <el-input
          :model-value="modelValue.base_url"
          @update:model-value="updateField('base_url', $event)"
          :placeholder="provider.base_url || ''"
        />
      </el-form-item>

      <!-- 三级模型配置 -->
      <el-divider content-position="left">模型配置</el-divider>

      <!-- 初级模型 -->
      <div class="model-tier">
        <div class="tier-header">
          <el-tag type="info" size="small">初级</el-tag>
          <span class="tier-desc">简单任务，快速响应</span>
          <el-button 
            v-if="!modelValue.basic?.is_default"
            size="small" 
            text
            @click="setDefaultTier('basic')"
          >
            设为默认
          </el-button>
          <el-tag v-else type="success" size="small">✓ 默认</el-tag>
        </div>
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="模型名称">
              <el-input
                :model-value="modelValue.basic?.model"
                @update:model-value="updateTier('basic', 'model', $event)"
                placeholder="例如: qwen-turbo"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Temperature">
              <el-input-number
                :model-value="modelValue.basic?.temperature"
                @update:model-value="updateTier('basic', 'temperature', $event)"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 中级模型 -->
      <div class="model-tier">
        <div class="tier-header">
          <el-tag type="primary" size="small">中级</el-tag>
          <span class="tier-desc">常规任务，平衡性能</span>
          <el-button 
            v-if="!modelValue.standard?.is_default"
            size="small" 
            text
            @click="setDefaultTier('standard')"
          >
            设为默认
          </el-button>
          <el-tag v-else type="success" size="small">✓ 默认</el-tag>
        </div>
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="模型名称">
              <el-input
                :model-value="modelValue.standard?.model"
                @update:model-value="updateTier('standard', 'model', $event)"
                placeholder="例如: qwen-plus"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Temperature">
              <el-input-number
                :model-value="modelValue.standard?.temperature"
                @update:model-value="updateTier('standard', 'temperature', $event)"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 高级模型 -->
      <div class="model-tier">
        <div class="tier-header">
          <el-tag type="danger" size="small">高级</el-tag>
          <span class="tier-desc">复杂任务，深度思考</span>
          <el-button 
            v-if="!modelValue.advanced?.is_default"
            size="small" 
            text
            @click="setDefaultTier('advanced')"
          >
            设为默认
          </el-button>
          <el-tag v-else type="success" size="small">✓ 默认</el-tag>
        </div>
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="模型名称">
              <el-input
                :model-value="modelValue.advanced?.model"
                @update:model-value="updateTier('advanced', 'model', $event)"
                placeholder="例如: qwen-max"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Temperature">
              <el-input-number
                :model-value="modelValue.advanced?.temperature"
                @update:model-value="updateTier('advanced', 'temperature', $event)"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <el-button
        type="primary"
        @click="$emit('test')"
        :loading="testing"
        style="width: 100%; margin-top: 16px"
      >
        测试连接
      </el-button>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { View, Hide } from '@element-plus/icons-vue'
import type { ModelTierConfig } from '@/api/types'

interface Provider {
  name: string
  display_name: string
  is_configured: boolean
  base_url?: string
}

interface ProviderSettings {
  api_key?: string
  base_url?: string
  basic?: ModelTierConfig
  standard?: ModelTierConfig
  advanced?: ModelTierConfig
}

const props = defineProps<{
  provider: Provider
  modelValue: ProviderSettings
  testing: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ProviderSettings]
  test: []
}>()

const showApiKey = ref(false)

const providerIcon = computed(() => {
  const icons: Record<string, string> = {
    dashscope: '🤖',
    claude: '🧠',
    openai: '🌟'
  }
  return icons[props.provider.name] || '🔧'
})

const apiKeyPlaceholder = computed(() => {
  const placeholders: Record<string, string> = {
    dashscope: 'sk-...',
    claude: 'sk-ant-...',
    openai: 'sk-...'
  }
  return placeholders[props.provider.name] || 'API Key'
})

const updateField = (field: keyof ProviderSettings, value: any) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

const updateTier = (tier: 'basic' | 'standard' | 'advanced', field: 'model' | 'temperature', value: any) => {
  const currentTier = props.modelValue[tier] || { model: '', temperature: 0.7 }
  emit('update:modelValue', {
    ...props.modelValue,
    [tier]: {
      ...currentTier,
      [field]: value
    }
  })
}

const setDefaultTier = (tier: 'basic' | 'standard' | 'advanced') => {
  // 将所有模型的 is_default 设为 false，只有选中的设为 true
  emit('update:modelValue', {
    ...props.modelValue,
    basic: {
      ...(props.modelValue.basic || { model: '', temperature: 0.3 }),
      is_default: tier === 'basic'
    },
    standard: {
      ...(props.modelValue.standard || { model: '', temperature: 0.7 }),
      is_default: tier === 'standard'
    },
    advanced: {
      ...(props.modelValue.advanced || { model: '', temperature: 0.9 }),
      is_default: tier === 'advanced'
    }
  })
}
</script>

<style scoped>
.provider-card {
  margin-bottom: 20px;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.provider-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.provider-icon {
  font-size: 24px;
}

.model-tier {
  margin-bottom: 20px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.tier-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.tier-desc {
  font-size: 13px;
  color: #909399;
}

:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}
</style>

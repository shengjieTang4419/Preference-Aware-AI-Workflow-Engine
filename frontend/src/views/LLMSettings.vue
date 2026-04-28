<template>
  <div class="llm-settings-page">
    <div class="page-header">
      <div class="header-left">
        <h2>⚙️ LLM 设置</h2>
        <p class="subtitle">配置大语言模型提供商和参数</p>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else class="settings-content">
      <el-card class="mb-20">
        <template #header>
          <span class="card-header">默认 LLM 提供商</span>
        </template>
        <el-select v-model="settings.default_provider" style="width: 100%">
          <el-option 
            v-for="provider in providers" 
            :key="provider.name" 
            :value="provider.name"
            :label="provider.display_name + (!provider.is_configured ? ' (未配置)' : '')"
          />
        </el-select>
      </el-card>

      <div class="providers-config">
        <ProviderConfigCard
          v-for="provider in providers"
          :key="provider.name"
          :provider="provider"
          v-model="(settings as any)[provider.name]"
          :testing="(testing as any)[provider.name] || false"
          @test="testConnection(provider.name as 'dashscope' | 'claude')"
        />
      </div>

      <el-card>
        <div class="input-actions">
          <el-button type="primary" @click="saveSettings" :loading="saving">
            保存设置
          </el-button>
          <el-button @click="loadSettings">
            重置
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { LLMProvider, LLMSettings } from '@/api/types'
import ProviderConfigCard from '@/components/settings/ProviderConfigCard.vue'

const loading = ref(true)
const saving = ref(false)
const testing = ref({ dashscope: false, claude: false })

const providers = ref<LLMProvider[]>([])
const settings = ref<LLMSettings>({
  default_provider: 'dashscope',
  dashscope: {
    api_key: '',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    basic: { model: 'qwen-turbo', temperature: 0.3 },
    standard: { model: 'qwen-plus', temperature: 0.7 },
    advanced: { model: 'qwen-max', temperature: 0.9 },
  },
  claude: {
    api_key: '',
    base_url: 'https://api.anthropic.com/v1',
    basic: { model: 'claude-3-haiku-20240307', temperature: 0.3 },
    standard: { model: 'claude-3-5-sonnet-20241022', temperature: 0.7 },
    advanced: { model: 'claude-3-opus-20240229', temperature: 0.9 },
  },
})

const loadSettings = async () => {
  try {
    loading.value = true
    const [providersData, settingsData] = await Promise.all([
      api.llm.listProviders(),
      api.llm.getSettings(),
    ])
    
    providers.value = providersData.providers
    settings.value = settingsData
    
    // 确保默认值存在
    if (!settings.value.dashscope) {
      settings.value.dashscope = {
        api_key: '',
        base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        basic: { model: 'qwen-turbo', temperature: 0.3 },
        standard: { model: 'qwen-plus', temperature: 0.7 },
        advanced: { model: 'qwen-max', temperature: 0.9 },
      }
    }
    
    if (!settings.value.claude) {
      settings.value.claude = {
        api_key: '',
        base_url: 'https://api.anthropic.com/v1',
        basic: { model: 'claude-3-haiku-20240307', temperature: 0.3 },
        standard: { model: 'claude-3-5-sonnet-20241022', temperature: 0.7 },
        advanced: { model: 'claude-3-opus-20240229', temperature: 0.9 },
      }
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    showMessage('加载设置失败', 'error')
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  try {
    saving.value = true
    const result = await api.llm.updateSettings(settings.value)
    showMessage(result.message, 'success')
    await loadSettings()
  } catch (error: any) {
    console.error('Failed to save settings:', error)
    showMessage(error.response?.data?.detail || '保存设置失败', 'error')
  } finally {
    saving.value = false
  }
}

const testConnection = async (provider: 'dashscope' | 'claude') => {
  try {
    testing.value[provider] = true
    const result = await api.llm.testProvider(provider)
    showMessage(result.message, 'success')
  } catch (error: any) {
    console.error(`Failed to test ${provider}:`, error)
    showMessage(error.response?.data?.detail || `测试 ${provider} 连接失败`, 'error')
  } finally {
    testing.value[provider] = false
  }
}

const showMessage = (msg: string, type: 'success' | 'error') => {
  if (type === 'success') {
    ElMessage.success(msg)
  } else {
    ElMessage.error(msg)
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.llm-settings-page {
  max-width: 1200px;
  margin: 0 auto;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}


.providers-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 2rem;
}

</style>

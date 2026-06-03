import axios from 'axios'
import type { AxiosInstance } from 'axios'
import type { Agent, Task, Crew, Execution, Skill, SkillsStatistics, PreferenceProposal, PreferenceProposalDetail, DiffView, LLMProvider, LLMSettings, Scene, SceneConfig, Creation, Membership, PricingPlan, MembershipTransaction, DiscoverSkill, InstalledSkill, MagicWandMatchResponse, FlowData } from './types'

// 创建 axios 实例
const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login'
      }
    }
    console.error('[API Error]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API 封装
export const api = {
  health: {
    check: () => client.get('/health'),
  },

  auth: {
    login: (data: { username: string; password: string }): Promise<any> =>
      client.post('/auth/login', data),
    register: (data: { username: string; email: string; password: string }): Promise<any> =>
      client.post('/auth/register', data),
    me: (): Promise<any> => client.get('/auth/me'),
  },

  agents: {
    list: (): Promise<Agent[]> => client.get('/agents'),
    get: (id: string): Promise<Agent> => client.get(`/agents/${id}`),
    create: (data: Partial<Agent>): Promise<Agent> => client.post('/agents', data),
    update: (id: string, data: Partial<Agent>): Promise<Agent> => client.put(`/agents/${id}`, data),
    delete: (id: string): Promise<void> => client.delete(`/agents/${id}`),
  },

  tasks: {
    list: (): Promise<Task[]> => client.get('/tasks'),
    get: (id: string): Promise<Task> => client.get(`/tasks/${id}`),
    create: (data: Partial<Task>): Promise<Task> => client.post('/tasks', data),
    update: (id: string, data: Partial<Task>): Promise<Task> => client.put(`/tasks/${id}`, data),
    delete: (id: string): Promise<void> => client.delete(`/tasks/${id}`),
  },

  crews: {
    list: (): Promise<Crew[]> => client.get('/crews'),
    get: (id: string): Promise<Crew> => client.get(`/crews/${id}`),
    create: (data: Partial<Crew>): Promise<Crew> => client.post('/crews', data),
    update: (id: string, data: Partial<Crew>): Promise<Crew> => client.put(`/crews/${id}`, data),
    delete: (id: string): Promise<void> => client.delete(`/crews/${id}`),
    getPlaceholders: (id: string): Promise<string[]> => client.get(`/crews/${id}/placeholders`),
  },

  executions: {
    list: (): Promise<Execution[]> => client.get('/executions'),
    get: (id: string): Promise<Execution> => client.get(`/executions/${id}`),
    create: (data: Partial<Execution>): Promise<Execution> => client.post('/executions', data),
    getLogs: (id: string): Promise<string> => client.get(`/executions/${id}/logs`),
    getFiles: (id: string): Promise<{ execution_id: string; output_dir: string; files: any[] }> =>
      client.get(`/executions/${id}/files`),
    getFileContent: (id: string, filePath: string): Promise<{ execution_id: string; file_path: string; content: string }> =>
      client.get(`/executions/${id}/files/content`, { params: { file_path: filePath } }),
    getFileDownloadUrl: (execId: string, filePath: string): string =>
      `/api/executions/${execId}/files/download?file_path=${encodeURIComponent(filePath)}`,
    getFlow: (execId: string): Promise<FlowData> =>
      client.get(`/executions/${execId}/flow`),
  },

  files: {
    getRoots: (): Promise<{ roots: Array<{ name: string; path: string }> }> =>
      client.get('/files/roots'),
    browse: (path: string): Promise<{
      current: string
      parent: string | null
      directories: Array<{ name: string; path: string; size: number; modified: number }>
      files: Array<{ name: string; path: string; size: number; modified: number }>
    }> => client.post('/files/browse', { path }),
    uploadDoc: (file: File): Promise<{ filename: string; path: string; size: number }> => {
      const form = new FormData()
      form.append('file', file)
      return client.post('/files/upload-doc', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    // 上传图片，返回本地路径 + OCR 结果
    uploadImage: (file: File): Promise<{ filename: string; path: string; size: number; ocr_text: string; ocr_success: boolean }> => {
      const form = new FormData()
      form.append('file', file)
      return client.post('/files/upload-image', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    // 对图片进行 OCR 识别
    ocrImage: (imagePath: string): Promise<{ image_path: string; text: string; success: boolean }> =>
      client.post('/files/ocr', { image_path: imagePath }),
    listDocs: (): Promise<{ files: Array<{ name: string; path: string; size: number }> }> =>
      client.get('/files/list-docs'),
  },

  chat: {
    generateCrew: (scenario: string, scene_id?: string, doc_filenames?: string[], ocr_texts?: string[]): Promise<{
      execution_id: string
      status: string
    }> => client.post('/chat/generate-crew', { scenario, scene_id, doc_filenames, ocr_texts }),
  },

  // Skills API
  skills: {
    list: (): Promise<Skill[]> => client.get('/skills/'),
    getDetail: (skillName: string): Promise<Skill> => client.get(`/skills/${skillName}`),
    getStatistics: (): Promise<SkillsStatistics> => client.get('/skills/statistics'),
    getRecommended: (role: string): Promise<Skill[]> => client.get(`/skills/recommend/${encodeURIComponent(role)}`),
    aiRecommend: (request: {
      role: string
      goal: string
      backstory: string
      task_context?: string
    }): Promise<{
      mode: string
      preferred: string[]
      auto_match: boolean
      include_patterns: string[]
      exclude_patterns: string[]
    }> => client.post('/skills/ai-recommend', request),
  },

  // 偏好进化 API - Git Merge 风格
  preferences: {
    // 获取所有提案
    listProposals: (): Promise<PreferenceProposal[]> => client.get('/preferences/proposals'),
    // 获取单个提案详情
    getProposal: (execId: string): Promise<PreferenceProposalDetail> => client.get(`/preferences/proposals/${execId}`),
    // 获取行级 diff（用于可视化对比）
    getDiff: (execId: string): Promise<DiffView> => client.get(`/preferences/proposals/${execId}/diff`),
    // 合并提案到 preferences.md
    mergeProposal: (execId: string): Promise<{ status: string; message: string }> =>
      client.post('/preferences/proposals/merge', { exec_id: execId }),
    // 拒绝提案
    rejectProposal: (execId: string, reason?: string): Promise<{ status: string }> =>
      client.post('/preferences/proposals/reject', { exec_id: execId, reason }),
    // 获取当前 preferences.md 内容
    getCurrent: (): Promise<{ content: string; file_path: string }> =>
      client.get('/preferences/current'),
    // 手动触发执行回顾（通常自动触发）
    evolveFromExecution: (execId: string): Promise<{ status: string; suggestions_count: number; view_url: string }> =>
      client.post(`/preferences/evolve-from-execution/${execId}`),
  },

  // 创意工坊 API
  scenes: {
    list: (): Promise<Scene[]> => client.get('/scenes'),
  },

  sceneConfigs: {
    list: (): Promise<SceneConfig[]> => client.get('/scene-configs'),
    get: (id: string): Promise<SceneConfig> => client.get(`/scene-configs/${id}`),
  },

  creations: {
    list: (): Promise<Creation[]> => client.get('/creations'),
    get: (id: string): Promise<Creation> => client.get(`/creations/${id}`),
    create: (data: { scene_id: string; input_text: string; input_files?: any[] }): Promise<Creation> =>
      client.post('/creations', data),
  },

  // LLM 设置 API
  llm: {
    listProviders: (): Promise<{ providers: LLMProvider[]; default_provider: string }> =>
      client.get('/llm/providers'),
    getSettings: (): Promise<LLMSettings> =>
      client.get('/llm/settings'),
    updateSettings: (settings: LLMSettings): Promise<{ message: string }> =>
      client.put('/llm/settings', settings),
    testProvider: (provider: string, model?: string): Promise<{ success: boolean; provider: string; model: string; message: string }> =>
      client.post(`/llm/test/${provider}`, null, { params: { model } }),
  },

  // 会员系统 API
  membership: {
    me: (): Promise<Membership> => client.get('/membership/me'),
    plans: (): Promise<PricingPlan[]> => client.get('/membership/plans'),
    activate: (code: string): Promise<Membership> => client.post('/membership/activate', { code }),
    purchase: (level: string, months: number): Promise<Membership> => client.post('/membership/purchase', { level, months }),
    transactions: (): Promise<MembershipTransaction[]> => client.get('/membership/transactions'),
    installedScenes: (): Promise<string[]> => client.get('/membership/installed-scenes'),
    installScene: (sceneId: string): Promise<any> => client.post(`/membership/install-scene/${sceneId}`),
  },

  // 技能市场 API
  skillsMarket: {
    discover: (q?: string): Promise<DiscoverSkill[]> =>
      client.get('/skills-market/discover', { params: { q: q || '' } }),
    installed: (): Promise<InstalledSkill[]> =>
      client.get('/skills-market/installed'),
    detail: (name: string): Promise<InstalledSkill> =>
      client.get(`/skills-market/installed/${name}`),
    install: (pkg: string): Promise<InstalledSkill> =>
      client.post('/skills-market/install', { package: pkg }),
    uninstall: (name: string): Promise<{ status: string }> =>
      client.delete(`/skills-market/installed/${name}`),
  },

  // 魔法棒 API
  magicWand: {
    match: (data: { scene_id: string; user_input: string }): Promise<MagicWandMatchResponse> =>
      client.post('/magic-wand/match', data),
  },
}

export * from './types'

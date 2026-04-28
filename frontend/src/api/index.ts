import axios from 'axios'
import type { Agent, Task, Crew, Execution, Skill, SkillsStatistics, PreferenceProposal, PreferenceProposalDetail, DiffView, LLMProvider, LLMSettings } from './types'

// 创建 axios 实例
const client = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
client.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('[API Error]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API 封装
export const api = {
  health: {
    check: () => client.get('/health'),
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
    listDocs: (): Promise<{ files: Array<{ name: string; path: string; size: number }> }> =>
      client.get('/files/list-docs'),
  },

  chat: {
    generateCrew: (scenario: string, context?: string): Promise<{
      topic: string
      crew_id: string
      agent_ids: string[]
      task_ids: string[]
      summary: string
    }> => client.post('/chat/generate-crew', { scenario, context }, {
      timeout: 120000, // AI 生成需要更长时间，设置 120 秒超时
    }),
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
}

export * from './types'

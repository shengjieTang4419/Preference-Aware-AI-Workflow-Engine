export interface Agent {
  id: string
  name: string
  role: string
  goal: string
  backstory: string
  allow_delegation?: boolean
  max_execution_time?: number
  llm_key?: string
  created_at: string
  updated_at: string
}

export interface Task {
  id: string
  name: string
  description: string
  expected_output: string
  agent_id: string
  context_task_ids?: string[]
  async_execution?: boolean
  // 新增：归属信息
  topic?: string
  crew_id?: string
  execution_id?: string
  role_type?: string
  // 时间戳
  created_at: string
  updated_at: string
}

export interface Crew {
  id: string
  name: string
  description?: string
  agent_ids: string[]
  task_ids: string[]
  process_type: 'sequential' | 'hierarchical'
  // Agent 模型等级分配 (agent_id -> model_tier)
  agent_model_assignments?: Record<string, 'basic' | 'standard' | 'advanced'>
  created_at: string
  updated_at: string
}

export interface Execution {
  id: string
  crew_id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  requirement: string
  input_folder?: string
  output_dir: string
  inputs?: Record<string, string>
  result?: string
  error?: string
  created_at: string
  updated_at: string
}

export interface FileItem {
  name: string
  path: string
  type: 'file' | 'directory'
  size?: number
  modified?: string
}

export interface SkillMetadata {
  name: string
  description: string
  author?: string
  version?: string
  [key: string]: any
}

export interface SkillScript {
  name: string
  path: string
  size: number
}

export interface Skill {
  name: string
  path: string
  metadata: SkillMetadata
  has_scripts: boolean
  content?: string
  scripts?: SkillScript[]
}

export interface SkillsStatistics {
  total_skills: number
  skills_with_scripts: number
  skills_by_directory: Record<string, number>
}

// === 偏好进化相关类型 ===

export interface SuggestedPreference {
  category: string
  content: string
  reason: string
  confidence: number
  source_exec_id: string
}

export interface PreferenceProposal {
  exec_id: string
  exec_topic: string
  created_at: string
  diff_summary: string
  suggestions_count: number
  status: 'pending' | 'merged' | 'rejected'
}

export interface PreferenceProposalDetail {
  exec_id: string
  exec_topic: string
  original_content: string
  suggested_content: string
  diff_summary: string
  suggestions: SuggestedPreference[]
  created_at: string
}

export interface DiffLine {
  type: 'context' | 'added' | 'removed'
  content: string
  line_number: number
}

export interface DiffView {
  exec_id: string
  lines: DiffLine[]
  stats: {
    added: number
    removed: number
    unchanged: number
  }
}

export interface ModelTierConfig {
  model: string
  temperature: number
}

export interface LLMProviderConfig {
  api_key?: string
  base_url?: string
  basic?: ModelTierConfig      // 初级模型
  standard?: ModelTierConfig   // 中级模型
  advanced?: ModelTierConfig   // 高级模型
}

export interface LLMProvider {
  name: string
  display_name: string
  is_configured: boolean
  available_models: string[]
  default_model: string
}

export interface LLMSettings {
  default_provider: string
  dashscope?: LLMProviderConfig
  claude?: LLMProviderConfig
}

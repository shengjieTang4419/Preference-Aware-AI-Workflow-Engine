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

// === 创意工坊相关类型 ===

export interface Scene {
  id: string
  icon: string
  title: string
  subtitle: string
  placeholder: string
  category: string
  tags: string[]
  output_format: string
  enabled: boolean
  sort_order: number
}

export interface SceneConfig {
  id: string
  icon: string
  title: string
  subtitle: string
  placeholder?: string
  category: string
  tags: string[]
  output_format: string
  enabled: boolean
  visible: boolean
  sort_order: number
  price_tier: string
  exec_mode: string
  output_dir?: string
  crew_template?: string
  description?: string
  created_at: string
  updated_at: string
}

export interface Creation {
  id: string
  scene_id: string
  scene_title?: string
  scene_icon?: string
  input_text: string
  status: 'pending' | 'running' | 'success' | 'failed'
  output?: string
  created_at: string
  updated_at: string
}

// === 会员系统相关类型 ===

export interface Membership {
  user_id: number
  level: string
  activation_code?: string
  activated_at?: string
  expires_at?: string
  is_expired: boolean
  virtual_money: number
}

export interface PricingPlan {
  level: string
  name: string
  price: number
  period: string
  features: string[]
  scene_access: string
}

export interface MembershipTransaction {
  id: number
  user_id: number
  action: string
  from_level?: string
  to_level?: string
  amount: number
  activation_code?: string
  remark?: string
  created_at: string
}

// === 技能市场相关类型 ===

export interface DiscoverSkill {
  name: string
  source: string
  installs: number | string
  description: string
}

export interface InstalledSkill {
  name: string
  package: string
  installed_at: string
  summary: string
  what_it_does: string
  when_to_use: string[]
  key_features: string[]
  example: string
  raw_content: string
}

// === 创意执行流程相关类型 ===

export interface ArtifactOut {
  id: number
  execution_id: string
  user_id?: number | null
  scene_id: string
  title?: string | null
  description?: string | null
  output_type?: string | null
  output_dir?: string | null
  output_files: string[]
  preview_text?: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  error_message?: string | null
  created_at: string
  completed_at?: string | null
}

export interface CreativityExecuteResponse {
  execution_id: string
  status: string
  artifact?: ArtifactOut | null
}

// === 执行流程图相关类型 ===

export interface FlowTask {
  id: string
  name: string
  description: string
  expected_output: string
  agent_id: string
  agent_name: string
  agent_role: string
  agent_goal: string
  agent_backstory: string
  model_tier: 'basic' | 'standard' | 'advanced'
  context_task_ids: string[]
  async_execution: boolean
  status: 'completed' | 'running' | 'pending' | 'failed'
  index: number
}

export interface FlowAgent {
  id: string
  name: string
  role: string
  goal: string
  backstory: string
  llm_key: string
  model_tier: 'basic' | 'standard' | 'advanced'
  assigned_tasks: string[]
}

export interface FlowEdge {
  source: string
  target: string
  type: 'dependency'
}

export interface FlowExecution {
  id: string
  status: string
  requirement: string
  crew_id: string
  created_at: string
  started_at: string
  completed_at: string
  error_message?: string | null
}

export interface FlowCrew {
  id: string
  name: string
  description: string
  process_type: 'sequential' | 'hierarchical'
  agent_model_assignments: Record<string, 'basic' | 'standard' | 'advanced'>
}

export interface FlowData {
  execution: FlowExecution
  crew: FlowCrew
  tasks: FlowTask[]
  agents: FlowAgent[]
  edges: FlowEdge[]
}

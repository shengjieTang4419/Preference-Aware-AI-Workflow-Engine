/**
 * 提案列表管理 Composable
 * 职责：加载、过滤、统计提案列表
 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { PreferenceProposal } from '@/api/types'

export function useProposalList() {
  const proposals = ref<PreferenceProposal[]>([])
  const loading = ref(false)
  const filterStatus = ref('all')

  // 统计
  const pendingCount = computed(() => 
    proposals.value.filter(p => p.status === 'pending').length
  )
  const mergedCount = computed(() => 
    proposals.value.filter(p => p.status === 'merged').length
  )
  const rejectedCount = computed(() => 
    proposals.value.filter(p => p.status === 'rejected').length
  )
  const totalCount = computed(() => proposals.value.length)

  // 过滤
  const filteredProposals = computed(() => {
    if (filterStatus.value === 'all') {
      return proposals.value
    }
    return proposals.value.filter(p => p.status === filterStatus.value)
  })

  // 加载提案列表
  const loadProposals = async () => {
    loading.value = true
    try {
      proposals.value = await api.preferences.listProposals()
      ElMessage.success(`加载了 ${proposals.value.length} 个提案`)
    } catch (error) {
      ElMessage.error('加载提案列表失败')
    } finally {
      loading.value = false
    }
  }

  // 更新提案状态
  const updateProposalStatus = (execId: string, status: 'merged' | 'rejected') => {
    const proposal = proposals.value.find(p => p.exec_id === execId)
    if (proposal) {
      proposal.status = status
    }
  }

  return {
    proposals,
    loading,
    filterStatus,
    pendingCount,
    mergedCount,
    rejectedCount,
    totalCount,
    filteredProposals,
    loadProposals,
    updateProposalStatus
  }
}

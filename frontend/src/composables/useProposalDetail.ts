/**
 * 提案详情管理 Composable
 * 职责：加载提案详情、Diff 数据
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import type { PreferenceProposalDetail, DiffView } from '@/api/types'

export function useProposalDetail() {
  const showDetail = ref(false)
  const currentProposal = ref<PreferenceProposalDetail | null>(null)
  const loadingDetail = ref(false)
  const diffLines = ref<DiffView['lines']>([])
  const diffStats = ref<DiffView['stats']>({ added: 0, removed: 0, unchanged: 0 })

  // 加载提案详情
  const viewProposalDetail = async (execId: string) => {
    showDetail.value = true
    loadingDetail.value = true
    currentProposal.value = null

    try {
      // 并行加载详情和 diff
      const [detail, diff] = await Promise.all([
        api.preferences.getProposal(execId),
        api.preferences.getDiff(execId),
      ])

      currentProposal.value = detail
      diffLines.value = diff.lines
      diffStats.value = diff.stats
    } catch (error) {
      ElMessage.error('加载提案详情失败')
      showDetail.value = false
    } finally {
      loadingDetail.value = false
    }
  }

  // 关闭详情
  const closeDetail = () => {
    showDetail.value = false
    currentProposal.value = null
    diffLines.value = []
    diffStats.value = { added: 0, removed: 0, unchanged: 0 }
  }

  return {
    showDetail,
    currentProposal,
    loadingDetail,
    diffLines,
    diffStats,
    viewProposalDetail,
    closeDetail
  }
}

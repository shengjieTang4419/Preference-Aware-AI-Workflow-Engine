/**
 * 提案操作 Composable
 * 职责：合并、拒绝提案
 */
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

export function useProposalActions() {
  const merging = ref(false)
  const rejecting = ref(false)
  const showRejectDialog = ref(false)
  const rejectReason = ref('')
  const currentRejectExecId = ref('')

  // 合并提案
  const mergeProposal = async (execId: string): Promise<boolean> => {
    try {
      await ElMessageBox.confirm(
        '确定要将这些变更合并到 preferences.md 吗？<br>原始文件将自动备份。',
        '确认合并',
        {
          confirmButtonText: '确认合并',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: true,
        }
      )

      merging.value = true
      const result = await api.preferences.mergeProposal(execId)
      ElMessage.success(result.message || '合并成功！')
      return true
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error('合并失败: ' + (error.message || '未知错误'))
      }
      return false
    } finally {
      merging.value = false
    }
  }

  // 打开拒绝对话框
  const openRejectDialog = (execId: string) => {
    currentRejectExecId.value = execId
    rejectReason.value = ''
    showRejectDialog.value = true
  }

  // 确认拒绝
  const confirmReject = async (): Promise<boolean> => {
    try {
      rejecting.value = true
      await api.preferences.rejectProposal(currentRejectExecId.value, rejectReason.value)
      ElMessage.success('已拒绝该提案')
      showRejectDialog.value = false
      return true
    } catch (error) {
      ElMessage.error('拒绝失败')
      return false
    } finally {
      rejecting.value = false
    }
  }

  // 取消拒绝
  const cancelReject = () => {
    showRejectDialog.value = false
    rejectReason.value = ''
    currentRejectExecId.value = ''
  }

  return {
    merging,
    rejecting,
    showRejectDialog,
    rejectReason,
    currentRejectExecId,
    mergeProposal,
    openRejectDialog,
    confirmReject,
    cancelReject
  }
}

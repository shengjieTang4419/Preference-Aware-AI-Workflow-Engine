/**
 * 当前偏好查看 Composable
 * 职责：加载和显示当前 preferences.md 内容
 */
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

export function useCurrentPreferences() {
  const showCurrent = ref(false)
  const currentPrefContent = ref('')
  const currentPrefPath = ref('')
  const loadingCurrent = ref(false)

  // 加载当前偏好
  const loadCurrentPreferences = async () => {
    loadingCurrent.value = true
    try {
      const result = await api.preferences.getCurrent()
      currentPrefContent.value = result.content
      currentPrefPath.value = result.file_path
      showCurrent.value = true
    } catch (error) {
      ElMessage.error('加载当前偏好失败')
    } finally {
      loadingCurrent.value = false
    }
  }

  // 关闭当前偏好
  const closeCurrent = () => {
    showCurrent.value = false
    currentPrefContent.value = ''
    currentPrefPath.value = ''
  }

  return {
    showCurrent,
    currentPrefContent,
    currentPrefPath,
    loadingCurrent,
    loadCurrentPreferences,
    closeCurrent
  }
}

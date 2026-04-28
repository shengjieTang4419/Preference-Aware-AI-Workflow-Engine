import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 通用 CRUD 对话框 Composable
 * 
 * 用于 Agent/Task/Crew 等资源的创建、编辑、删除操作
 * 
 * @example
 * const {
 *   items,
 *   loading,
 *   showDialog,
 *   form,
 *   editingId,
 *   openCreateDialog,
 *   openEditDialog,
 *   saveItem,
 *   deleteItem,
 *   loadItems
 * } = useCRUDDialog({
 *   resourceName: 'Agent',
 *   apiService: api.agents,
 *   defaultForm: { name: '', role: '', goal: '', backstory: '' }
 * })
 */

interface CRUDOptions<T> {
  /** 资源名称（用于提示消息） */
  resourceName: string
  /** API 服务对象 */
  apiService: {
    list: () => Promise<T[]>
    create: (data: Partial<T>) => Promise<T>
    update: (id: string, data: Partial<T>) => Promise<T>
    delete: (id: string) => Promise<void>
  }
  /** 默认表单数据 */
  defaultForm: Partial<T>
  /** 自定义验证函数（可选） */
  validate?: (form: Partial<T>) => string | null
}

export function useCRUDDialog<T extends { id: string }>(options: CRUDOptions<T>) {
  const { resourceName, apiService, defaultForm, validate } = options

  // 状态
  const items = ref<T[]>([])
  const loading = ref(false)
  const showDialog = ref(false)
  const editingId = ref<string | null>(null)
  const form = ref<Partial<T>>({ ...defaultForm })

  // 计算属性
  const isEditing = computed(() => !!editingId.value)
  const dialogTitle = computed(() => isEditing.value ? `编辑${resourceName}` : `新建${resourceName}`)

  // 加载列表
  const loadItems = async () => {
    loading.value = true
    try {
      items.value = await apiService.list()
    } catch (error: any) {
      ElMessage.error(`加载${resourceName}列表失败: ${error.message}`)
    } finally {
      loading.value = false
    }
  }

  // 打开创建对话框
  const openCreateDialog = () => {
    form.value = { ...defaultForm }
    editingId.value = null
    showDialog.value = true
  }

  // 打开编辑对话框
  const openEditDialog = (item: T) => {
    form.value = { ...item }
    editingId.value = item.id
    showDialog.value = true
  }

  // 关闭对话框
  const closeDialog = () => {
    showDialog.value = false
    form.value = { ...defaultForm }
    editingId.value = null
  }

  // 保存（创建或更新）
  const saveItem = async () => {
    // 自定义验证
    if (validate) {
      const error = validate(form.value)
      if (error) {
        ElMessage.warning(error)
        return
      }
    }

    loading.value = true
    try {
      if (isEditing.value) {
        // 更新
        await apiService.update(editingId.value!, form.value)
        ElMessage.success(`${resourceName}更新成功`)
      } else {
        // 创建
        await apiService.create(form.value)
        ElMessage.success(`${resourceName}创建成功`)
      }
      closeDialog()
      await loadItems()
    } catch (error: any) {
      ElMessage.error(`保存失败: ${error.message}`)
    } finally {
      loading.value = false
    }
  }

  // 删除
  const deleteItem = async (id: string) => {
    try {
      await ElMessageBox.confirm(
        `确定要删除这个${resourceName}吗？此操作不可恢复。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )

      loading.value = true
      await apiService.delete(id)
      ElMessage.success(`${resourceName}删除成功`)
      await loadItems()
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(`删除失败: ${error.message}`)
      }
    } finally {
      loading.value = false
    }
  }

  return {
    // 状态
    items,
    loading,
    showDialog,
    form,
    editingId,
    
    // 计算属性
    isEditing,
    dialogTitle,
    
    // 方法
    loadItems,
    openCreateDialog,
    openEditDialog,
    closeDialog,
    saveItem,
    deleteItem,
  }
}

<template>
  <!-- 登录/注册页 - 无侧边栏 -->
  <router-view v-if="isGuestRoute" />
  <!-- 主应用 - 带侧边栏 -->
  <div class="app-container" v-else>
    <el-container>
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <el-icon size="24"><Management /></el-icon>
          <span>CrewAI Web</span>
        </div>
        <el-menu
          :default-active="$route.path"
          router
          class="el-menu-vertical"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><MagicStick /></el-icon>
            <span>创意工坊</span>
          </el-menu-item>
          <el-menu-item index="/market">
            <el-icon><ShoppingCart /></el-icon>
            <span>模版市场</span>
          </el-menu-item>
          <el-menu-item index="/membership">
            <el-icon><StarFilled /></el-icon>
            <span>会员中心</span>
          </el-menu-item>
          <el-menu-item index="/agents">
            <el-icon><UserFilled /></el-icon>
            <span>Agents</span>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <span>Tasks</span>
          </el-menu-item>
          <el-menu-item index="/crews">
            <el-icon><Connection /></el-icon>
            <span>Crews</span>
          </el-menu-item>
          <el-menu-item index="/skills">
            <el-icon><Tools /></el-icon>
            <span>Skills</span>
          </el-menu-item>
          <el-menu-item index="/executions">
            <el-icon><VideoPlay /></el-icon>
            <span>执行历史</span>
          </el-menu-item>
          <el-menu-item index="/preferences">
            <el-icon><TrendCharts /></el-icon>
            <span>偏好进化</span>
          </el-menu-item>
          <el-menu-item index="/llm-settings">
            <el-icon><Setting /></el-icon>
            <span>LLM 设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header class="header">
          <div class="header-title">创意工坊</div>
          <div class="header-right" v-if="authStore.isAuthenticated">
            <span class="balance-display" v-if="authStore.user?.virtual_money !== undefined">
              💰 ¥{{ (authStore.user?.virtual_money || 0).toFixed(2) }}
            </span>
            <el-dropdown @command="handleHeaderCommand">
              <span class="user-dropdown">
                <el-tag
                  :type="memberTagType"
                  size="small"
                  class="member-tag"
                  v-if="memberLevel"
                >{{ memberLevel }}</el-tag>
                <span class="username">{{ authStore.user?.username }}</span>
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="membership">会员中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { computed, ref, onMounted, watch } from 'vue'
import { api } from '@/api'
import type { Membership } from '@/api'

const authStore = useAuthStore()
const router = useRouter()
const isGuestRoute = computed(() => router.currentRoute.value.meta?.guest === true)

const membership = ref<Membership | null>(null)

const memberLevel = computed(() => {
  const map: Record<string, string> = { free: 'Free', pro: 'Pro', max: 'Max' }
  return map[membership.value?.level || 'free'] || 'Free'
})

const memberTagType = computed(() => {
  const map: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    free: 'info', pro: '', max: 'warning',
  }
  return map[membership.value?.level || 'free'] || 'info'
})

async function fetchMembership() {
  if (!authStore.isAuthenticated) return
  try {
    membership.value = await api.membership.me()
    // sync virtual_money to user
    if (authStore.user && membership.value) {
      authStore.user.virtual_money = membership.value.virtual_money
    }
  } catch {
    // ignore
  }
}

function handleHeaderCommand(command: string) {
  if (command === 'membership') {
    router.push('/membership')
  } else if (command === 'logout') {
    handleLogout()
  }
}

function handleLogout() {
  authStore.logout()
  membership.value = null
  router.push('/login')
}

// Fetch membership on mount and when auth state changes
onMounted(fetchMembership)
watch(() => authStore.isAuthenticated, (val) => {
  if (val) fetchMembership()
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  border-bottom: 1px solid #1f2d3d;
}

.logo .el-icon {
  margin-right: 8px;
}

.el-menu-vertical {
  border-right: none;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.balance-display {
  font-size: 14px;
  font-weight: 600;
  color: #e6a23c;
  background: #fdf6ec;
  padding: 4px 12px;
  border-radius: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
}

.user-dropdown:hover {
  color: #409eff;
}

.member-tag {
  font-weight: 600;
}

.username {
  font-size: 14px;
  color: #606266;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}

:deep(.el-container) {
  height: 100%;
}
</style>

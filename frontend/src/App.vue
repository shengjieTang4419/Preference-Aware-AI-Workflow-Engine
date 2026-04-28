<template>
  <div class="app-container">
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
            <el-icon><ChatDotRound /></el-icon>
            <span>AI 对话</span>
          </el-menu-item>
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>仪表盘</span>
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
          <div class="header-title">一人公司智能助手</div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
// 组件逻辑
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
}

.header-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}

:deep(.el-container) {
  height: 100%;
}
</style>

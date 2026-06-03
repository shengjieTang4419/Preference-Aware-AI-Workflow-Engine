import { createRouter, createWebHistory } from 'vue-router'
import Chat from '@/views/Chat.vue'
import Home from '@/views/Home.vue'
import Agents from '@/views/Agents.vue'
import Tasks from '@/views/Tasks.vue'
import Crews from '@/views/Crews.vue'
import Executions from '@/views/Executions.vue'
import Skills from '@/views/Skills.vue'
import Preferences from '@/views/Preferences.vue'
import LLMSettings from '@/views/LLMSettings.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import TemplateMarket from '@/views/TemplateMarket.vue'
import Membership from '@/views/Membership.vue'
import ExecutionFlow from '@/views/ExecutionFlow.vue'
import PipelineProgress from '@/views/PipelineProgress.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: Login,
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: Register,
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'Home',
      component: Home,
    },
    {
      path: '/market',
      name: 'TemplateMarket',
      component: TemplateMarket,
    },
    {
      path: '/membership',
      name: 'Membership',
      component: Membership,
    },
    {
      path: '/pipeline/:id',
      name: 'PipelineProgress',
      component: PipelineProgress,
    },
    {
      path: '/flow/:id',
      name: 'ExecutionFlow',
      component: ExecutionFlow,
    },
    {
      path: '/chat',
      name: 'Chat',
      component: Chat,
    },
    {
      path: '/agents',
      name: 'Agents',
      component: Agents,
    },
    {
      path: '/tasks',
      name: 'Tasks',
      component: Tasks,
    },
    {
      path: '/crews',
      name: 'Crews',
      component: Crews,
    },
    {
      path: '/executions',
      name: 'Executions',
      component: Executions,
    },
    {
      path: '/skills',
      name: 'Skills',
      component: Skills,
    },
    {
      path: '/preferences',
      name: 'Preferences',
      component: Preferences,
    },
    {
      path: '/llm-settings',
      name: 'LLMSettings',
      component: LLMSettings,
    },
  ],
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')

  // 已登录用户访问登录/注册页 -> 重定向到首页
  if (to.meta.guest && token) {
    return next('/')
  }

  // 未登录用户访问受保护页面 -> 重定向到登录页
  if (!to.meta.guest && !token) {
    return next('/login')
  }

  next()
})

export default router

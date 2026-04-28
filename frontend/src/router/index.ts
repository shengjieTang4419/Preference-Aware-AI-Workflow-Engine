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

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Chat',
      component: Chat,
    },
    {
      path: '/dashboard',
      name: 'Home',
      component: Home,
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

export default router

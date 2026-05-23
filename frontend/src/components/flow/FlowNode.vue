<template>
  <g
    :transform="`translate(${x}, ${y})`"
    class="flow-node-group"
    :class="{ selected: isSelected, clickable: true }"
    @click="$emit('select', task.id)"
  >
    <!-- Node shadow -->
    <rect
      :x="-nodeWidth / 2"
      :y="-nodeHeight / 2"
      :width="nodeWidth"
      :height="nodeHeight"
      rx="12"
      ry="12"
      class="node-shadow"
    />
    <!-- Node background -->
    <rect
      :x="-nodeWidth / 2"
      :y="-nodeHeight / 2"
      :width="nodeWidth"
      :height="nodeHeight"
      rx="12"
      ry="12"
      class="node-bg"
      :class="statusClass"
    />
    <!-- Status indicator bar (left side) -->
    <rect
      :x="-nodeWidth / 2"
      :y="-nodeHeight / 2"
      width="5"
      :height="nodeHeight"
      rx="3"
      ry="0"
      :style="{ fill: statusColor }"
    />

    <!-- Status icon -->
    <text
      :x="-nodeWidth / 2 + 18"
      :y="-nodeHeight / 2 + 24"
      class="status-icon"
      text-anchor="middle"
      dominant-baseline="central"
    >{{ statusIcon }}</text>

    <!-- Task name -->
    <text
      :x="-nodeWidth / 2 + 36"
      :y="-nodeHeight / 2 + 24"
      class="node-title"
      dominant-baseline="central"
    >{{ truncatedName }}</text>

    <!-- Agent info line -->
    <text
      :x="0"
      :y="-nodeHeight / 2 + 50"
      class="node-agent"
      text-anchor="middle"
      dominant-baseline="central"
    >👤 {{ task.agent_name }}</text>

    <!-- Model tier badge -->
    <g :transform="`translate(${badgeX}, ${-nodeHeight / 2 + 70})`">
      <rect
        :x="-badgeWidth / 2"
        :y="-10"
        :width="badgeWidth"
        height="20"
        rx="10"
        ry="10"
        :style="{ fill: tierBgColor }"
      />
      <text
        class="tier-text"
        text-anchor="middle"
        dominant-baseline="central"
        :style="{ fill: tierTextColor }"
      >{{ tierLabel }}</text>
    </g>

    <!-- Duration (if completed) -->
    <text
      v-if="task.status === 'completed' && executionTimes && executionTimes[task.id]"
      :x="0"
      :y="-nodeHeight / 2 + 96"
      class="node-duration"
      text-anchor="middle"
      dominant-baseline="central"
    >⏱️ {{ executionTimes[task.id] }}</text>

    <!-- Selection ring -->
    <rect
      v-if="isSelected"
      :x="-nodeWidth / 2 - 3"
      :y="-nodeHeight / 2 - 3"
      :width="nodeWidth + 6"
      :height="nodeHeight + 6"
      rx="14"
      ry="14"
      class="selection-ring"
    />
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FlowTask } from '@/api'

const props = defineProps<{
  task: FlowTask
  x: number
  y: number
  isSelected: boolean
  executionTimes?: Record<string, string>
}>()

defineEmits<{
  select: [id: string]
}>()

const nodeWidth = 220
const nodeHeight = 110
const badgeWidth = 80

const truncatedName = computed(() => {
  const name = props.task.name
  return name.length > 12 ? name.slice(0, 12) + '…' : name
})

const badgeX = computed(() => 0)

const statusClass = computed(() => {
  const map: Record<string, string> = {
    completed: 'status-completed',
    running: 'status-running',
    pending: 'status-pending',
    failed: 'status-failed',
  }
  return map[props.task.status] || 'status-pending'
})

const statusColor = computed(() => {
  const map: Record<string, string> = {
    completed: '#67c23a',
    running: '#409eff',
    pending: '#c0c4cc',
    failed: '#f56c6c',
  }
  return map[props.task.status] || '#c0c4cc'
})

const statusIcon = computed(() => {
  const map: Record<string, string> = {
    completed: '✅',
    running: '⏳',
    pending: '⏸️',
    failed: '❌',
  }
  return map[props.task.status] || '⏸️'
})

const tierLabel = computed(() => {
  const map: Record<string, string> = {
    advanced: '🚀 高级',
    standard: '⚡ 标准',
    basic: '📦 基础',
  }
  return map[props.task.model_tier] || '📦 基础'
})

const tierBgColor = computed(() => {
  const map: Record<string, string> = {
    advanced: '#fef0e6',
    standard: '#ecf5ff',
    basic: '#f0f9eb',
  }
  return map[props.task.model_tier] || '#f0f9eb'
})

const tierTextColor = computed(() => {
  const map: Record<string, string> = {
    advanced: '#e6a23c',
    standard: '#409eff',
    basic: '#67c23a',
  }
  return map[props.task.model_tier] || '#67c23a'
})
</script>

<style scoped>
.flow-node-group {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.flow-node-group:hover .node-bg {
  filter: brightness(0.97);
}

.node-shadow {
  fill: rgba(0, 0, 0, 0.06);
  transform: translate(2px, 3px);
}

.node-bg {
  fill: #ffffff;
  stroke: #e4e7ed;
  stroke-width: 2;
  transition: all 0.3s ease;
}

.node-bg.status-completed {
  stroke: #67c23a;
  stroke-width: 2;
}

.node-bg.status-running {
  stroke: #409eff;
  stroke-width: 2;
  animation: pulse-border 2s ease-in-out infinite;
}

.node-bg.status-pending {
  stroke: #c0c4cc;
}

.node-bg.status-failed {
  stroke: #f56c6c;
  stroke-width: 2;
}

@keyframes pulse-border {
  0%, 100% { stroke-opacity: 1; }
  50% { stroke-opacity: 0.5; }
}

.status-icon {
  font-size: 16px;
}

.node-title {
  font-size: 14px;
  font-weight: 600;
  fill: #303133;
}

.node-agent {
  font-size: 12px;
  fill: #606266;
}

.tier-text {
  font-size: 11px;
  font-weight: 500;
}

.node-duration {
  font-size: 11px;
  fill: #909399;
}

.selection-ring {
  fill: none;
  stroke: #409eff;
  stroke-width: 2;
  stroke-dasharray: 6 3;
  animation: dash-rotate 1s linear infinite;
}

@keyframes dash-rotate {
  to {
    stroke-dashoffset: -9;
  }
}
</style>

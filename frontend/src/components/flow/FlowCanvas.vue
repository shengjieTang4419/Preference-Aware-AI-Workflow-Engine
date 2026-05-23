<template>
  <div class="flow-canvas-wrapper" ref="wrapperRef">
    <svg
      ref="svgRef"
      class="flow-canvas"
      :width="svgWidth"
      :height="svgHeight"
      :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
    >
      <!-- Arrowhead marker definition -->
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#909399" />
        </marker>
        <marker
          id="arrowhead-green"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#67c23a" />
        </marker>
        <marker
          id="arrowhead-blue"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
          markerUnits="strokeWidth"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#409eff" />
        </marker>
      </defs>

      <!-- Background grid pattern -->
      <defs>
        <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
          <circle cx="15" cy="15" r="0.8" fill="#e8e8e8" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />

      <!-- Process type badge -->
      <g :transform="`translate(${svgWidth / 2}, 30)`">
        <rect x="-80" y="-14" width="160" height="28" rx="14" fill="#f0f2f5" />
        <text class="process-label" text-anchor="middle" dominant-baseline="central">
          {{ processTypeLabel }}
        </text>
      </g>

      <!-- Start node -->
      <g
        :transform="`translate(${startNodeX}, ${centerY})`"
        class="start-node"
      >
        <circle r="32" fill="url(#start-gradient)" />
        <defs>
          <linearGradient id="start-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#667eea" />
            <stop offset="100%" stop-color="#764ba2" />
          </linearGradient>
        </defs>
        <text class="start-icon" text-anchor="middle" dominant-baseline="central" y="-2">📝</text>
        <text class="start-label" text-anchor="middle" y="50">用户输入</text>
      </g>

      <!-- Edges (drawn before nodes so nodes appear on top) -->
      <FlowEdge
        v-for="(edge, i) in computedEdges"
        :key="'edge-' + i"
        :sourceX="edge.sourceX"
        :sourceY="edge.sourceY"
        :targetX="edge.targetX"
        :targetY="edge.targetY"
        :sourceStatus="edge.sourceStatus"
        :targetStatus="edge.targetStatus"
        :isSequential="flowData.crew.process_type === 'sequential'"
      />

      <!-- Edge from start to first tasks -->
      <FlowEdge
        v-for="(taskId, i) in firstTaskIds"
        :key="'start-edge-' + i"
        :sourceX="startNodeX + 32"
        :sourceY="centerY"
        :targetX="getTaskX(taskId) - nodeWidth / 2"
        :targetY="getTaskY(taskId)"
        sourceStatus="completed"
        :targetStatus="getTaskStatus(taskId)"
        :isSequential="true"
      />

      <!-- Edge from last tasks to end node -->
      <FlowEdge
        v-for="(taskId, i) in lastTaskIds"
        :key="'end-edge-' + i"
        :sourceX="getTaskX(taskId) + nodeWidth / 2"
        :sourceY="getTaskY(taskId)"
        :targetX="endNodeX - 32"
        :targetY="centerY"
        :sourceStatus="getTaskStatus(taskId)"
        :targetStatus="endNodeStatus"
        :isSequential="true"
      />

      <!-- Task nodes -->
      <FlowNode
        v-for="task in flowData.tasks"
        :key="task.id"
        :task="task"
        :x="getTaskX(task.id)"
        :y="getTaskY(task.id)"
        :isSelected="selectedTaskId === task.id"
        @select="handleSelect"
      />

      <!-- End node -->
      <g
        :transform="`translate(${endNodeX}, ${centerY})`"
        class="end-node"
      >
        <circle r="32" :fill="endNodeColor" />
        <text class="end-icon" text-anchor="middle" dominant-baseline="central" y="-2">📦</text>
        <text class="end-label" text-anchor="middle" y="50">输出结果</text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { FlowData } from '@/api'
import FlowNode from './FlowNode.vue'
import FlowEdge from './FlowEdge.vue'

const props = defineProps<{
  flowData: FlowData
  selectedTaskId: string | null
}>()

const emit = defineEmits<{
  select: [id: string]
}>()

const wrapperRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)

const nodeWidth = 220
const nodeGap = 80
const paddingX = 100
const paddingY = 60

// Calculate positions
const taskPositions = computed(() => {
  const tasks = props.flowData.tasks
  const processType = props.flowData.crew.process_type
  const positions: Record<string, { x: number; y: number }> = {}

  if (processType === 'sequential') {
    // Left to right in order
    tasks.forEach((task, index) => {
      positions[task.id] = {
        x: paddingX + 80 + index * (nodeWidth + nodeGap) + nodeWidth / 2,
        y: paddingY + 80 + nodeWidth / 2,
      }
    })
  } else {
    // Hierarchical: topological sort with layers
    const layers = computeLayers(tasks)
    const layerKeys = Object.keys(layers).sort((a, b) => Number(a) - Number(b))

    layerKeys.forEach((layerKey) => {
      const layer = layers[Number(layerKey)]
      layer.forEach((taskId, indexInLayer) => {
        positions[taskId] = {
          x: paddingX + 80 + Number(layerKey) * (nodeWidth + nodeGap) + nodeWidth / 2,
          y: paddingY + 80 + indexInLayer * (140) + nodeWidth / 2,
        }
      })
    })
  }

  return positions
})

function computeLayers(tasks: FlowData['tasks']): Record<number, string[]> {
  const layers: Record<number, string[]> = {}
  const taskMap = new Map(tasks.map(t => [t.id, t]))
  const assigned = new Set<string>()

  function getLayer(taskId: string): number {
    if (assigned.has(taskId)) {
      // Find which layer it's in
      for (const [k, v] of Object.entries(layers)) {
        if (v.includes(taskId)) return Number(k)
      }
      return 0
    }
    const task = taskMap.get(taskId)
    if (!task || task.context_task_ids.length === 0) return 0

    let maxDep = -1
    for (const depId of task.context_task_ids) {
      if (taskMap.has(depId)) {
        maxDep = Math.max(maxDep, getLayer(depId))
      }
    }
    return maxDep + 1
  }

  // Assign layers
  for (const task of tasks) {
    const layer = getLayer(task.id)
    if (!layers[layer]) layers[layer] = []
    layers[layer].push(task.id)
    assigned.add(task.id)
  }

  return layers
}

// SVG dimensions
const svgWidth = computed(() => {
  const tasks = props.flowData.tasks
  if (tasks.length === 0) return 600
  const maxX = Math.max(...Object.values(taskPositions.value).map(p => p.x))
  return maxX + paddingX + 200
})

const svgHeight = computed(() => {
  const tasks = props.flowData.tasks
  if (tasks.length === 0) return 300
  const maxY = Math.max(...Object.values(taskPositions.value).map(p => p.y))
  return Math.max(maxY + paddingY + 80, 300)
})

const centerY = computed(() => {
  return svgHeight.value / 2
})

const startNodeX = computed(() => 50)
const endNodeX = computed(() => svgWidth.value - 50)

const processTypeLabel = computed(() => {
  const map: Record<string, string> = {
    sequential: '📌 顺序执行模式',
    hierarchical: '🌳 层级执行模式',
  }
  return map[props.flowData.crew.process_type] || '📌 执行模式'
})

// Find first tasks (no dependencies)
const firstTaskIds = computed(() => {
  return props.flowData.tasks
    .filter(t => t.context_task_ids.length === 0)
    .map(t => t.id)
})

// Find last tasks (not depended on by any other task)
const lastTaskIds = computed(() => {
  const depTargets = new Set(props.flowData.edges.map(e => e.target))
  return props.flowData.tasks
    .filter(t => !depTargets.has(t.id))
    .map(t => t.id)
})

const endNodeStatus = computed(() => {
  const execStatus = props.flowData.execution.status
  if (execStatus === 'completed') return 'completed'
  if (execStatus === 'failed') return 'failed'
  return 'pending'
})

const endNodeColor = computed(() => {
  const s = endNodeStatus.value
  if (s === 'completed') return '#67c23a'
  if (s === 'failed') return '#f56c6c'
  return '#c0c4cc'
})

// Compute edges with positions
const computedEdges = computed(() => {
  return props.flowData.edges.map(edge => {
    const srcPos = taskPositions.value[edge.source]
    const tgtPos = taskPositions.value[edge.target]
    if (!srcPos || !tgtPos) return null

    const srcTask = props.flowData.tasks.find(t => t.id === edge.source)
    const tgtTask = props.flowData.tasks.find(t => t.id === edge.target)

    return {
      sourceX: srcPos.x + nodeWidth / 2,
      sourceY: srcPos.y,
      targetX: tgtPos.x - nodeWidth / 2,
      targetY: tgtPos.y,
      sourceStatus: srcTask?.status || 'pending',
      targetStatus: tgtTask?.status || 'pending',
    }
  }).filter(Boolean) as Array<{
    sourceX: number
    sourceY: number
    targetX: number
    targetY: number
    sourceStatus: string
    targetStatus: string
  }>
})

function getTaskX(taskId: string): number {
  return taskPositions.value[taskId]?.x ?? 0
}

function getTaskY(taskId: string): number {
  return taskPositions.value[taskId]?.y ?? 0
}

function getTaskStatus(taskId: string): string {
  return props.flowData.tasks.find(t => t.id === taskId)?.status || 'pending'
}

function handleSelect(id: string) {
  emit('select', id)
}
</script>

<style scoped>
.flow-canvas-wrapper {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 8px;
  background: #fafbfc;
  border-radius: 12px;
}

.flow-canvas {
  display: block;
  min-width: 100%;
}

.process-label {
  font-size: 13px;
  fill: #606266;
  font-weight: 500;
}

.start-icon, .end-icon {
  font-size: 20px;
}

.start-label, .end-label {
  font-size: 12px;
  fill: #606266;
  font-weight: 500;
}

.start-node, .end-node {
  cursor: default;
}
</style>

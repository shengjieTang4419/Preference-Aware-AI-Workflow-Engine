<template>
  <g class="flow-edge-group">
    <!-- Edge path -->
    <path
      :d="pathData"
      class="edge-path"
      :class="edgeStatus"
      fill="none"
      :stroke="strokeColor"
      :stroke-width="2"
      marker-end="url(#arrowhead)"
    />
    <!-- Animated dot for running edges -->
    <circle
      v-if="edgeStatus === 'active'"
      r="4"
      :fill="strokeColor"
      class="animated-dot"
    >
      <animateMotion
        :dur="animDuration"
        repeatCount="indefinite"
        :path="pathData"
      />
    </circle>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  sourceX: number
  sourceY: number
  targetX: number
  targetY: number
  sourceStatus: string
  targetStatus: string
  isSequential: boolean
}>()

const edgeStatus = computed(() => {
  if (props.sourceStatus === 'completed' && props.targetStatus === 'completed') return 'completed'
  if (props.sourceStatus === 'completed' && props.targetStatus === 'running') return 'active'
  if (props.sourceStatus === 'completed' && props.targetStatus === 'pending') return 'ready'
  return 'pending'
})

const strokeColor = computed(() => {
  const map: Record<string, string> = {
    completed: '#67c23a',
    active: '#409eff',
    ready: '#b3d8ff',
    pending: '#dcdfe6',
  }
  return map[edgeStatus.value] || '#dcdfe6'
})

const animDuration = computed(() => '2s')

const pathData = computed(() => {
  const sx = props.sourceX
  const sy = props.sourceY
  const tx = props.targetX
  const ty = props.targetY

  if (props.isSequential) {
    // Straight horizontal line with slight curve
    const midX = (sx + tx) / 2
    return `M ${sx} ${sy} C ${midX} ${sy}, ${midX} ${ty}, ${tx} ${ty}`
  } else {
    // Curved path for hierarchical
    const dx = tx - sx
    const dy = ty - sy
    const cx1 = sx + dx * 0.4
    const cy1 = sy
    const cx2 = tx - dx * 0.4
    const cy2 = ty
    return `M ${sx} ${sy} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${tx} ${ty}`
  }
})
</script>

<style scoped>
.edge-path {
  transition: stroke 0.3s ease, stroke-width 0.3s ease;
}

.edge-path.completed {
  stroke-width: 2.5;
}

.edge-path.active {
  stroke-width: 2.5;
}

.edge-path.pending {
  stroke-dasharray: 6 4;
}

.animated-dot {
  filter: drop-shadow(0 0 3px rgba(64, 158, 255, 0.6));
}
</style>

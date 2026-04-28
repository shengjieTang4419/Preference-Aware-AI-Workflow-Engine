<template>
  <div class="markdown-body" v-html="rendered" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{
  content: string
}>()

const rendered = computed(() => {
  if (!props.content) return ''
  try {
    return marked(props.content)
  } catch {
    return props.content
  }
})
</script>

<style scoped>
.markdown-body {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #e1e4e8;
  font-size: 14px;
  line-height: 1.6;
}

:deep(h1) {
  font-size: 2em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 24px;
  margin-bottom: 16px;
}

:deep(h2) {
  font-size: 1.5em;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 24px;
  margin-bottom: 16px;
}

:deep(h3) {
  font-size: 1.25em;
  margin-top: 24px;
  margin-bottom: 16px;
}

:deep(p) {
  margin-top: 0;
  margin-bottom: 16px;
}

:deep(ul),
:deep(ol) {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
}

:deep(li) {
  margin-bottom: 0.25em;
}

:deep(code) {
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-size: 85%;
  margin: 0;
  padding: 0.2em 0.4em;
  font-family: 'Courier New', monospace;
}

:deep(pre) {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  margin-bottom: 16px;
}

:deep(pre code) {
  background-color: transparent;
  border: 0;
  display: inline;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
}

:deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  color: #6a737d;
  padding: 0 1em;
  margin: 0 0 16px 0;
}

:deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

:deep(table th),
:deep(table td) {
  border: 1px solid #dfe2e5;
  padding: 6px 13px;
}

:deep(table th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

:deep(table tr:nth-child(2n)) {
  background-color: #f6f8fa;
}

:deep(a) {
  color: #0366d6;
  text-decoration: none;
}

:deep(a:hover) {
  text-decoration: underline;
}

:deep(hr) {
  height: 0.25em;
  padding: 0;
  margin: 24px 0;
  background-color: #e1e4e8;
  border: 0;
}
</style>

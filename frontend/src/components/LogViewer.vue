<template>
  <n-card class="log-viewer-card">
    <template #header>
      <div class="section-title">
        <n-icon :component="TerminalOutline" size="20" />
        实时日志
        <n-tag size="small" round type="info" v-if="logs.length > 0">
          {{ logs.length }} 条
        </n-tag>
      </div>
    </template>
    <template #header-extra>
      <n-button 
        quaternary 
        size="small"
        @click="handleClear"
        :disabled="logs.length === 0"
      >
        清空
      </n-button>
    </template>

    <div class="log-container" ref="logContainerRef">
      <div v-if="logs.length === 0" class="log-empty">
        <n-icon :component="DocumentTextOutline" size="48" color="#64748b" />
        <p>暂无日志，开始压测后将显示实时日志</p>
      </div>
      
      <div 
        v-for="(log, index) in logs" 
        :key="index" 
        :class="['log-line', getLogLevel(log)]"
      >
        <span class="log-prefix">{{ getLogPrefix(index) }}</span>
        <span class="log-content">{{ formatLog(log) }}</span>
      </div>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { TerminalOutline, DocumentTextOutline } from '@vicons/ionicons5'

const props = defineProps<{
  logs: string[]
}>()

const emit = defineEmits<{
  (e: 'clear'): void
}>()

const logContainerRef = ref<HTMLElement | null>(null)

// Auto-scroll to bottom when new logs added
watch(() => props.logs.length, async () => {
  await nextTick()
  if (logContainerRef.value) {
    logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
  }
})

function getLogLevel(log: string): string {
  // Progress lines - running status with VUs and iterations
  if (log.includes('[PROGRESS]') || 
      (log.includes('running') && (log.includes('VUs') || log.includes('VU'))) ||
      (log.includes('default') && log.includes('%'))) {
    return 'progress'
  }
  // K6 metrics output lines
  if (log.includes('http_req_duration') || 
      log.includes('http_reqs') || 
      log.includes('iterations') ||
      log.includes('data_received') ||
      log.includes('vus_max')) {
    return 'metric'
  }
  if (log.includes('[ERROR]') || log.includes('error') || log.includes('failed')) {
    return 'error'
  }
  if (log.includes('[WARN]') || log.includes('warning')) {
    return 'warning'
  }
  if (log.includes('[INFO]') || log.includes('Starting') || log.includes('Generated')) {
    return 'info'
  }
  if (log.includes('✓') || log.includes('success') || log.includes('completed')) {
    return 'success'
  }
  return ''
}

function getLogPrefix(index: number): string {
  const num = (index + 1).toString().padStart(3, '0')
  return `[${num}]`
}

function formatLog(log: string): string {
  // Remove [PROGRESS] prefix for display
  return log.replace('[PROGRESS] ', '')
}

function handleClear() {
  // Parent should handle this by clearing the logs array
  emit('clear')
}
</script>

<style scoped>
.log-viewer-card {
  background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.125rem;
  font-weight: 600;
  color: #e2e8f0;
}

.log-container {
  background: #0a0a14;
  border-radius: 8px;
  padding: 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.8125rem;
  line-height: 1.8;
  max-height: 350px;
  min-height: 200px;
  overflow-y: auto;
  border: 1px solid rgba(148, 163, 184, 0.15);
}

.log-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: #64748b;
  gap: 12px;
}

.log-empty p {
  font-size: 0.875rem;
}

.log-line {
  padding: 2px 0;
  display: flex;
  gap: 8px;
  word-break: break-all;
}

.log-prefix {
  color: #64748b;
  flex-shrink: 0;
}

.log-content {
  color: #e2e8f0;
}

.log-line.info .log-content {
  color: #3b82f6;
}

.log-line.success .log-content {
  color: #10b981;
}

.log-line.warning .log-content {
  color: #f59e0b;
}

.log-line.error .log-content {
  color: #ef4444;
}

/* Progress lines - K6 running status */
.log-line.progress {
  background: rgba(139, 92, 246, 0.1);
  border-left: 3px solid #8b5cf6;
  padding-left: 8px;
  margin-left: -11px;
}

.log-line.progress .log-content {
  color: #a78bfa;
  font-weight: 600;
}

.log-line.progress .log-prefix {
  color: #8b5cf6;
}

/* Metric lines - K6 metrics output */
.log-line.metric {
  background: rgba(14, 165, 233, 0.08);
}

.log-line.metric .log-content {
  color: #0ea5e9;
}

/* Scrollbar for log container */
.log-container::-webkit-scrollbar {
  width: 6px;
}

.log-container::-webkit-scrollbar-track {
  background: transparent;
}

.log-container::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.log-container::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>

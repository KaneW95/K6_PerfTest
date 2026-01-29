<template>
  <n-card class="execution-panel">
    <div class="panel-header">
      <div class="status-info">
        <span class="status-label">状态：</span>
        <span :class="['status-badge', status]">
          <span v-if="status === 'running'" class="status-dot animate-pulse"></span>
          {{ statusText }}
        </span>
      </div>
      
      <div class="execution-info" v-if="executionId">
        <n-tag size="small" round>
          执行ID: {{ executionId }}
        </n-tag>
      </div>
    </div>

    <div class="panel-actions" v-if="status === 'running'">
      <n-button 
        type="error" 
        size="small"
        @click="$emit('stop-test')"
      >
        <template #icon>
          <n-icon :component="StopOutline" />
        </template>
        停止测试
      </n-button>
    </div>

    <!-- Progress Animation -->
    <div class="progress-container" v-if="status === 'running'">
      <div class="progress-bar">
        <div class="progress-fill animate-pulse"></div>
      </div>
      <div class="progress-text">测试进行中...</div>
    </div>

    <!-- Completion Status -->
    <div class="completion-status" v-if="status === 'completed'">
      <n-icon :component="CheckmarkCircleOutline" size="48" color="#10b981" />
      <span>测试完成</span>
    </div>

    <div class="completion-status error" v-if="status === 'failed'">
      <n-icon :component="CloseCircleOutline" size="48" color="#ef4444" />
      <span>测试失败</span>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  StopOutline, 
  CheckmarkCircleOutline,
  CloseCircleOutline
} from '@vicons/ionicons5'
import type { TestStatus } from '@/types'

const props = defineProps<{
  status: TestStatus
  executionId: number | null
}>()

defineEmits<{
  (e: 'stop-test'): void
}>()

const statusText = computed(() => {
  const statusMap: Record<TestStatus, string> = {
    idle: '空闲',
    starting: '启动中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
  }
  return statusMap[props.status] || '未知'
})
</script>

<style scoped>
.execution-panel {
  background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 0.875rem;
  color: #94a3b8;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.idle {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.status-badge.starting {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.status-badge.running {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.status-badge.completed {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.panel-actions {
  margin-top: 16px;
}

.progress-container {
  margin-top: 16px;
}

.progress-bar {
  height: 4px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  width: 100%;
  background: linear-gradient(90deg, #7c3aed, #3b82f6, #7c3aed);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

.progress-text {
  margin-top: 8px;
  font-size: 0.75rem;
  color: #94a3b8;
  text-align: center;
}

.completion-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  margin-top: 16px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
  font-weight: 600;
  color: #10b981;
}

.completion-status.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

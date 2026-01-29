<template>
  <n-card class="result-display-card">
    <template #header>
      <div class="section-title">
        <n-icon :component="StatsChartOutline" size="20" />
        压测结果
        <n-tag 
          size="small" 
          round 
          :type="status === 'completed' ? 'success' : 'error'"
        >
          {{ status === 'completed' ? '成功' : '失败' }}
        </n-tag>
      </div>
    </template>

    <div class="result-content" v-if="result">
      <!-- Summary Cards -->
      <div class="result-grid">
        <div class="result-card">
          <div class="label">总请求数</div>
          <div class="value">{{ formatNumber(getTotalRequests()) }}</div>
        </div>
        
        <div class="result-card success">
          <div class="label">成功率</div>
          <div class="value">{{ getSuccessRate() }}%</div>
        </div>
        
        <div class="result-card" :class="{ error: getFailedRequests() > 0 }">
          <div class="label">错误请求数</div>
          <div class="value">{{ formatNumber(getFailedRequests()) }}</div>
        </div>
        
        <div class="result-card">
          <div class="label">平均响应时间</div>
          <div class="value">{{ formatDuration(getAvgDuration()) }}</div>
        </div>
        
        <div class="result-card">
          <div class="label">P95 响应时间</div>
          <div class="value">{{ formatDuration(getP95Duration()) }}</div>
        </div>
        
        <div class="result-card">
          <div class="label">平均 RPS</div>
          <div class="value">{{ getAvgRPS() }}</div>
        </div>
        
        <div class="result-card">
          <div class="label">最大 RPS</div>
          <div class="value">{{ getMaxRPS() }}</div>
        </div>
      </div>


    </div>

    <div v-else class="no-result">
      <n-icon :component="BarChartOutline" size="48" color="#64748b" />
      <p>暂无结果数据</p>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { StatsChartOutline, BarChartOutline } from '@vicons/ionicons5'
import type { TestStatus, TestResultSummary } from '@/types'

const props = defineProps<{
  result: TestResultSummary | null
  status: TestStatus
}>()

// Helper functions to safely extract metrics
function getTotalRequests(): number {
  if (!props.result) return 0
  
  // Check various possible structures
  if (typeof props.result.http_reqs === 'number') {
    return props.result.http_reqs
  }
  if (props.result.metrics?.http_reqs?.values?.count) {
    return props.result.metrics.http_reqs.values.count
  }
  return 0
}

function getSuccessRate(): string {
  if (!props.result) return '0'
  
  const total = getTotalRequests()
  if (total === 0) return '100'
  
  let failed = 0
  if (typeof props.result.http_req_failed === 'number') {
    failed = props.result.http_req_failed
  } else if (props.result.metrics?.http_req_failed?.values?.count) {
    failed = props.result.metrics.http_req_failed.values.count
  }
  
  const rate = ((total - failed) / total) * 100
  return rate.toFixed(2)
}

function getAvgDuration(): number {
  if (!props.result) return 0
  
  if (props.result.http_req_duration?.avg) {
    return props.result.http_req_duration.avg
  }
  if (props.result.metrics?.http_req_duration?.values?.avg) {
    return props.result.metrics.http_req_duration.values.avg
  }
  return 0
}

function getP95Duration(): number {
  if (!props.result) return 0
  
  if (props.result.http_req_duration?.p95) {
    return props.result.http_req_duration.p95
  }
  if (props.result.metrics?.http_req_duration?.values?.['p(95)']) {
    return props.result.metrics.http_req_duration.values['p(95)']
  }
  return 0
}



function getFailedRequests(): number {
  if (!props.result) return 0
  
  if (typeof props.result.http_req_failed === 'number') {
    return props.result.http_req_failed
  } else if (props.result.metrics?.http_req_failed?.values?.count) {
    return props.result.metrics.http_req_failed.values.count
  }
  return 0
}



function getAvgRPS(): string {
  if (!props.result) return '0'
  
  if (typeof props.result.rps === 'number') {
    return props.result.rps.toFixed(2)
  }
  
  // Get RPS from http_reqs metric rate
  if (props.result.metrics?.http_reqs?.values?.rate) {
    return props.result.metrics.http_reqs.values.rate.toFixed(2)
  }
  
  // Calculate from total requests and duration if available
  const total = getTotalRequests()
  if (total > 0 && props.result.duration) {
    const durationSec = props.result.duration / 1000
    if (durationSec > 0) {
      return (total / durationSec).toFixed(2)
    }
  }
  
  return '0'
}

function getMaxRPS(): string {
  if (!props.result) return '0'
  
  if (typeof props.result.rps_max === 'number') {
    return props.result.rps_max.toFixed(2)
  }
  
  // Fallback to average/estimated logic
  if (props.result.metrics?.http_reqs?.values?.rate) {
    const avgRps = props.result.metrics.http_reqs.values.rate
    return avgRps.toFixed(2)
  }
  
  return getAvgRPS()
}



function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(2) + 'K'
  }
  return num.toString()
}

function formatDuration(ms: number | undefined): string {
  if (ms === undefined || ms === null) return '-'
  if (ms === 0) return '0 ms'
  
  if (ms < 1) {
    return (ms * 1000).toFixed(2) + 'μs'
  }
  if (ms < 1000) {
    return ms.toFixed(2) + 'ms'
  }
  return (ms / 1000).toFixed(2) + 's'
}
</script>

<style scoped>
.result-display-card {
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

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.result-card {
  background: linear-gradient(135deg, rgba(22, 33, 62, 0.8) 0%, rgba(26, 26, 46, 0.8) 100%);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
  border-color: rgba(124, 58, 237, 0.5);
}

.result-card .label {
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.result-card .value {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.result-card.success .value {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.result-card.error .value {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.result-card.error {
  border-color: rgba(239, 68, 68, 0.4);
}

.metrics-table {
  margin-top: 8px;
}

:deep(.n-table th) {
  background: rgba(26, 26, 46, 0.5) !important;
  color: #94a3b8;
  font-weight: 600;
}

:deep(.n-table td) {
  color: #e2e8f0;
}

.no-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: #64748b;
  gap: 12px;
}

.no-result p {
  font-size: 0.875rem;
}

:deep(.n-divider) {
  margin: 20px 0 16px;
}

:deep(.n-divider .n-divider__title) {
  font-weight: 600;
  color: #94a3b8;
}
</style>

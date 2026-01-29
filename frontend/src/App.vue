<template>
  <n-config-provider :theme="darkTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-notification-provider>
        <div class="app-container">
          <!-- Header -->
          <header class="header">
            <div class="header-left">
              <h1>⚡ K6 接口压测平台</h1>
              <span class="version-badge">v1.0.0</span>
            </div>
            <div class="header-right">
              <n-tag :type="connectionStatus === 'connected' ? 'success' : 'error'" round>
                {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
              </n-tag>
            </div>
          </header>

          <!-- Main Content -->
          <main class="main-container">
            <!-- Left Column: Configuration -->
            <div class="left-column">
              <ConfigForm 
                ref="configFormRef"
                :loading="testStatus === 'running'" 
                @run-test="handleRunTest"
              />
            </div>

            <!-- Right Column: Execution & Results -->
            <div class="right-column">
              <!-- Action Buttons -->
              <div class="action-buttons">
                <n-button 
                  type="primary" 
                  size="large"
                  :loading="testStatus === 'running'"
                  :disabled="testStatus === 'running'"
                  @click="handleStartTest"
                >
                  <template #icon>
                    <n-icon :component="PlayOutline" />
                  </template>
                  开始压测
                </n-button>
                <n-button 
                  size="large"
                  :disabled="testStatus === 'running'"
                  @click="handlePreviewScript"
                >
                  <template #icon>
                    <n-icon :component="CodeOutline" />
                  </template>
                  脚本预览
                </n-button>
              </div>

              <!-- Execution Panel -->
              <ExecutionPanel 
                :status="testStatus"
                :execution-id="currentExecutionId"
                @stop-test="handleStopTest"
              />

              <!-- Log Viewer -->
              <LogViewer :logs="logs" />

              <!-- Result Display -->
              <ResultDisplay 
                v-if="testResult" 
                :result="testResult"
                :status="testStatus"
              />
            </div>
          </main>
        </div>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { PlayOutline, CodeOutline } from '@vicons/ionicons5'
import ConfigForm from './components/ConfigForm.vue'
import ExecutionPanel from './components/ExecutionPanel.vue'
import LogViewer from './components/LogViewer.vue'
import ResultDisplay from './components/ResultDisplay.vue'
import type { TestConfig, TestStatus, WebSocketMessage, TestResultSummary } from './types'



// Theme customization
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#7c3aed',
    primaryColorHover: '#6d28d9',
    primaryColorPressed: '#5b21b6',
    primaryColorSuppl: '#8b5cf6',
  },
  Card: {
    color: '#16213e',
  },
  Input: {
    color: '#1a1a2e',
    borderColor: 'rgba(148, 163, 184, 0.3)',
  },
  Select: {
    peers: {
      InternalSelection: {
        color: '#1a1a2e',
        borderColor: 'rgba(148, 163, 184, 0.3)',
      },
    },
  },
}

// State
const configFormRef = ref<InstanceType<typeof ConfigForm> | null>(null)
const testStatus = ref<TestStatus>('idle')
const connectionStatus = ref<'connected' | 'disconnected'>('disconnected')
const currentExecutionId = ref<number | null>(null)
const logs = ref<string[]>([])
const testResult = ref<TestResultSummary | null>(null)

// WebSocket
let ws: WebSocket | null = null

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/api/ws/test`)

  ws.onopen = () => {
    connectionStatus.value = 'connected'
    console.log('WebSocket connected')
  }

  ws.onclose = () => {
    connectionStatus.value = 'disconnected'
    console.log('WebSocket disconnected')
    // Reconnect after 3 seconds
    setTimeout(connectWebSocket, 3000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  ws.onmessage = (event) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      handleWebSocketMessage(message)
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }
}

function handleWebSocketMessage(message: WebSocketMessage) {
  switch (message.type) {
    case 'log':
      if (message.message) {
        logs.value.push(message.message)
        if (logs.value.length > 500) logs.value.shift()
      }
      break
    case 'status':
      if (message.status) {
        testStatus.value = message.status as TestStatus
      }
      break
    case 'result':
      if (message.data) {
        testResult.value = message.data.summary || message.data
      }
      break
    case 'execution_started':
      if (message.execution_id) {
        currentExecutionId.value = message.execution_id
      }
      break
    case 'error':
      logs.value.push(`[ERROR] ${message.message}`)
      if (logs.value.length > 500) logs.value.shift()
      testStatus.value = 'failed'
      break
    case 'info':
      if (message.message) {
        logs.value.push(`[INFO] ${message.message}`)
        if (logs.value.length > 500) logs.value.shift()
      }
      break
  }
}

function handleRunTest(config: TestConfig) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.error('WebSocket not connected')
    return
  }

  // Reset state
  logs.value = []
  testResult.value = null
  testStatus.value = 'starting'
  currentExecutionId.value = null

  // Convert headers from object to array format for backend
  const headersArray = Object.entries(config.headers || {}).map(([key, value]) => ({ key, value }))

  // Build request config based on two-level load mode
  const requestConfig: any = {
    name: config.name,
    url: config.url,
    method: config.method,
    headers: headersArray,
    body: config.body || null,
    loadCategory: config.loadCategory,
    loadSubMode: config.loadSubMode,
    thresholds: config.thresholds.filter(t => t.metric && t.condition),
    stopOnFailure: config.stopOnFailure,
    dataFile: config.dataFile,
  }

  // Add mode-specific config based on two-level structure
  if (config.loadCategory === 'vus') {
    if (config.loadSubMode === 'simple') {
      requestConfig.vus = config.vus
      requestConfig.duration = config.duration
    } else {
      requestConfig.stages = config.stages.filter(s => s.duration && s.target > 0)
    }
  } else {
    // RPS mode
    requestConfig.preAllocatedVUs = config.preAllocatedVUs
    requestConfig.maxVUs = config.maxVUs
    if (config.loadSubMode === 'simple') {
      requestConfig.rps = config.rps
      requestConfig.duration = config.duration
    } else {
      requestConfig.rpsStages = config.rpsStages.filter(s => s.duration && s.target > 0)
    }
  }

  // Send run command
  ws.send(JSON.stringify({
    action: 'run',
    config: requestConfig,
  }))
}

function handleStopTest() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'stop' }))
  }
}

function handleStartTest() {
  if (configFormRef.value) {
    configFormRef.value.handleSubmit()
  }
}

function handlePreviewScript() {
  if (configFormRef.value) {
    configFormRef.value.handlePreviewScript()
  }
}

onMounted(() => {
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h1 {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.version-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  background: rgba(124, 58, 237, 0.2);
  color: #a78bfa;
  border-radius: 12px;
}

.main-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 24px 60px;
  flex: 1;
}

@media (max-width: 1200px) {
  .main-container {
    grid-template-columns: 1fr;
  }
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}
</style>

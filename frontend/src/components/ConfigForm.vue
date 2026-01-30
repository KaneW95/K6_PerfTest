<template>
  <n-card class="config-form-card">
    <template #header>
      <div class="section-title">
        <n-icon :component="SettingsOutline" size="20" />
        压测配置
      </div>
    </template>
    <template #header-extra>
      <n-button size="small" @click="showCurlImport = true" :disabled="loading">
        <template #icon><n-icon :component="CodeSlashOutline" /></template>
        导入cURL
      </n-button>
    </template>

    <n-form ref="formRef" :model="formData" :rules="rules" label-placement="top">
      <!-- Basic Info -->
      <n-divider title-placement="left">基本信息</n-divider>
      
      <n-form-item label="配置名称" path="name">
        <n-input 
          v-model:value="formData.name" 
          placeholder="请输入配置名称"
          :disabled="loading"
        />
      </n-form-item>

      <n-grid :cols="24" :x-gap="16">
        <n-grid-item :span="6">
          <n-form-item label="请求方法" path="method">
            <n-select 
              v-model:value="formData.method"
              :options="methodOptions"
              :disabled="loading"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item :span="18">
          <n-form-item label="请求URL" path="url">
            <n-input-group>
              <n-input 
                v-model:value="formData.url" 
                placeholder="https://api.example.com/endpoint"
                :disabled="loading"
              />
              <n-button type="primary" :disabled="loading || !formData.url" @click="handleDebugRequest">
                调试
              </n-button>
            </n-input-group>
          </n-form-item>
        </n-grid-item>
      </n-grid>

      <!-- Headers (JSON) -->
      <n-form-item label="请求头 (JSON格式)">
        <n-input
          v-model:value="headersJson"
          type="textarea"
          placeholder='{"Content-Type": "application/json", "Authorization": "Bearer xxx"}'
          :autosize="{ minRows: 2, maxRows: 6 }"
          :disabled="loading"
          :status="headersJsonError ? 'error' : undefined"
        />
        <template #feedback>
          <span v-if="headersJsonError" style="color: #ef4444;">{{ headersJsonError }}</span>
        </template>
      </n-form-item>

      <!-- Request Body -->
      <n-form-item label="请求体 (JSON)" v-if="['POST', 'PUT', 'PATCH'].includes(formData.method)">
        <n-input
          v-model:value="formData.body"
          type="textarea"
          placeholder='{"key": "value"}'
          :autosize="{ minRows: 3, maxRows: 8 }"
          :disabled="loading"
          :status="bodyJsonError ? 'error' : undefined"
          @blur="formatBody"
        />
        <template #feedback>
          <span v-if="bodyJsonError" style="color: #ef4444;">{{ bodyJsonError }}</span>
        </template>
      </n-form-item>

      <!-- Data Configuration -->
      <n-divider title-placement="left">数据配置 (可选)</n-divider>
      <n-form-item label="上传数据文件 (CSV)">
        <n-upload
          action="/api/upload/data"
          :max="1"
          name="file"
          response-type="json"
          @finish="handleUploadFinish"
          @error="handleUploadError"
          :show-file-list="true"
        >
          <n-button :disabled="loading">上传 CSV 文件</n-button>
        </n-upload>
      </n-form-item>
      <!-- Initial Spacer not working in form item context well, use simple margin -->
      <n-form-item>
         <n-button @click="downloadTemplate" size="small">
            <template #icon><n-icon :component="CloudDownloadOutline" /></template>
            下载 CSV 模板
         </n-button>
      </n-form-item>
      <n-alert type="info" v-if="formData.dataFile" :bordered="false" closable @close="formData.dataFile = undefined">
        已关联数据文件: {{ formData.dataFile }}
        <br>
        <span style="font-size: 0.9em; opacity: 0.8">
          提示：在请求体中使用 <span v-pre>{{ column_name }}</span> 引用 CSV 列数据。
        </span>
      </n-alert>


      <!-- Performance Metrics -->
      <n-divider title-placement="left">压测指标</n-divider>

      <!-- Load Mode Selection - Level 1: Category -->
      <n-form-item label="一级模式">
        <n-radio-group v-model:value="formData.loadCategory" :disabled="loading">
          <n-radio-button value="vus">
            <n-space align="center" :size="4">
              <span>🧑‍💻</span>
              <span>并发用户 (VUs)</span>
            </n-space>
          </n-radio-button>
          <n-radio-button value="rps">
            <n-space align="center" :size="4">
              <span>⚡</span>
              <span>吞吐量 (RPS)</span>
            </n-space>
          </n-radio-button>
        </n-radio-group>
      </n-form-item>

      <!-- Load Mode Selection - Level 2: Sub Mode -->
      <n-form-item label="二级模式">
        <n-radio-group v-model:value="formData.loadSubMode" :disabled="loading">
          <n-radio-button value="simple">简单模式</n-radio-button>
          <n-radio-button value="stages">阶梯模式</n-radio-button>
        </n-radio-group>
      </n-form-item>

      <!-- VU Simple Mode -->
      <template v-if="formData.loadCategory === 'vus' && formData.loadSubMode === 'simple'">
        <n-grid :cols="24" :x-gap="16">
          <n-grid-item :span="12">
            <n-form-item label="虚拟用户数 (VUs)" path="vus">
              <n-input-number 
                v-model:value="formData.vus" 
                :min="1" 
                :max="100000"
                placeholder="10"
                :disabled="loading"
                style="width: 100%"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="12">
            <n-form-item label="持续时间" path="duration">
              <n-input 
                v-model:value="formData.duration" 
                placeholder="30s / 1m / 5m"
                :disabled="loading"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-alert type="info" :bordered="false">
          VU简单模式：使用固定数量的虚拟用户并发请求
        </n-alert>
      </template>

      <!-- VU Stages Mode -->
      <template v-if="formData.loadCategory === 'vus' && formData.loadSubMode === 'stages'">
        <n-form-item label="VU阶段配置">
          <div class="stages-list">
            <div 
              v-for="(stage, index) in formData.stages" 
              :key="index" 
              class="stage-item"
            >
              <n-input 
                v-model:value="stage.duration" 
                placeholder="持续时间 (如 30s)"
                :disabled="loading"
                style="flex: 1"
              />
              <n-input-number 
                v-model:value="stage.target" 
                :min="0"
                placeholder="目标VU数"
                :disabled="loading"
                style="flex: 1"
              />
              <n-button 
                quaternary 
                circle 
                type="error"
                :disabled="loading"
                @click="removeStage(index)"
              >
                <template #icon>
                  <n-icon :component="CloseOutline" />
                </template>
              </n-button>
            </div>
            <n-button 
              dashed 
              block 
              :disabled="loading"
              @click="addStage"
            >
              <template #icon>
                <n-icon :component="AddOutline" />
              </template>
              添加阶段
            </n-button>
          </div>
        </n-form-item>
        <n-alert type="info" :bordered="false">
          VU阶梯模式：逐步增加/减少虚拟用户数，适合测试系统容量和找到性能拐点
        </n-alert>
      </template>

      <!-- RPS Simple Mode -->
      <template v-if="formData.loadCategory === 'rps' && formData.loadSubMode === 'simple'">
        <n-grid :cols="24" :x-gap="16">
          <n-grid-item :span="12">
            <n-form-item label="目标 RPS (每秒请求数)">
              <n-input-number 
                v-model:value="formData.rps" 
                :min="1" 
                :max="100000"
                placeholder="100"
                :disabled="loading"
                style="width: 100%"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="12">
            <n-form-item label="持续时间">
              <n-input 
                v-model:value="formData.duration" 
                placeholder="30s / 1m / 5m"
                :disabled="loading"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-grid :cols="24" :x-gap="16">
          <n-grid-item :span="12">
            <n-form-item label="预分配 VUs">
              <n-input-number 
                v-model:value="formData.preAllocatedVUs" 
                :min="1" 
                :max="100000"
                placeholder="10"
                :disabled="loading"
                style="width: 100%"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="12">
            <n-form-item label="最大 VUs">
              <n-input-number 
                v-model:value="formData.maxVUs" 
                :min="1" 
                :max="100000"
                placeholder="100"
                :disabled="loading"
                style="width: 100%"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-alert type="info" :bordered="false">
          RPS简单模式：保持恒定的每秒请求数，K6会自动调整VU数量以维持目标RPS
        </n-alert>
      </template>

      <!-- RPS Stages Mode -->
      <template v-if="formData.loadCategory === 'rps' && formData.loadSubMode === 'stages'">
        <n-form-item label="RPS阶段配置">
          <div class="stages-list">
            <div 
              v-for="(stage, index) in formData.rpsStages" 
              :key="index" 
              class="stage-item"
            >
              <n-input 
                v-model:value="stage.duration" 
                placeholder="持续时间 (如 30s)"
                :disabled="loading"
                style="flex: 1"
              />
              <n-input-number 
                v-model:value="stage.target" 
                :min="0"
                placeholder="目标RPS"
                :disabled="loading"
                style="flex: 1"
              />
              <n-button 
                quaternary 
                circle 
                type="error"
                :disabled="loading"
                @click="removeRpsStage(index)"
              >
                <template #icon>
                  <n-icon :component="CloseOutline" />
                </template>
              </n-button>
            </div>
            <n-button 
              dashed 
              block 
              :disabled="loading"
              @click="addRpsStage"
            >
              <template #icon>
                <n-icon :component="AddOutline" />
              </template>
              添加阶段
            </n-button>
          </div>
        </n-form-item>
        <n-grid :cols="24" :x-gap="16">
          <n-grid-item :span="12">
            <n-form-item label="预分配 VUs">
              <n-input-number 
                v-model:value="formData.preAllocatedVUs" 
                :min="1" 
                :max="100000"
                placeholder="10"
                :disabled="loading"
                style="width: 100%"
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item :span="12">
            <n-form-item label="最大 VUs">
              <n-input-number 
                v-model:value="formData.maxVUs" 
                :min="1" 
                :max="100000"
                placeholder="100"
                :disabled="loading"
                style="width: 100%"
              />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-alert type="info" :bordered="false">
          RPS阶梯模式：逐步增加/减少每秒请求数，适合测试系统吞吐量极限
        </n-alert>
      </template>


      
      <!-- Execution Control -->
      <n-divider title-placement="left">执行控制</n-divider>
      <n-form-item>
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-checkbox v-model:checked="formData.stopOnFailure" :disabled="loading">
              遇到错误立即停止 (Stop on Failure)
            </n-checkbox>
          </template>
          开启后，如果请求返回非 2xx 状态码，压测将立即终止
        </n-tooltip>
      </n-form-item>

      <!-- Thresholds -->
      <n-divider title-placement="left">阈值配置</n-divider>
      
      <div class="thresholds-list">
        <div 
          v-for="(threshold, index) in formData.thresholds" 
          :key="index" 
          class="threshold-item"
        >
          <n-select 
            v-model:value="threshold.metric" 
            :options="metricOptions"
            placeholder="指标"
            :disabled="loading"
            style="flex: 1"
          />
          <n-input 
            v-model:value="threshold.condition" 
            placeholder="条件 (如 p(95)<500)"
            :disabled="loading"
            style="flex: 1"
          />
          <n-button 
            quaternary 
            circle 
            type="error"
            :disabled="loading"
            @click="removeThreshold(index)"
          >
            <template #icon>
              <n-icon :component="CloseOutline" />
            </template>
          </n-button>
        </div>
        <n-button 
          dashed 
          block 
          :disabled="loading"
          @click="addThreshold"
        >
          <template #icon>
            <n-icon :component="AddOutline" />
          </template>
          添加阈值
        </n-button>
      </div>


    </n-form>

    <!-- cURL Import Modal -->
    <n-modal v-model:show="showCurlImport" preset="dialog" title="导入 cURL 命令">
      <n-input
        v-model:value="curlInput"
        type="textarea"
        placeholder="粘贴 cURL 命令..."
        :autosize="{ minRows: 5, maxRows: 15 }"
      />
      <template #action>
        <n-button @click="showCurlImport = false">取消</n-button>
        <n-button type="primary" @click="handleImportCurl">导入</n-button>
      </template>
    </n-modal>

    <!-- Script Preview Modal -->
    <n-modal v-model:show="showScriptPreview" preset="card" title="K6 脚本预览" style="width: 800px; max-width: 90vw;">
      <n-code :code="previewScript" language="javascript" show-line-numbers word-wrap />
      <template #footer>
        <n-space justify="end">
          <n-button @click="handleCopyScript">
            <template #icon><n-icon :component="CopyOutline" /></template>
            复制脚本
          </n-button>
          <n-button type="primary" @click="showScriptPreview = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- Debug Result Modal -->
    <n-modal v-model:show="showDebugResult" preset="card" title="接口调试结果" style="width: 700px; max-width: 90vw;">
      <n-spin :show="debugLoading">
        <div v-if="debugResult">
          <n-descriptions :column="2" label-placement="left" bordered>
            <n-descriptions-item label="状态码">
              <n-tag :type="debugResult.status < 400 ? 'success' : 'error'">
                {{ debugResult.status }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="耗时">
              {{ debugResult.duration }}ms
            </n-descriptions-item>
          </n-descriptions>
          <n-divider>响应头</n-divider>
          <n-code :code="JSON.stringify(debugResult.headers, null, 2)" language="json" word-wrap />
          <n-divider>响应体</n-divider>
          <n-code :code="formatResponseBody(debugResult.body)" language="json" style="max-height: 300px; overflow: auto;" word-wrap />
        </div>
      </n-spin>
    </n-modal>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { 
  SettingsOutline, 
  AddOutline, 
  CloseOutline,
  CodeSlashOutline,
  CopyOutline,
  CloudDownloadOutline
} from '@vicons/ionicons5'
import type { TestConfig } from '@/types'

// Props & Emits
const props = defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'run-test', config: TestConfig): void
  (e: 'preview-script', config: TestConfig): void
}>()

const message = useMessage()

// Form ref
const formRef = ref<FormInst | null>(null)

// Form data
const formData = reactive<TestConfig>({
  name: '新建压测',
  url: '',
  method: 'GET',
  headers: {},
  body: '',
  loadCategory: 'vus',
  loadSubMode: 'simple',
  vus: 10,
  duration: '30s',
  stages: [],
  rps: 100,
  preAllocatedVUs: 10,
  maxVUs: 100,
  rpsStages: [
    { duration: '10s', target: 100 },
    { duration: '20s', target: 200 },
    { duration: '10s', target: 400 }

  ],
  stopOnFailure: false,
  thresholds: [
    { metric: 'http_req_duration', condition: 'p(95)<500' },
    { metric: 'http_req_failed', condition: 'rate<0.01' }
  ],
})

// Headers JSON string for textarea
const headersJson = ref('{\n  "Content-Type": "application/json"\n}')
const headersJsonError = ref('')

// Watch headers JSON and parse
watch(headersJson, (val) => {
  try {
    formData.headers = JSON.parse(val || '{}')
    headersJsonError.value = ''
  } catch (e) {
    headersJsonError.value = 'JSON 格式错误'
  }
})

// Body validation and formatting
const bodyJsonError = ref('')

function formatBody() {
  if (!formData.body) {
    bodyJsonError.value = ''
    return
  }
  try {
    const obj = JSON.parse(formData.body)
    formData.body = JSON.stringify(obj, null, 2)
    bodyJsonError.value = ''
  } catch (e) {
    bodyJsonError.value = 'JSON 格式错误'
  }
}

function processBodyForSubmission(headers: any, body: string): string {
  // Check for Content-Type
  let contentType = ''
  if (Array.isArray(headers)) {
     const h = headers.find((x: any) => x.key.toLowerCase() === 'content-type')
     if (h) contentType = h.value
  } else if (typeof headers === 'object') {
     const k = Object.keys(headers).find(k => k.toLowerCase() === 'content-type')
     if (k) contentType = headers[k]
  }

  if (contentType.includes('application/x-www-form-urlencoded') && body) {
    try {
        const obj = JSON.parse(body)
        const params = new URLSearchParams()
        Object.entries(obj).forEach(([k, v]) => {
            params.append(k, String(v))
        })
        return params.toString()
    } catch (e) {
        // Not valid JSON, return as is
        return body
    }
  }
  return body
}


// Form rules
const rules: FormRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
  ],
  url: [
    { required: true, message: '请输入请求URL', trigger: 'blur' },
    { 
      pattern: /^https?:\/\/.+/, 
      message: 'URL必须以 http:// 或 https:// 开头', 
      trigger: 'blur' 
    },
  ],
  vus: [
    { required: true, type: 'number', message: '请输入虚拟用户数', trigger: 'blur' },
  ],
  duration: [
    { required: true, message: '请输入持续时间', trigger: 'blur' },
    {
      pattern: /^\d+[smh]$/,
      message: '格式应为数字+单位，如 30s, 1m, 1h',
      trigger: 'blur',
    },
  ],
}

// Options
const methodOptions = [
  { label: 'GET', value: 'GET' },
  { label: 'POST', value: 'POST' },
  { label: 'PUT', value: 'PUT' },
  { label: 'DELETE', value: 'DELETE' },
  { label: 'PATCH', value: 'PATCH' },
]

const metricOptions = [
  { label: 'http_req_duration (响应时间)', value: 'http_req_duration' },
  { label: 'http_req_failed (失败率)', value: 'http_req_failed' },
  { label: 'http_reqs (请求数)', value: 'http_reqs' },
  { label: 'iteration_duration (迭代时间)', value: 'iteration_duration' },
]

// Stage management - VU stages
function addStage() {
  formData.stages.push({ duration: '30s', target: 10 })
}

function removeStage(index: number) {
  formData.stages.splice(index, 1)
}

// Stage management - RPS stages
function addRpsStage() {
  formData.rpsStages.push({ duration: '30s', target: 50 })
}

function removeRpsStage(index: number) {
  formData.rpsStages.splice(index, 1)
}

// Threshold management
function addThreshold() {
  formData.thresholds.push({ metric: '', condition: '' })
}

function removeThreshold(index: number) {
  formData.thresholds.splice(index, 1)
}

// Upload handlers
function handleUploadFinish({ file, event }: { file: any, event: ProgressEvent }) {
  const xhr = event.target as XMLHttpRequest
  try {
    let res = xhr.response
    // If response is a string, try to parse it
    if (typeof res === 'string') {
      try {
        res = JSON.parse(res)
      } catch (e) {
        // Not JSON, assume error text
        throw new Error('Invalid JSON response')
      }
    }
    
    // Check if response has expected structure (e.g. path)
    if (res && res.path) {
      formData.dataFile = res.path // Store server absolute path
      message.success(`文件 ${file.name} 上传成功`)
    } else {
       throw new Error('Invalid response structure')
    }
  } catch (e) {
    console.error('Upload parse error', e)
    let errorMsg = 'Unknown error'
    if (xhr.response) {
       if (typeof xhr.response === 'string') {
          errorMsg = xhr.response.substring(0, 200)
       } else {
          errorMsg = JSON.stringify(xhr.response).substring(0, 200)
       }
    }
    message.error(`文件上传失败: ${errorMsg}`)
  }
}

function handleUploadError() {
  message.error('文件上传失败')
}

function downloadTemplate() {
  window.open('/api/template/csv', '_blank')
}

// Submit handler
async function handleSubmit() {
  try {
    await formRef.value?.validate()
    if (headersJsonError.value) {
      message.error('请修正请求头 JSON 格式')
      return
    }
    const payload = { ...formData }
    payload.body = processBodyForSubmission(payload.headers, payload.body)
    emit('run-test', payload)
  } catch (e) {
    console.error('Validation failed:', e)
  }
}

// ============ cURL Import ============
const showCurlImport = ref(false)
const curlInput = ref('')

function parseCurl(curlCommand: string) {
  const result = {
    url: '',
    method: 'GET',
    headers: {} as Record<string, string>,
    body: ''
  }
  
  // Remove line continuations and normalize whitespace
  let normalized = curlCommand
    .replace(/\\\r?\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  
  // Remove 'curl' prefix
  normalized = normalized.replace(/^curl\s+/i, '')
  
  // Extract URL - it's usually the first argument or after -X METHOD
  // URL can be quoted or unquoted
  const urlPatterns = [
    /^['"]?(https?:\/\/[^\s'"]+)['"]?/,  // URL at start
    /\s['"]?(https?:\/\/[^\s'"]+)['"]?/,  // URL after space
  ]
  
  for (const pattern of urlPatterns) {
    const match = normalized.match(pattern)
    if (match) {
      result.url = match[1]
      break
    }
  }
  
  // Extract method with -X
  const methodMatch = normalized.match(/-X\s+['"]?(\w+)['"]?/i)
  if (methodMatch) {
    result.method = methodMatch[1].toUpperCase()
  }
  
  // Extract all headers with -H
  // Extract all headers with -H
  // Regex to handle -H 'key: value' or -H "key: value" or -H key:value
  const headerRegex = /-H\s+(?:'([^']*)'|"([^"]*)"|([^\s"']+))/gi
  let headerMatch
  while ((headerMatch = headerRegex.exec(normalized)) !== null) {
    const headerStr = headerMatch[1] || headerMatch[2] || headerMatch[3] || ''
    const colonIndex = headerStr.indexOf(':')
    if (colonIndex > 0) {
      const key = headerStr.substring(0, colonIndex).trim()
      const value = headerStr.substring(colonIndex + 1).trim()
      result.headers[key] = value
    }
  }
  
  // Extract body data - handle multiple formats
  const bodyParts: string[] = []
  
  // Handle body data extraction with better quote support
  const dataFlags = ['--data-urlencode', '-d', '--data', '--data-raw']
  const flagPattern = dataFlags.map(f => f.replace(/-/g, '\\-')).join('|')
  const bodyRegex = new RegExp(`(?:${flagPattern})\\s+(?:'([^']*)'|"([^"]*)"|([^\\s"']+))`, 'gi')
  
  let bodyMatch
  while ((bodyMatch = bodyRegex.exec(normalized)) !== null) {
    const content = bodyMatch[1] || bodyMatch[2] || bodyMatch[3] || ''
    bodyParts.push(content)
  }
  
  // Combine body parts
  if (bodyParts.length > 0) {
    // Check if it's URL encoded format
    const isUrlEncoded = bodyParts.some(p => p.includes('='))
    if (isUrlEncoded) {
      const combined = bodyParts.join('&')
      try {
        const params = new URLSearchParams(combined)
        const obj: Record<string, string | string[]> = {}
        for (const [key, value] of params.entries()) {
          // Handle arrays? URLSearchParams handles multiple values by .getAll?
          // For simplicity, just overwrite or simpler logic for now. 
          // Standard params.entries() iterates all.
          // Let's manually handle duplicates if needed or just use simple assignment.
          // Actually, if we use Object.fromEntries(params) it takes last value.
          // Let's iteration safely.
          if (Object.prototype.hasOwnProperty.call(obj, key)) {
             // If array logic needed, complex. User probably has simple keys.
             // Just take last or keep it simple.
             obj[key] = value
          } else {
             obj[key] = value
          }
        }
        result.body = JSON.stringify(obj, null, 2)
      } catch (e) {
        result.body = combined
      }
    } else {
      result.body = bodyParts.join('')
    }
    
    // If method is still GET but we have body, change to POST
    if (result.method === 'GET' && result.body) {
      result.method = 'POST'
    }
  }
  
  return result
}

function handleImportCurl() {
  if (!curlInput.value.trim()) {
    message.warning('请输入 cURL 命令')
    return
  }
  
  try {
    const parsed = parseCurl(curlInput.value)
    formData.url = parsed.url
    formData.method = parsed.method
    formData.headers = parsed.headers
    formData.body = parsed.body
    headersJson.value = JSON.stringify(parsed.headers, null, 2)
    
    showCurlImport.value = false
    curlInput.value = ''
    message.success('导入成功')
  } catch (e) {
    message.error('解析 cURL 命令失败')
  }
}

// ============ Script Preview ============
const showScriptPreview = ref(false)
const previewScript = ref('')

function generateK6Script(): string {
  const config = formData
  
  // Build options based on two-level mode
  let optionsContent = ''
  
  if (config.loadCategory === 'vus') {
    if (config.loadSubMode === 'simple') {
      optionsContent = `  vus: ${config.vus},
  duration: '${config.duration}',`
    } else {
      // VU stages
      const stagesJson = JSON.stringify(config.stages.filter(s => s.duration && s.target > 0), null, 4)
      optionsContent = `  stages: ${stagesJson.replace(/\n/g, '\n  ')},`
    }
  } else {
    // RPS mode
    if (config.loadSubMode === 'simple') {
      optionsContent = `  scenarios: {
    constant_rps: {
      executor: 'constant-arrival-rate',
      rate: ${config.rps},
      timeUnit: '1s',
      duration: '${config.duration}',
      preAllocatedVUs: ${config.preAllocatedVUs},
      maxVUs: ${config.maxVUs},
    },
  },`
    } else {
      // RPS stages
      const rpsStagesJson = JSON.stringify(config.rpsStages.filter(s => s.duration && s.target > 0), null, 6)
      optionsContent = `  scenarios: {
    ramping_rps: {
      executor: 'ramping-arrival-rate',
      startRate: 0,
      timeUnit: '1s',
      preAllocatedVUs: ${config.preAllocatedVUs},
      maxVUs: ${config.maxVUs},
      stages: ${rpsStagesJson.replace(/\n/g, '\n      ')},
    },
  },`
    }
  }
  
  // Build thresholds
  const thresholds = config.thresholds.filter(t => t.metric && t.condition)
  let thresholdsContent = ''
  if (thresholds.length > 0) {
    const thresholdsObj: Record<string, string[]> = {}
    thresholds.forEach(t => {
      if (!thresholdsObj[t.metric]) {
        thresholdsObj[t.metric] = []
      }
      thresholdsObj[t.metric].push(t.condition)
    })
    thresholdsContent = `  thresholds: ${JSON.stringify(thresholdsObj, null, 4).replace(/\n/g, '\n  ')},`
  }
  
  // Build headers
  const headersJson = JSON.stringify(config.headers, null, 6)
  
  // Build request
  const method = config.method.toLowerCase()
  let requestCode = ''
  
  const bodyToUse = processBodyForSubmission(config.headers, config.body)
  
  if (['post', 'put', 'patch'].includes(method) && bodyToUse) {
    const bodyEscaped = bodyToUse.replace(/\\/g, '\\\\').replace(/`/g, '\\`').replace(/\${/g, '\\${')
    requestCode = `const payload = \`${bodyEscaped}\`;
  
  const res = http.${method}(url, payload, params);`
  } else {
    if (method === 'get') {
      requestCode = 'const res = http.get(url, params);'
    } else if (method === 'delete') {
      requestCode = 'const res = http.del(url, null, params);'
    } else {
      requestCode = `const res = http.${method}(url, null, params);`
    }
  }
  
  return `import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';${config.stopOnFailure ? "\nimport exec from 'k6/execution';" : ""}

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
${optionsContent}
${thresholdsContent}
};

export default function () {
  const url = '${config.url}';
  
  const params = {
    headers: ${headersJson},
  };
  
  ${requestCode}
  
  // Record metrics
  responseTime.add(res.timings.duration);
  
  // Check response
  const checkResult = check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!checkResult);
  
  // Log error details if failed
  if (res.status >= 400 || res.status === 0) {
    console.error(\`[Request Error] Status: \${res.status}, URL: \${url}\`);
    console.error(\`[Request Error] Response Body: \${res.body}\`);${config.stopOnFailure ? "\n    exec.test.abort('Aborting test due to failure (Status ${res.status})');" : ""}
  }
  
  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': JSON.stringify(data, null, 2),
  };
}
`
}

function handlePreviewScript() {
  previewScript.value = generateK6Script()
  showScriptPreview.value = true
}

function handleCopyScript() {
  navigator.clipboard.writeText(previewScript.value)
  message.success('已复制到剪贴板')
}

// ============ Debug Request ============
const showDebugResult = ref(false)
const debugLoading = ref(false)
const debugResult = ref<{
  status: number
  duration: number
  headers: Record<string, string>
  body: string
} | null>(null)

async function handleDebugRequest() {
  if (!formData.url) {
    message.warning('请输入请求 URL')
    return
  }
  
  showDebugResult.value = true
  debugLoading.value = true
  debugResult.value = null
  
  try {
    const startTime = Date.now()
    
    const response = await fetch('/api/debug', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: formData.url,
        method: formData.method,
        headers: formData.headers,
        body: processBodyForSubmission(formData.headers, formData.body || '')
      })
    })
    
    const data = await response.json()
    const duration = Date.now() - startTime
    
    debugResult.value = {
      status: data.status || response.status,
      duration: data.duration || duration,
      headers: data.headers || {},
      body: data.body || ''
    }
  } catch (e: any) {
    message.error('请求失败: ' + e.message)
    debugResult.value = {
      status: 0,
      duration: 0,
      headers: {},
      body: e.message
    }
  } finally {
    debugLoading.value = false
  }
}

function formatResponseBody(body: string): string {
  try {
    return JSON.stringify(JSON.parse(body), null, 2)
  } catch {
    return body
  }
}

// Expose for parent component
defineExpose({
  handleSubmit,
  handlePreviewScript,
  formData
})
</script>

<style scoped>
.config-form-card {
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

.stages-list,
.thresholds-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.stage-item,
.threshold-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

:deep(.n-divider) {
  margin: 16px 0;
}

:deep(.n-divider .n-divider__title) {
  font-weight: 600;
  color: #94a3b8;
}

:deep(.n-code) {
  max-height: 400px;
  overflow: auto;
}
</style>

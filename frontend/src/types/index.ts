// API types for K6 Performance Test Platform

export interface HeaderItem {
  key: string
  value: string
}

export interface StageConfig {
  duration: string
  target: number
}

export interface ThresholdConfig {
  metric: string
  condition: string
}

// 压测模式 - 两级结构
// 一级：并发用户模式 / 吞吐量模式
export type LoadCategory = 'vus' | 'rps'
// 二级：简单模式 / 阶梯模式  
export type LoadSubMode = 'simple' | 'stages'

// 保留旧类型以兼容
export type LoadMode = 'simple' | 'stages' | 'rps'

// RPS阶梯配置
export interface RpsStageConfig {
  duration: string
  target: number  // 目标RPS
}

// 简单模式配置
export interface SimpleLoadConfig {
  vus: number
  duration: string
}

// 阶梯模式配置
export interface StagesLoadConfig {
  stages: StageConfig[]
}

// RPS模式配置
export interface RpsLoadConfig {
  rps: number
  duration: string
  preAllocatedVUs: number
  maxVUs: number
}

export interface TestConfig {
  name: string
  url: string
  method: string
  headers: Record<string, string>  // JSON格式
  body: string
  // 压测模式 - 两级结构
  loadCategory: LoadCategory      // 一级：vus / rps
  loadSubMode: LoadSubMode        // 二级：simple / stages
  // VU简单模式
  vus: number
  duration: string
  // VU阶梯模式
  stages: StageConfig[]
  // RPS简单模式
  rps: number
  preAllocatedVUs: number
  maxVUs: number
  // RPS阶梯模式
  rpsStages: RpsStageConfig[]
  // 阈值
  thresholds: ThresholdConfig[]
  // 执行控制
  stopOnFailure?: boolean
  // 数据驱动
  dataFile?: string
}

export interface TestConfigResponse extends TestConfig {
  id: number
  created_at: string
  updated_at: string
}

export interface TestExecution {
  id: number
  config_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  start_time?: string
  end_time?: string
  result_summary?: TestResultSummary
  result_file?: string
  created_at: string
}

export interface TestResultSummary {
  http_reqs?: number
  http_req_duration?: {
    avg: number
    min: number
    max: number
    p90: number
    p95: number
  }
  http_req_failed?: number
  iterations?: number
  vus?: number
  vus_max?: number
  duration?: number  // Test duration in ms
  rps?: number       // Average RPS
  rps_max?: number   // Max RPS
  metrics?: K6Metrics
}

export interface K6Metrics {
  http_reqs?: MetricValue
  http_req_duration?: MetricTiming
  http_req_failed?: MetricValue
  http_req_blocked?: MetricTiming
  http_req_connecting?: MetricTiming
  http_req_tls_handshaking?: MetricTiming
  http_req_sending?: MetricTiming
  http_req_waiting?: MetricTiming
  http_req_receiving?: MetricTiming
  iterations?: MetricValue
  iteration_duration?: MetricTiming
  data_received?: MetricValue
  data_sent?: MetricValue
  vus?: MetricValue
  vus_max?: MetricValue
}

export interface MetricValue {
  type: string
  contains: string
  values: {
    count?: number
    rate?: number
    value?: number
  }
}

export interface MetricTiming {
  type: string
  contains: string
  values: {
    avg: number
    min: number
    med: number
    max: number
    'p(90)': number
    'p(95)': number
  }
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'log' | 'status' | 'result' | 'error' | 'execution_started' | 'info' | 'script_preview'
  level?: 'info' | 'warning' | 'error' | 'success'
  message?: string
  status?: string
  data?: any
  execution_id?: number
  config_id?: number
  script?: string
}

// Component state types
export type TestStatus = 'idle' | 'starting' | 'running' | 'completed' | 'failed'

// Curl解析结果
export interface CurlParseResult {
  url: string
  method: string
  headers: Record<string, string>
  body: string
}

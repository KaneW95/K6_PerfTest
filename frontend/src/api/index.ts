import axios from 'axios'
import type { TestConfig, TestConfigResponse, TestExecution } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Test Configuration APIs
export const configApi = {
  // List all configurations
  list: () => api.get<TestConfigResponse[]>('/configs'),
  
  // Get a specific configuration
  get: (id: number) => api.get<TestConfigResponse>(`/configs/${id}`),
  
  // Create a new configuration
  create: (config: TestConfig) => api.post<TestConfigResponse>('/configs', config),
  
  // Update a configuration
  update: (id: number, config: Partial<TestConfig>) => 
    api.put<TestConfigResponse>(`/configs/${id}`, config),
  
  // Delete a configuration
  delete: (id: number) => api.delete(`/configs/${id}`),
}

// Test Execution APIs
export const executionApi = {
  // List executions
  list: (configId?: number) => {
    const params = configId ? { config_id: configId } : {}
    return api.get<TestExecution[]>('/executions', { params })
  },
  
  // Get a specific execution
  get: (id: number) => api.get<TestExecution>(`/executions/${id}`),
}

// WebSocket helper
export function createTestWebSocket(): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return new WebSocket(`${protocol}//${host}/api/ws/test`)
}

export default api

import request from './request'

export function createTask(formData) {
  return request.post('/tasks', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
}

export function createTaskBatch(formData) {
  return request.post('/tasks/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  })
}

export function getTasks(params) {
  return request.get('/tasks', { params })
}

export function getTaskDetail(taskNo) {
  return request.get(`/tasks/${taskNo}`)
}

export function getTaskResult(taskNo) {
  return request.get(`/tasks/${taskNo}/result`)
}

export function downloadReport(taskNo) {
  return request.get(`/tasks/${taskNo}/download`)
}

export function downloadBatchReports(taskNos) {
  return request.post('/tasks/download-batch', taskNos, { responseType: 'blob' })
}

export function retryTask(taskNo) {
  return request.post(`/tasks/${taskNo}/retry`)
}

export function getTaskLogs(taskNo) {
  return request.get(`/tasks/${taskNo}/logs`)
}

export function getLlmCostStats() {
  return request.get('/tasks/stats/llm-cost')
}

import request from './request'

export function createTask(formData) {
  return request.post('/tasks', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
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

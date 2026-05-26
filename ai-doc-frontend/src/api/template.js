import request from './request'

export function getTemplates(params) {
  return request.get('/templates', { params })
}

export function createTemplate(formData) {
  return request.post('/templates', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteTemplate(id) {
  return request.delete(`/templates/${id}`)
}

import request from './request'

export function getNotifyConfigs() {
  return request.get('/notify-config')
}

export function createNotifyConfig(data) {
  return request.post('/notify-config', data)
}

export function updateNotifyConfig(id, data) {
  return request.put(`/notify-config/${id}`, data)
}

export function deleteNotifyConfig(id) {
  return request.delete(`/notify-config/${id}`)
}

export function testNotify(data) {
  return request.post('/notify-config/test', data)
}

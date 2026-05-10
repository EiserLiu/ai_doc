import { Tag } from 'antd'

const statusMap = {
  pending: { color: 'default', text: '等待中' },
  queued: { color: 'processing', text: '已排队' },
  processing: { color: 'processing', text: '处理中' },
  success: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
}

export default function TaskStatusTag({ status }) {
  const config = statusMap[status] || { color: 'default', text: status }
  return <Tag color={config.color}>{config.text}</Tag>
}

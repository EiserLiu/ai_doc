import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Typography, Descriptions } from 'antd'
import { FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, ApiOutlined } from '@ant-design/icons'
import { getTasks, getLlmCostStats } from '../api/task'
import TaskStatusTag from '../components/TaskStatusTag'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ total: 0, success: 0, failed: 0, processing: 0 })
  const [recentTasks, setRecentTasks] = useState([])
  const [costStats, setCostStats] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [all, success, failed, processing] = await Promise.all([
        getTasks({ page_size: 1 }),
        getTasks({ status: 'success', page_size: 1 }),
        getTasks({ status: 'failed', page_size: 1 }),
        getTasks({ status: 'processing', page_size: 1 }),
      ])
      setStats({
        total: all.total || 0,
        success: success.total || 0,
        failed: failed.total || 0,
        processing: (processing.total || 0),
      })

      const recent = await getTasks({ page_size: 5 })
      setRecentTasks(recent.items || [])

      try {
        const cost = await getLlmCostStats()
        setCostStats(cost)
      } catch (e) {
        // cost stats may not be available yet
      }
    } catch (e) {
      // ignore
    }
  }

  const columns = [
    { title: '文件名', dataIndex: 'original_filename', key: 'filename' },
    { title: '类型', dataIndex: 'analyze_type', key: 'type', render: (v) => v === 'policy' ? '政策分析' : '招标分析' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v) => <TaskStatusTag status={v} /> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v) => v ? new Date(v).toLocaleString('zh-CN') : '-' },
  ]

  const costColumns = [
    { title: '模型', dataIndex: 'model', key: 'model' },
    { title: '调用次数', dataIndex: 'call_count', key: 'call_count' },
    { title: '输入 Token', dataIndex: 'prompt_tokens', key: 'prompt_tokens', render: (v) => (v || 0).toLocaleString() },
    { title: '输出 Token', dataIndex: 'completion_tokens', key: 'completion_tokens', render: (v) => (v || 0).toLocaleString() },
  ]

  return (
    <div>
      <Title level={4}>首页概览</Title>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card><Statistic title="总任务数" value={stats.total} prefix={<FileTextOutlined />} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="已完成" value={stats.success} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#3f8600' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="处理中" value={stats.processing} prefix={<SyncOutlined spin />} valueStyle={{ color: '#1890ff' }} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="失败" value={stats.failed} prefix={<CloseCircleOutlined />} valueStyle={{ color: '#cf1322' }} /></Card>
        </Col>
      </Row>

      {costStats && (
        <Card title="LLM 调用统计" style={{ marginBottom: 24 }} extra={<ApiOutlined />}>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Statistic title="总调用次数" value={costStats.total_calls} />
            </Col>
            <Col span={8}>
              <Statistic title="输入 Token" value={costStats.total_prompt_tokens} />
            </Col>
            <Col span={8}>
              <Statistic title="输出 Token" value={costStats.total_completion_tokens} />
            </Col>
          </Row>
          {costStats.by_model && costStats.by_model.length > 0 && (
            <Table
              columns={costColumns}
              dataSource={costStats.by_model}
              rowKey="model"
              pagination={false}
              size="small"
            />
          )}
        </Card>
      )}

      <Card title="最近任务">
        <Table
          columns={columns}
          dataSource={recentTasks}
          rowKey="task_no"
          pagination={false}
          onRow={(record) => ({ onClick: () => navigate(`/tasks/${record.task_no}`), style: { cursor: 'pointer' } })}
        />
      </Card>
    </div>
  )
}

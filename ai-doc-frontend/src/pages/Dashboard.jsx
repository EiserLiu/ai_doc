import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Typography } from 'antd'
import { FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons'
import { getTasks } from '../api/task'
import TaskStatusTag from '../components/TaskStatusTag'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ total: 0, success: 0, failed: 0, processing: 0 })
  const [recentTasks, setRecentTasks] = useState([])

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

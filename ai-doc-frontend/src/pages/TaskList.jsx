import { useEffect, useState } from 'react'
import { Table, Card, Select, Space, Button, Typography } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { getTasks } from '../api/task'
import TaskStatusTag from '../components/TaskStatusTag'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

export default function TaskList() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState(null)
  const [typeFilter, setTypeFilter] = useState(null)

  const loadData = async (p = page) => {
    setLoading(true)
    try {
      const params = { page: p, page_size: 15 }
      if (statusFilter) params.status = statusFilter
      if (typeFilter) params.analyze_type = typeFilter
      const res = await getTasks(params)
      setData(res.items || [])
      setTotal(res.total || 0)
    } catch (e) {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData(1); setPage(1) }, [statusFilter, typeFilter])

  const columns = [
    { title: '文件名', dataIndex: 'original_filename', key: 'filename', ellipsis: true },
    { title: '分析类型', dataIndex: 'analyze_type', key: 'type', width: 120, render: (v) => v === 'policy' ? '政策分析' : '招标分析' },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v) => <TaskStatusTag status={v} /> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180, render: (v) => v ? new Date(v).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'action', width: 100,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => navigate(`/tasks/${record.task_no}`)}>
          查看
        </Button>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>任务列表</Title>
        <Space>
          <Select placeholder="状态筛选" allowClear style={{ width: 120 }} onChange={setStatusFilter}
            options={[
              { value: 'pending', label: '等待中' },
              { value: 'queued', label: '已排队' },
              { value: 'processing', label: '处理中' },
              { value: 'success', label: '已完成' },
              { value: 'failed', label: '失败' },
            ]}
          />
          <Select placeholder="类型筛选" allowClear style={{ width: 120 }} onChange={setTypeFilter}
            options={[
              { value: 'policy', label: '政策分析' },
              { value: 'bidding', label: '招标分析' },
            ]}
          />
          <Button icon={<ReloadOutlined />} onClick={() => loadData()}>刷新</Button>
        </Space>
      </div>
      <Card>
        <Table
          columns={columns}
          dataSource={data}
          rowKey="task_no"
          loading={loading}
          pagination={{
            current: page,
            total,
            pageSize: 15,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p) => { setPage(p); loadData(p) },
          }}
        />
      </Card>
    </div>
  )
}

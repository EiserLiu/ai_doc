import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Descriptions, Typography, Button, Spin, message, Divider, List, Tag, Timeline } from 'antd'
import { DownloadOutlined, ReloadOutlined, RedoOutlined } from '@ant-design/icons'
import { getTaskDetail, downloadReport, retryTask, getTaskLogs } from '../api/task'
import TaskStatusTag from '../components/TaskStatusTag'

const { Title, Paragraph, Text } = Typography

export default function TaskDetail() {
  const { taskNo } = useParams()
  const [loading, setLoading] = useState(true)
  const [task, setTask] = useState(null)
  const [logs, setLogs] = useState([])
  const [retrying, setRetrying] = useState(false)

  const loadTask = async () => {
    setLoading(true)
    try {
      const res = await getTaskDetail(taskNo)
      setTask(res)
    } catch (e) {
      // handled
    } finally {
      setLoading(false)
    }
  }

  const loadLogs = async () => {
    try {
      const res = await getTaskLogs(taskNo)
      setLogs(res || [])
    } catch (e) {
      // ignore
    }
  }

  const handleRetry = async () => {
    setRetrying(true)
    try {
      await retryTask(taskNo)
      message.success('已重新提交任务')
      loadTask()
    } catch (e) {
      message.error('重试失败')
    } finally {
      setRetrying(false)
    }
  }

  useEffect(() => { loadTask(); loadLogs() }, [taskNo])

  useEffect(() => {
    if (task && ['pending', 'queued', 'processing'].includes(task.status)) {
      const timer = setInterval(() => { loadTask(); loadLogs() }, 3000)
      return () => clearInterval(timer)
    }
  }, [task?.status])

  const handleDownload = async () => {
    try {
      const res = await downloadReport(taskNo)
      window.open(res.download_url, '_blank')
    } catch (e) {
      message.error('下载失败')
    }
  }

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!task) return <div>任务不存在</div>

  const result = task.result_json || {}

  const renderList = (title, items) => {
    if (!items || !Array.isArray(items) || items.length === 0) return null
    return (
      <>
        <Title level={5}>{title}</Title>
        <List
          size="small"
          bordered
          dataSource={items}
          renderItem={(item, i) => <List.Item>{i + 1}. {item}</List.Item>}
          style={{ marginBottom: 16 }}
        />
      </>
    )
  }

  const renderRisks = (items) => {
    if (!items || !Array.isArray(items) || items.length === 0) return null
    return (
      <>
        <Title level={5}>风险提醒</Title>
        <List
          size="small"
          bordered
          dataSource={items}
          renderItem={(item) => (
            <List.Item>
              <Tag color="red" style={{ marginRight: 8 }}>风险</Tag>
              {item}
            </List.Item>
          )}
          style={{ marginBottom: 16 }}
        />
      </>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>任务详情</Title>
        <Space>
          {task.status === 'success' && (
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>下载报告</Button>
          )}
          {task.status === 'failed' && (
            <Button type="primary" danger icon={<RedoOutlined />} onClick={handleRetry} loading={retrying}>重试</Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={() => { loadTask(); loadLogs() }}>刷新</Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions column={2}>
          <Descriptions.Item label="任务编号">{task.task_no}</Descriptions.Item>
          <Descriptions.Item label="状态"><TaskStatusTag status={task.status} /></Descriptions.Item>
          <Descriptions.Item label="文件名">{task.original_filename}</Descriptions.Item>
          <Descriptions.Item label="分析类型">{task.analyze_type === 'policy' ? '政策文件分析' : '招标文件分析'}</Descriptions.Item>
          <Descriptions.Item label="输出格式">{task.output_format?.toUpperCase()}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
          {task.finished_at && <Descriptions.Item label="完成时间">{new Date(task.finished_at).toLocaleString('zh-CN')}</Descriptions.Item>}
          {task.error_message && <Descriptions.Item label="错误信息"><Text type="danger">{task.error_message}</Text></Descriptions.Item>}
        </Descriptions>
      </Card>

      {task.status === 'success' && result && (
        <Card title="分析结果">
          {result.summary && (
            <>
              <Title level={5}>核心摘要</Title>
              <Paragraph style={{ background: '#f6f8fa', padding: 16, borderRadius: 8, marginBottom: 16 }}>{result.summary}</Paragraph>
            </>
          )}

          {task.analyze_type === 'policy' && (
            <>
              {result.policy_title && <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
                <Descriptions.Item label="政策标题">{result.policy_title}</Descriptions.Item>
                {result.publish_department && <Descriptions.Item label="发布部门">{result.publish_department}</Descriptions.Item>}
                {result.publish_date && <Descriptions.Item label="发布日期">{result.publish_date}</Descriptions.Item>}
                {result.deadline && <Descriptions.Item label="截止时间"><Text type="danger">{result.deadline}</Text></Descriptions.Item>}
              </Descriptions>}
              {renderList('支持对象', result.support_target)}
              {renderList('支持行业', result.support_industry)}
              {renderList('申报条件', result.apply_conditions)}
              {renderList('支持措施', result.support_measures)}
              {renderList('奖补金额', result.subsidy_amount)}
              {renderList('申报材料', result.apply_materials)}
              {renderList('申报流程', result.process)}
              {renderRisks(result.risks)}
              {renderList('建议行动', result.suggestions)}
            </>
          )}

          {task.analyze_type === 'bidding' && (
            <>
              {result.project_name && <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
                <Descriptions.Item label="项目名称">{result.project_name}</Descriptions.Item>
                {result.buyer && <Descriptions.Item label="采购人">{result.buyer}</Descriptions.Item>}
                {result.agency && <Descriptions.Item label="代理机构">{result.agency}</Descriptions.Item>}
                {result.budget && <Descriptions.Item label="预算金额">{result.budget}</Descriptions.Item>}
                {result.bid_deadline && <Descriptions.Item label="投标截止"><Text type="danger">{result.bid_deadline}</Text></Descriptions.Item>}
                {result.bid_open_time && <Descriptions.Item label="开标时间">{result.bid_open_time}</Descriptions.Item>}
              </Descriptions>}
              {renderList('资质要求', result.qualification_requirements)}
              {renderList('业绩要求', result.performance_requirements)}
              {renderList('技术要求', result.technical_requirements)}
              {renderList('评分标准', result.score_rules)}
              {renderList('投标材料', result.required_materials)}
              {renderRisks(result.invalid_bid_risks)}
              {renderList('重点关注', result.key_points)}
              {renderList('投标准备建议', result.suggestions)}
            </>
          )}

          <Divider />
          <Paragraph type="secondary" style={{ fontSize: 12 }}>
            免责声明：本报告由 AI 根据上传文件自动生成，仅用于辅助整理和初步分析。涉及法律、财务、投标、政策申报等重要事项，请以原文和专业人员审核为准。
          </Paragraph>
        </Card>
      )}

      {logs.length > 0 && (
        <Card title="处理日志" style={{ marginTop: 16 }}>
          <Timeline
            items={logs.map((log) => ({
              color: log.level === 'ERROR' ? 'red' : log.level === 'WARNING' ? 'orange' : 'blue',
              children: (
                <div>
                  <Text type="secondary" style={{ fontSize: 12 }}>{log.created_at ? new Date(log.created_at).toLocaleString('zh-CN') : ''}</Text>
                  <br />
                  <Text>{log.message}</Text>
                </div>
              ),
            }))}
          />
        </Card>
      )}
    </div>
  )
}

function Space({ children, ...props }) {
  return <span style={{ display: 'inline-flex', gap: 8, ...props }}>{children}</span>
}

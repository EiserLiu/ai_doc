import { useState, useEffect } from 'react'
import { Card, Form, Upload, Radio, Switch, Select, Button, message, Typography, Result, Table, Alert } from 'antd'
import { InboxOutlined, FileTextOutlined } from '@ant-design/icons'
import { createTask, createTaskBatch } from '../api/task'
import { getTemplates } from '../api/template'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography
const { Dragger } = Upload

export default function UploadPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [analyzeType, setAnalyzeType] = useState('policy')
  const [outputFormat, setOutputFormat] = useState('docx')
  const [notify, setNotify] = useState(false)
  const [fileList, setFileList] = useState([])
  const [results, setResults] = useState(null)
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  useEffect(() => {
    getTemplates().then((res) => setTemplates(res || [])).catch(() => {})
  }, [])

  const filteredTemplates = templates.filter((t) => t.analyze_type === analyzeType)

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }
    setLoading(true)
    try {
      if (fileList.length === 1) {
        const formData = new FormData()
        formData.append('file', fileList[0])
        formData.append('analyze_type', analyzeType)
        formData.append('output_format', outputFormat)
        if (selectedTemplate) formData.append('template_id', selectedTemplate)
        const res = await createTask(formData)
        setResults([{ ...res, filename: fileList[0].name }])
      } else {
        const formData = new FormData()
        fileList.forEach((f) => formData.append('files', f))
        formData.append('analyze_type', analyzeType)
        formData.append('output_format', outputFormat)
        if (selectedTemplate) formData.append('template_id', selectedTemplate)
        const res = await createTaskBatch(formData)
        setResults(res)
      }
      message.success(fileList.length > 1 ? '批量任务创建成功' : '任务创建成功')
    } catch (e) {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  if (results) {
    const successTasks = results.filter((r) => !r.error)
    const failedTasks = results.filter((r) => r.error)

    const columns = [
      { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
      { title: '任务编号', dataIndex: 'task_no', key: 'task_no' },
      { title: '状态', dataIndex: 'status', key: 'status' },
      { title: '错误', dataIndex: 'error', key: 'error', render: (v) => v ? <span style={{ color: '#ff4d4f' }}>{v}</span> : '-' },
    ]

    return (
      <div>
        <Result
          status={failedTasks.length > 0 ? 'warning' : 'success'}
          title={failedTasks.length > 0 ? '部分任务创建成功' : '任务创建成功'}
          subTitle={`成功 ${successTasks.length} 个，失败 ${failedTasks.length} 个`}
        />
        {failedTasks.length > 0 && (
          <Alert type="warning" message="以下文件创建失败" description={failedTasks.map((f) => `${f.filename}: ${f.error}`).join('\n')} style={{ marginBottom: 16 }} />
        )}
        <Table
          dataSource={results}
          columns={columns}
          rowKey={(r) => r.task_no || r.filename}
          pagination={false}
          size="small"
          style={{ marginBottom: 16 }}
        />
        <Button type="primary" onClick={() => { setResults(null); setFileList([]) }}>
          继续上传
        </Button>
      </div>
    )
  }

  const uploadProps = {
    accept: '.pdf,.docx,.xlsx',
    beforeUpload: (f) => {
      setFileList((prev) => [...prev, f])
      return false
    },
    fileList,
    onRemove: (file) => {
      setFileList((prev) => prev.filter((f) => f !== file))
    },
    multiple: true,
  }

  return (
    <div>
      <Title level={4}>上传分析</Title>
      <Card style={{ maxWidth: 600 }}>
        <Form layout="vertical">
          <Form.Item label="分析类型">
            <Radio.Group value={analyzeType} onChange={(e) => { setAnalyzeType(e.target.value); setSelectedTemplate(null) }}>
              <Radio.Button value="policy">政策文件分析</Radio.Button>
              <Radio.Button value="bidding">招标文件分析</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item label="上传文件">
            <Dragger {...uploadProps} style={{ padding: '20px 0' }}>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持 PDF、DOCX、XLSX 格式，可多选，最大 50MB</p>
            </Dragger>
          </Form.Item>
          <Form.Item label="输出格式">
            <Radio.Group value={outputFormat} onChange={(e) => setOutputFormat(e.target.value)}>
              <Radio value="docx">Word</Radio>
              <Radio value="pdf">PDF</Radio>
            </Radio.Group>
          </Form.Item>
          {filteredTemplates.length > 0 && (
            <Form.Item label="报告模板">
              <Select
                allowClear
                placeholder="使用默认模板"
                value={selectedTemplate}
                onChange={setSelectedTemplate}
                options={filteredTemplates.map((t) => ({ value: t.id, label: t.template_name }))}
              />
            </Form.Item>
          )}
          <Form.Item label="完成后通知">
            <Switch checked={notify} onChange={setNotify} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<FileTextOutlined />} loading={loading} onClick={handleUpload} block size="large">
              {fileList.length > 1 ? `开始分析 (${fileList.length} 个文件)` : '开始分析'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

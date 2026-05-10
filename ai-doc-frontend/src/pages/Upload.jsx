import { useState } from 'react'
import { Card, Form, Upload, Radio, Switch, Button, message, Typography, Result } from 'antd'
import { InboxOutlined, FileTextOutlined } from '@ant-design/icons'
import { createTask } from '../api/task'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography
const { Dragger } = Upload

export default function UploadPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [analyzeType, setAnalyzeType] = useState('policy')
  const [outputFormat, setOutputFormat] = useState('docx')
  const [notify, setNotify] = useState(false)
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)

  const handleUpload = async () => {
    if (!file) {
      message.warning('请先选择文件')
      return
    }
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('analyze_type', analyzeType)
      formData.append('output_format', outputFormat)
      const res = await createTask(formData)
      setResult(res)
      message.success('任务创建成功')
    } catch (e) {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return (
      <Result
        status="success"
        title="任务创建成功"
        subTitle={`任务编号：${result.task_no}，当前状态：${result.status}`}
        extra={[
          <Button type="primary" key="detail" onClick={() => navigate(`/tasks/${result.task_no}`)}>
            查看任务详情
          </Button>,
          <Button key="new" onClick={() => { setResult(null); setFile(null) }}>
            继续上传
          </Button>,
        ]}
      />
    )
  }

  const uploadProps = {
    accept: '.pdf,.docx',
    beforeUpload: (f) => {
      setFile(f)
      return false
    },
    fileList: file ? [file] : [],
    onRemove: () => setFile(null),
    maxCount: 1,
  }

  return (
    <div>
      <Title level={4}>上传分析</Title>
      <Card style={{ maxWidth: 600 }}>
        <Form layout="vertical">
          <Form.Item label="分析类型">
            <Radio.Group value={analyzeType} onChange={(e) => setAnalyzeType(e.target.value)}>
              <Radio.Button value="policy">政策文件分析</Radio.Button>
              <Radio.Button value="bidding">招标文件分析</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item label="上传文件">
            <Dragger {...uploadProps} style={{ padding: '20px 0' }}>
              <p className="ant-upload-drag-icon"><InboxOutlined /></p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持 PDF、DOCX 格式，最大 50MB</p>
            </Dragger>
          </Form.Item>
          <Form.Item label="输出格式">
            <Radio.Group value={outputFormat} onChange={(e) => setOutputFormat(e.target.value)}>
              <Radio value="docx">Word</Radio>
              <Radio value="pdf">PDF</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item label="完成后通知">
            <Switch checked={notify} onChange={setNotify} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" icon={<FileTextOutlined />} loading={loading} onClick={handleUpload} block size="large">
              开始分析
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

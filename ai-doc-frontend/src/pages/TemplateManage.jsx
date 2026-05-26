import { useEffect, useState } from 'react'
import { Card, Table, Button, Modal, Form, Input, Select, Upload, message, Typography, Popconfirm, Tag } from 'antd'
import { PlusOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons'
import { getTemplates, createTemplate, deleteTemplate } from '../api/template'

const { Title } = Typography

export default function TemplateManage() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [file, setFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await getTemplates()
      setData(res || [])
    } catch (e) {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (!file) {
        message.warning('请选择模板文件')
        return
      }
      setSubmitting(true)
      const formData = new FormData()
      formData.append('file', file)
      formData.append('template_name', values.template_name)
      formData.append('analyze_type', values.analyze_type)
      await createTemplate(formData)
      message.success('模板创建成功')
      setModalOpen(false)
      form.resetFields()
      setFile(null)
      loadData()
    } catch (e) {
      // handled by interceptor
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteTemplate(id)
      message.success('模板已删除')
      loadData()
    } catch (e) {
      // handled by interceptor
    }
  }

  const columns = [
    { title: '模板名称', dataIndex: 'template_name', key: 'name' },
    {
      title: '分析类型', dataIndex: 'analyze_type', key: 'type', width: 120,
      render: (v) => <Tag color={v === 'policy' ? 'blue' : 'green'}>{v === 'policy' ? '政策分析' : '招标分析'}</Tag>,
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180, render: (v) => v ? new Date(v).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'action', width: 100,
      render: (_, record) => (
        <Popconfirm title="确定删除该模板？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} size="small">删除</Button>
        </Popconfirm>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>模板管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>上传模板</Button>
      </div>
      <Card>
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title="上传模板"
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => { setModalOpen(false); form.resetFields(); setFile(null) }}
        confirmLoading={submitting}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="template_name" label="模板名称" rules={[{ required: true, message: '请输入模板名称' }]}>
            <Input placeholder="例如：政策分析报告模板" />
          </Form.Item>
          <Form.Item name="analyze_type" label="分析类型" rules={[{ required: true, message: '请选择分析类型' }]}>
            <Select placeholder="选择分析类型" options={[
              { value: 'policy', label: '政策文件分析' },
              { value: 'bidding', label: '招标文件分析' },
            ]} />
          </Form.Item>
          <Form.Item label="模板文件" required>
            <Upload
              accept=".docx"
              beforeUpload={(f) => { setFile(f); return false }}
              fileList={file ? [file] : []}
              onRemove={() => setFile(null)}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择 .docx 文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

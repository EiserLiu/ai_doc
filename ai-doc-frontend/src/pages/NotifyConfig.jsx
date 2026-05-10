import { useEffect, useState } from 'react'
import { Card, Form, Input, Select, Switch, Button, List, message, Typography, Modal, Space, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined, SendOutlined } from '@ant-design/icons'
import { getNotifyConfigs, createNotifyConfig, deleteNotifyConfig, updateNotifyConfig, testNotify } from '../api/notify'

const { Title } = Typography

const notifyTypes = [
  { value: 'feishu', label: '飞书机器人' },
  { value: 'wecom', label: '企业微信' },
  { value: 'dingtalk', label: '钉钉' },
]

export default function NotifyConfig() {
  const [configs, setConfigs] = useState([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const loadConfigs = async () => {
    setLoading(true)
    try {
      const res = await getNotifyConfigs()
      setConfigs(res || [])
    } catch (e) {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadConfigs() }, [])

  const handleAdd = async (values) => {
    try {
      await createNotifyConfig(values)
      message.success('配置成功')
      setModalOpen(false)
      form.resetFields()
      loadConfigs()
    } catch (e) {
      // handled
    }
  }

  const handleDelete = async (id) => {
    try {
      await deleteNotifyConfig(id)
      message.success('已删除')
      loadConfigs()
    } catch (e) {
      // handled
    }
  }

  const handleToggle = async (config) => {
    try {
      await updateNotifyConfig(config.id, { is_enabled: !config.is_enabled })
      loadConfigs()
    } catch (e) {
      // handled
    }
  }

  const handleTest = async (config) => {
    try {
      await testNotify({ notify_type: config.notify_type, webhook_url: config.webhook_url })
      message.success('测试通知发送成功')
    } catch (e) {
      message.error('测试通知发送失败')
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>通知配置</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加配置</Button>
      </div>
      <Card>
        <List
          loading={loading}
          dataSource={configs}
          locale={{ emptyText: '暂无通知配置' }}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Switch checked={!!item.is_enabled} onChange={() => handleToggle(item)} checkedChildren="启用" unCheckedChildren="禁用" />,
                <Button type="link" icon={<SendOutlined />} onClick={() => handleTest(item)}>测试</Button>,
                <Popconfirm title="确认删除？" onConfirm={() => handleDelete(item.id)}>
                  <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                title={notifyTypes.find(t => t.value === item.notify_type)?.label || item.notify_type}
                description={item.webhook_url}
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal title="添加通知配置" open={modalOpen} onCancel={() => setModalOpen(false)} onOk={() => form.submit()} okText="保存">
        <Form form={form} layout="vertical" onFinish={handleAdd}>
          <Form.Item name="notify_type" label="通知类型" rules={[{ required: true, message: '请选择通知类型' }]}>
            <Select options={notifyTypes} placeholder="选择通知类型" />
          </Form.Item>
          <Form.Item name="webhook_url" label="Webhook URL" rules={[{ required: true, message: '请输入 Webhook URL' }]}>
            <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
          </Form.Item>
          <Form.Item name="is_enabled" label="启用" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

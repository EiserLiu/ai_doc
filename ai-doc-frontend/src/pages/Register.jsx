import { Card, Form, Input, Button, message, Typography } from 'antd'
import { UserOutlined, LockOutlined, BankOutlined, PhoneOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../api/auth'

const { Title } = Typography

export default function Register() {
  const navigate = useNavigate()

  const onFinish = async (values) => {
    try {
      await register(values)
      message.success('注册成功，请登录')
      navigate('/login')
    } catch (e) {
      // error handled by interceptor
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>注册账号</Title>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }, { min: 2, message: '至少2个字符' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '至少6个字符' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item name="company_name">
            <Input prefix={<BankOutlined />} placeholder="公司名称（可选）" />
          </Form.Item>
          <Form.Item name="phone">
            <Input prefix={<PhoneOutlined />} placeholder="手机号（可选）" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>注册</Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            <Link to="/login">已有账号？返回登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}

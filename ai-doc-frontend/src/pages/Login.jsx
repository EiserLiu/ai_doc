import { Card, Form, Input, Button, message, Typography } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { login, getMe } from '../api/auth'
import useAuthStore from '../store/authStore'

const { Title } = Typography

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const setUser = useAuthStore((s) => s.setUser)

  const onFinish = async (values) => {
    try {
      const res = await login(values)
      setAuth(res.access_token, null)
      const user = await getMe()
      setUser(user)
      message.success('登录成功')
      navigate('/')
    } catch (e) {
      // error handled by interceptor
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>AI 文档自动化助手</Title>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>登录</Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            <Link to="/register">没有账号？立即注册</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}

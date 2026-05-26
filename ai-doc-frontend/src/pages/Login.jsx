import { useState } from 'react'
import { Card, Form, Input, Button, message, Typography, Tabs } from 'antd'
import { UserOutlined, LockOutlined, KeyOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { login, loginByCode, getMe } from '../api/auth'
import useAuthStore from '../store/authStore'

const { Title } = Typography

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const setUser = useAuthStore((s) => s.setUser)
  const [loading, setLoading] = useState(false)

  const onLogin = async (values) => {
    setLoading(true)
    try {
      const res = await login(values)
      setAuth(res.access_token, null)
      const user = await getMe()
      setUser(user)
      message.success('登录成功')
      navigate('/')
    } catch (e) {
      // error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const onLoginByCode = async (values) => {
    setLoading(true)
    try {
      const res = await loginByCode(values)
      setAuth(res.access_token, null)
      const user = await getMe()
      setUser(user)
      message.success('登录成功')
      navigate('/')
    } catch (e) {
      // error handled by interceptor
    } finally {
      setLoading(false)
    }
  }

  const tabItems = [
    {
      key: 'password',
      label: '账号登录',
      children: (
        <Form onFinish={onLogin} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>登录</Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'code',
      label: '访问码登录',
      children: (
        <Form onFinish={onLoginByCode} size="large">
          <Form.Item name="access_code" rules={[{ required: true, message: '请输入访问码' }]}>
            <Input prefix={<KeyOutlined />} placeholder="访问码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>登录</Button>
          </Form.Item>
        </Form>
      ),
    },
  ]

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 32 }}>AI 文档自动化助手</Title>
        <Tabs items={tabItems} centered />
        <div style={{ textAlign: 'center', marginTop: 8 }}>
          <Link to="/register">没有账号？立即注册</Link>
        </div>
      </Card>
    </div>
  )
}

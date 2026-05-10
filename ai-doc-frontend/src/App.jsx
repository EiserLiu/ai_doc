import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import AppRouter from './router'

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AppRouter />
    </ConfigProvider>
  )
}

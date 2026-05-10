import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from '../components/AppLayout'
import Login from '../pages/Login'
import Register from '../pages/Register'
import Dashboard from '../pages/Dashboard'
import Upload from '../pages/Upload'
import TaskList from '../pages/TaskList'
import TaskDetail from '../pages/TaskDetail'
import NotifyConfig from '../pages/NotifyConfig'
import useAuthStore from '../store/authStore'

function PrivateRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              <AppLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/upload" element={<Upload />} />
                  <Route path="/tasks" element={<TaskList />} />
                  <Route path="/tasks/:taskNo" element={<TaskDetail />} />
                  <Route path="/notify" element={<NotifyConfig />} />
                </Routes>
              </AppLayout>
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

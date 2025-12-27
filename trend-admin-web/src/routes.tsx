import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from '@/components/Layout/AppLayout'
import Dashboard from '@/pages/Dashboard'
import Accounts from '@/pages/Accounts'
import Proxy from '@/pages/Proxy'
import Tasks from '@/pages/Tasks'
import Contents from '@/pages/Contents'

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="accounts" element={<Accounts />} />
        <Route path="proxy" element={<Proxy />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="contents/:platform" element={<Contents />} />
        <Route path="contents" element={<Navigate to="/contents/xhs" replace />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './components/layout'
import { Dashboard, Servers, ServerDetail, Groups, GroupDetail, Policies, Jobs, Alerts, Settings } from './pages'
import { AdminTenants } from './pages/admin'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="servers" element={<Servers />} />
          <Route path="servers/:id" element={<ServerDetail />} />
          <Route path="groups" element={<Groups />} />
          <Route path="groups/:id" element={<GroupDetail />} />
          <Route path="policies" element={<Policies />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="settings" element={<Settings />} />
          <Route path="admin/tenants" element={<AdminTenants />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

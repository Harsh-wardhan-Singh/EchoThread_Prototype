import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useMemo, useState } from 'react'
import Login from './pages/Login'
import Diary from './pages/Diary'
import Feed from './pages/Feed'
import PulseDashboard from './pages/PulseDashboard'
import CounselorDashboard from './pages/CounselorDashboard'

function ProtectedRoute({ role, allowedRoles, children }) {
  if (!role || !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }
  return children
}

function App() {
  const [auth, setAuth] = useState(() => {
    const role = localStorage.getItem('role')
    const email = localStorage.getItem('email')
    return {
      role,
      email,
    }
  })

  const onLogin = (role, email) => {
    localStorage.setItem('role', role)
    localStorage.setItem('email', email)
    setAuth({ role, email })
  }

  const onLogout = () => {
    localStorage.removeItem('role')
    localStorage.removeItem('email')
    setAuth({ role: null, email: null })
  }

  const authProps = useMemo(
    () => ({ role: auth.role, email: auth.email, onLogout }),
    [auth.role, auth.email],
  )

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login onLogin={onLogin} />} />
        <Route
          path="/diary"
          element={
            <ProtectedRoute role={auth.role} allowedRoles={['student']}>
              <Diary {...authProps} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/feed"
          element={
            <ProtectedRoute role={auth.role} allowedRoles={['student']}>
              <Feed {...authProps} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pulse"
          element={
            <ProtectedRoute role={auth.role} allowedRoles={['student']}>
              <PulseDashboard {...authProps} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/counselor"
          element={
            <ProtectedRoute role={auth.role} allowedRoles={['counselor']}>
              <CounselorDashboard {...authProps} />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
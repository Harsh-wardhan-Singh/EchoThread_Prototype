import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useMemo, useState } from 'react'
import Login from './pages/Login'
import Diary from './pages/Diary'
import Feed from './pages/Feed'
import PulseDashboard from './pages/PulseDashboard'
import CounselorDashboard from './pages/CounselorDashboard'
import OpenChat from './pages/OpenChat'
import { AppContainer } from './components/ui/Primitives'

function ProtectedRoute({ role, allowedRoles, children }) {
  if (!role || !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }
  return children
}

function AppRoutes({ auth, authProps, onLogin }) {
  const location = useLocation()
  const isLoginRoute = location.pathname === '/'
  const containerClass =
    isLoginRoute
      ? 'max-w-xl sm:max-w-2xl p-5 sm:p-6'
      : '!w-[98vw] !h-[98vh] !max-w-none !p-0 overflow-hidden'
  const shellClassName = isLoginRoute ? '' : '!p-[1vh]'

  return (
    <AppContainer className={containerClass} shellClassName={shellClassName}>
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
          path="/chat"
          element={
            <ProtectedRoute role={auth.role} allowedRoles={['student']}>
              <OpenChat {...authProps} />
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
    </AppContainer>
  )
}

function App() {
  const [auth, setAuth] = useState(() => {
    const role = localStorage.getItem('role')
    const email = localStorage.getItem('email')
    const sessionToken = localStorage.getItem('sessionToken')
    const userUuid = localStorage.getItem('userUuid')
    return {
      role,
      email,
      sessionToken,
      userUuid,
    }
  })

  const onLogin = (role, email, sessionToken, userUuid) => {
    localStorage.setItem('role', role)
    localStorage.setItem('email', email)
    localStorage.setItem('sessionToken', sessionToken)
    localStorage.setItem('userUuid', userUuid || '')
    setAuth({ role, email, sessionToken, userUuid })
  }

  const onLogout = () => {
    localStorage.removeItem('role')
    localStorage.removeItem('email')
    localStorage.removeItem('sessionToken')
    localStorage.removeItem('userUuid')
    setAuth({ role: null, email: null, sessionToken: null, userUuid: null })
  }

  const authProps = useMemo(
    () => ({ role: auth.role, email: auth.email, sessionToken: auth.sessionToken, userUuid: auth.userUuid, onLogout }),
    [auth.role, auth.email, auth.sessionToken, auth.userUuid],
  )

  return (
    <BrowserRouter>
      <AppRoutes auth={auth} authProps={authProps} onLogin={onLogin} />
    </BrowserRouter>
  )
}

export default App
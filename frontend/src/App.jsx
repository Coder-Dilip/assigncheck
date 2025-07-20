import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'

// Auth pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'

// Dashboard pages
import TeacherDashboard from './pages/teacher/TeacherDashboard'
import StudentDashboard from './pages/student/StudentDashboard'

// Assignment pages
import AssignmentList from './pages/assignments/AssignmentList'
import AssignmentDetail from './pages/assignments/AssignmentDetail'
import CreateAssignment from './pages/teacher/CreateAssignment'
import EditAssignment from './pages/teacher/EditAssignment'

// Submission pages
import SubmissionList from './pages/submissions/SubmissionList'
import SubmissionDetail from './pages/submissions/SubmissionDetail'
import CreateSubmission from './pages/student/CreateSubmission'

// Viva pages
import VivaSessionList from './pages/viva/VivaSessionList'
import VivaSession from './pages/viva/VivaSession'
import MockViva from './pages/viva/MockViva'
import VivaReview from './pages/teacher/VivaReview'

// Profile pages
import Profile from './pages/Profile'

// Error pages
import NotFound from './pages/NotFound'

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            {/* Dashboard routes */}
            <Route index element={<DashboardRedirect />} />
            <Route path="dashboard" element={<DashboardRedirect />} />
            <Route path="teacher/dashboard" element={
              <ProtectedRoute requireRole="teacher">
                <TeacherDashboard />
              </ProtectedRoute>
            } />
            <Route path="student/dashboard" element={
              <ProtectedRoute requireRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            } />
            
            {/* Assignment routes */}
            <Route path="assignments" element={<AssignmentList />} />
            <Route path="assignments/:id" element={<AssignmentDetail />} />
            <Route path="assignments/create" element={
              <ProtectedRoute requireRole="teacher">
                <CreateAssignment />
              </ProtectedRoute>
            } />
            <Route path="assignments/:id/edit" element={
              <ProtectedRoute requireRole="teacher">
                <EditAssignment />
              </ProtectedRoute>
            } />
            
            {/* Submission routes */}
            <Route path="submissions" element={<SubmissionList />} />
            <Route path="submissions/:id" element={<SubmissionDetail />} />
            <Route path="assignments/:assignmentId/submit" element={
              <ProtectedRoute requireRole="student">
                <CreateSubmission />
              </ProtectedRoute>
            } />
            
            {/* Viva routes */}
            <Route path="viva" element={<VivaSessionList />} />
            <Route path="viva/session/:id" element={<VivaSession />} />
            <Route path="viva/mock/:assignmentId" element={
              <ProtectedRoute requireRole="student">
                <MockViva />
              </ProtectedRoute>
            } />
            <Route path="viva/review/:sessionId" element={
              <ProtectedRoute requireRole="teacher">
                <VivaReview />
              </ProtectedRoute>
            } />
            
            {/* Profile routes */}
            <Route path="profile" element={<Profile />} />
            
            {/* 404 route */}
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </div>
    </AuthProvider>
  )
}

// Component to redirect to appropriate dashboard based on user role
const DashboardRedirect = () => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return <LoadingSpinner />
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (user.role === 'teacher') {
    return <Navigate to="/teacher/dashboard" replace />
  } else if (user.role === 'student') {
    return <Navigate to="/student/dashboard" replace />
  }
  
  return <Navigate to="/assignments" replace />
}

export default App

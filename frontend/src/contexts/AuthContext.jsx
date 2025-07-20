import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [refreshPromise, setRefreshPromise] = useState(null)

  // Function to refresh token
  const refreshToken = useCallback(async () => {
    console.log('DEBUG: Attempting to refresh token...')
    try {
      const response = await authAPI.refreshToken()
      const { access_token, user: userData } = response.data
      
      if (access_token && userData) {
        console.log('DEBUG: Token refresh successful')
        localStorage.setItem('token', access_token)
        setToken(access_token)
        setUser(userData)
        return access_token
      }
      throw new Error('Invalid token refresh response')
    } catch (error) {
      console.error('DEBUG: Token refresh failed:', error)
      logout()
      throw error
    }
  }, [])

  // Handle token refresh queue
  const getRefreshedToken = useCallback(async () => {
    if (refreshPromise) {
      console.log('DEBUG: Using existing refresh promise')
      return refreshPromise
    }
    
    console.log('DEBUG: Creating new refresh promise')
    const promise = refreshToken()
    setRefreshPromise(promise)
    
    try {
      const newToken = await promise
      return newToken
    } finally {
      setRefreshPromise(null)
    }
  }, [refreshPromise, refreshToken])

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (token) {
          console.log('DEBUG: Initial auth check with existing token')
          const response = await authAPI.getCurrentUser()
          setUser(response.data)
        }
      } catch (error) {
        console.error('DEBUG: Initial auth check failed:', error)
        if (error.response?.status === 401) {
          try {
            await getRefreshedToken()
          } catch {
            // If refresh fails, we'll stay logged out
          }
        }
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [token, getRefreshedToken])

  const login = async (credentials) => {
    try {
      console.log('DEBUG: Starting login process...')
      const response = await authAPI.login(credentials)
      console.log('DEBUG: Login response received:', response.data)
      
      const { access_token, user: userData } = response.data
      
      if (!access_token || !userData) {
        throw new Error('Invalid login response')
      }
      
      console.log('DEBUG: Login successful, storing token and user data')
      localStorage.setItem('token', access_token)
      setToken(access_token)
      setUser(userData)
      
      toast.success(`Welcome back, ${userData.full_name}!`)
      
      // Return success with redirect info for the component to handle
      const redirectTo = userData.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard'
      
      return { success: true, redirectTo }
    } catch (error) {
      console.error('DEBUG: Login error:', error)
      const message = error.response?.data?.detail || 'Login failed. Please check your credentials.'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const logout = (options = {}) => {
    const { silent = false } = options
    console.log('DEBUG: Logging out', { silent })
    
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    
    if (!silent) {
      toast.success('You have been logged out')
      // Let the component handle navigation
      window.location.href = '/login'
    }
  }

  // Check if user has required role
  const hasRole = (requiredRole) => {
    if (!user) return false
    return user.role === requiredRole
  }

  // Get auth headers for API calls
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    hasRole,
    getAuthHeaders,
    refreshToken: getRefreshedToken,
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}

export default AuthContext

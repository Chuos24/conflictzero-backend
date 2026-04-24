import React, { createContext, useState, useContext, useEffect, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import type { User, AuthContextType } from '../types'

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const token = localStorage.getItem('cz_token')
    if (token) {
      fetchUser(token)
    } else {
      setLoading(false)
    }
  }, [])

  const fetchUser = async (token: string) => {
    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      const response = await api.get('/api/v1/auth/me')
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      localStorage.removeItem('cz_token')
      delete api.defaults.headers.common['Authorization']
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const response = await api.post('/api/v1/auth/login', { email, password })
      const { access_token, user } = response.data
      
      localStorage.setItem('cz_token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      setUser(user)
      
      return { success: true }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      return {
        success: false,
        error: err.response?.data?.detail || 'Error de autenticación'
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('cz_token')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
    navigate('/login')
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

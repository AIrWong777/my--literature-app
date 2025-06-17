'use client';
// 创建React上下文
import { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

// 定义上下文类型
type AuthContextType = {
  isAuthenticated: boolean
  isLoading: boolean
  login: (token: string, refreshToken?: string) => void
  logout: () => void
}

// 创建初始值
const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  login: () => {}, // 空函数占位
  logout: () => {}
})

// 创建Provider组件
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true);

  // 组件加载时检查本地token
  useEffect(() => {
    const token = localStorage.getItem('token')
    setIsAuthenticated(!!token) // !!将值转为布尔值
    setIsLoading(false);
  }, [])

  // 登录方法
  const login = (token: string, refreshToken?: string) => {
    localStorage.setItem('token', token)
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
    setIsAuthenticated(true) 
  }

  // 注销方法
  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token');
    setIsAuthenticated(false)
    router.push('/login') // 注销后跳转到登录页
  }

  return (
    <AuthContext.Provider value={{ 
      isAuthenticated, 
      isLoading,
      login,
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  )
}

// 创建自定义hook
export const useAuth = () => useContext(AuthContext)
'use client';
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Heading } from "@/components/ui/heading";
import { Input } from "@/components/ui/input";
import { useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Link from "next/link";
import axios from 'axios'
import api from '@/lib/api' // 使用我们创建的实例


export default function Login() {
  // 使用useRef来保持表单数据，防止重新渲染时丢失
  const formRef = useRef({
    phone_number: '',
    password: ''
  });
  
  const { login } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState('login');
  const [formData, setFormData] = useState({
    phone_number: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

// 输入处理 ================================
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target
    
    // 同时更新state和ref
    formRef.current[id as keyof typeof formRef.current] = value;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }))
    
    // 用户开始输入时清除错误信息
    if(error) setError('')
  }, [error])

  // 提交处理 ================================
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    e.stopPropagation() // 阻止事件冒泡
    
    console.log('登录提交开始', { 
      formData: formData,
      formRef: formRef.current 
    })
    
    // 使用ref中的数据进行验证，防止state丢失
    const currentData = {
      phone_number: formRef.current.phone_number || formData.phone_number,
      password: formRef.current.password || formData.password
    };
    
    // 前端验证
    if (!/^\d{11}$/.test(currentData.phone_number)) {
      setError('手机号必须为11位数字')
      console.log('手机号验证失败')
      return false
    }

    if (!currentData.password.trim()) {
      setError('请输入密码')
      console.log('密码验证失败')
      return false
    }

    try {
      setIsLoading(true)
      setError('') // 清除之前的错误信息
      
      console.log('开始调用登录API', currentData)
      
      // 调用登录接口
      const response = await api.post('/api/auth/login', {
        phone_number: currentData.phone_number,
        password: currentData.password
      })

      console.log('登录API调用成功', response.data)
      
      login(response.data.access_token, response.data.refresh_token);
      
      console.log('准备跳转到主页面')
      // 跳转到主页面
      router.push('/main');
    } catch (err) {
      console.log('登录失败', err)
      // 登录失败时不清空表单，只显示错误信息
      if (axios.isAxiosError(err)) {
        const errorMessage = err.response?.data?.detail || '登录失败，请检查手机号和密码'
        console.log('设置错误信息:', errorMessage)
        setError(errorMessage)
        
        // 确保表单数据不丢失
        setTimeout(() => {
          console.log('错误后检查表单数据:', {
            formData: formData,
            formRef: formRef.current
          });
          
          // 如果formData被清空了，从ref恢复
          if (!formData.phone_number && formRef.current.phone_number) {
            setFormData({
              phone_number: formRef.current.phone_number,
              password: formRef.current.password
            });
          }
        }, 100);
        
      } else {
        console.log('网络错误:', err)
        setError('网络连接异常，请稍后重试')
      }
      // 注意：这里不清空formData，保持用户输入的内容
    } finally {
      setIsLoading(false)
      console.log('登录流程结束')
    }
    
    return false // 确保不会导致页面刷新
  }, [formData, error, login, router])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white">
      {/* 顶部标签页容器（添加背景色） */}
      <div className="w-98 max-w-md mb-6 bg-gray-50 rounded-lg p-1">
        <div className="flex">
          {/* 登录按钮（根据状态动态设置样式） */}
          <Button
            variant={activeTab === 'login' ? 'secondary' : 'outline'}
            className={`w-48 py-2 transition-all duration-200 ${
              activeTab === 'login' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => setActiveTab('login')}
            type="button"
          >
            登录账号
          </Button>
          
          {/* 注册按钮（根据状态动态设置样式） */}
          <Link 
            href="/register" >
          <Button
            variant={activeTab === 'register' ? 'secondary' : 'outline'}
            className={`w-48 py-2 transition-all duration-200 ${
              activeTab === 'register' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => setActiveTab('register')}
            type="button"
          >
            注册账号
          </Button>
          </Link>
        </div>
      </div>
      {/* 登录表单 */}
      <Card className="flex flex-col items-start space-y-0 p-5 w-96">
        <Heading as="h2" size="lg">
          登录账号
        </Heading>
        <p className="text-gray-500 -mt-4">
          欢迎回来
        </p>
        <form className="flex flex-col space-y-4 w-full" onSubmit={handleSubmit} noValidate>
          <label htmlFor="phone_number" className="text-sm">
            手机号
          </label>
          <Input
            id="phone_number"
            placeholder="请输入手机号"
            className="w-full"
            value={formData.phone_number}
            onChange={handleInputChange}
            disabled={isLoading}
            autoComplete="tel"
          />
          <label htmlFor="password" className="text-sm">
            密码
          </label>
          <Input
            id="password"
            placeholder="请输入密码"
            type="password"
            className="w-full"
            value={formData.password}
            onChange={handleInputChange}
            disabled={isLoading}
            autoComplete="current-password"
          />

          {/* 错误提示 - 改进样式，使其更明显且持久 */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 text-sm p-3 rounded-md">
              <div className="flex items-center">
                <span className="mr-2">⚠️</span>
                <span>{error}</span>
              </div>
            </div>
          )}

          <Button 
            className="px-8 py-2 w-full mt-5"
            type="submit"
            disabled={isLoading} // 加载时禁用
          >
            {isLoading ? '登录中...' : '登录'}
          </Button>
        </form>
      </Card>
    </div>
  );
}
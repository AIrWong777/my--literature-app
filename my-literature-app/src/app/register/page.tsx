'use client';
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Heading } from "@/components/ui/heading";
import { Input } from "@/components/ui/input";
import { useState } from 'react';
import Link from "next/link";
import axios from "axios";
import React from 'react';

export default function Register() {
  // 状态管理：记录当前激活的标签页
  const [activeTab, setActiveTab] = useState('register');

  // 状态1：表单数据存储
  // 作用：跟踪用户输入的所有字段值
  const [formData, setFormData] = useState({
    username: '',        // 用户名输入值
    phone_number: '',    // 手机号输入值
    password: '',        // 密码输入值
    password_confirm: '' // 确认密码输入值
  });

  // 状态2：错误提示信息
  // 作用：显示后端返回或前端验证的错误
  const [error, setError] = useState('');

  // 状态3：加载状态
  // 作用：防止重复提交，显示加载提示
  const [isLoading, setIsLoading] = useState(false);
  
  // 输入处理函数 ================================
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    // 更新对应字段的状态值
    setFormData(prev => ({
      ...prev,         // 保留其他字段值
      [id]: value      // 动态更新当前修改的字段
    }));
    
    // 清空错误提示（当用户开始修改时）
    if(error) setError('');
  };

  // 表单提交函数 ================================
  const handleSubmit = async () => {
    // 前端验证阶段 ----------
    if (!formData.username) {
      setError('用户名不能为空');
      return;
    }
    if (!/^\d{11}$/.test(formData.phone_number)) {
      setError('手机号必须为11位数字');
      return;
    }
    if (formData.password.length < 8) {
      setError('密码至少需要8位字符');
      return;
    }
    if (formData.password !== formData.password_confirm) {
      setError('两次输入的密码不一致');
      return;
    }

    // 网络请求阶段 ----------
    setIsLoading(true); // 开始加载
    try {
      const response = await axios.post(
        'http://localhost:8000/api/auth/register',
        {
          username: formData.username,
          phone_number: formData.phone_number,
          password: formData.password,
          password_confirm: formData.password_confirm
        }
      );

      // 成功处理
      if (response.status === 201) {
        window.location.href = '/login'; // 跳转登录页
      }
    } catch (err) {
      // 错误处理
      if (axios.isAxiosError(err)) {
        setError(err.response?.data.detail || '注册失败，请稍后重试');
      } else {
        setError('网络连接异常，请检查网络');
      }
    } finally {
      setIsLoading(false); // 结束加载
    }
  };

  // 组件渲染阶段 ================================
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white">
      {/* 顶部标签页容器（添加背景色） */}
      <div className="w-98 max-w-md mb-6 bg-gray-50 rounded-lg p-1">
        <div className="flex">
          {/* 登录按钮（根据状态动态设置样式） */}
          <Link 
            href="/login">
          <Button
            variant={activeTab === 'login' ? 'secondary' : 'outline'}
            className={`w-48 py-2 transition-all duration-200 ${
              activeTab === 'login' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => setActiveTab('login')}
          >
            登录账号
          </Button>
          </Link>
          
          {/* 注册按钮（根据状态动态设置样式） */}
          <Button
            variant={activeTab === 'register' ? 'secondary' : 'outline'}
            className={`w-48 py-2 transition-all duration-200 ${
              activeTab === 'register' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => setActiveTab('register')}
          >
            注册账号
          </Button>
        </div>
      </div>
      {/* 注册表单 */}
      <Card className="flex flex-col items-start space-y-0 p-5 w-96">
        <Heading as="h2" size="lg">
          注册账号
        </Heading>
        <p className="text-gray-500 -mt-4">
          欢迎使用
        </p>
        <div className="flex flex-col space-y-4 w-full">
          <label htmlFor="username" className="text-sm">
            用户名
          </label>
          <Input
            id="username"
            placeholder="请输入用户名"
            className="w-full -mt-2"
            value={formData.username} // 绑定状态值
            onChange={handleInputChange} // 输入时更新状态
            disabled={isLoading} // 加载时禁用
          />
          <label htmlFor="phone_number" className="text-sm">
            手机号
          </label>
          <Input
            id="phone_number"
            placeholder="请输入手机号"
            className="w-full -mt-2"
            value={formData.phone_number}
            onChange={handleInputChange}
            disabled={isLoading}
          />
          <label htmlFor="password" className="text-sm">
            密码
          </label>
          <Input
            id="password"
            placeholder="请输入密码"
            type="password"
            className="w-full -mt-2"
            value={formData.password}
            onChange={handleInputChange}
            disabled={isLoading}
          />
          <label htmlFor="password_confirm" className="text-sm">
            确认密码
          </label>
          <Input
            id="password_confirm"
            placeholder="请再次输入密码"
            type="password"
            className="w-full -mt-2"
            value={formData.password_confirm}
            onChange={handleInputChange}
            disabled={isLoading}
          />

          {/* 错误提示 */}
          {error && (
            <div className="text-red-500 text-sm mt-2">
              ⚠️ {error}
            </div>
          )}

          <Button 
            className="px-8 py-2 w-full mt-5" 
            onClick={handleSubmit} // 绑定提交函数
            disabled={isLoading} // 加载时禁用
          >
            {isLoading ? '注册中...' : '注册'}
          </Button>
        </div>
      </Card>
    </div>
  );
}
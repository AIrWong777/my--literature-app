'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import api from '@/lib/api';
import { toast } from 'sonner';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BsArrowLeft, BsTrash, BsCloudUpload, BsDatabase } from 'react-icons/bs';
import ProtectedRoute from '@/components/ProtectedRoute';

// 存储统计接口
interface StorageStats {
  total_size: number;
  file_count: number;
  average_size: number;
  largest_file: {
    id: string;
    filename: string;
    size: number;
  };
  by_type: {
    [key: string]: {
      count: number;
      total_size: number;
    };
  };
}

// 缓存统计接口
interface CacheStats {
  hit_rate: number;
  miss_rate: number;
  item_count: number;
  memory_usage: number;
  types: {
    [key: string]: {
      count: number;
      memory_usage: number;
    };
  };
}

export default function AdminPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  
  // 存储统计状态
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [isCleaningStorage, setIsCleaningStorage] = useState(false);
  
  // 缓存统计状态
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [isClearingCache, setIsClearingCache] = useState(false);
  
  // 检查是否为管理员
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }
    
    // 这里应该根据实际情况检查用户是否为管理员
    // 假设用户对象中有一个is_admin字段
    if (user && user.is_admin) {
      setIsAdmin(true);
      loadAdminData();
    } else {
      toast.error('权限不足', {
        description: '您没有管理员权限'
      });
      router.replace('/home');
    }
  }, [isAuthenticated, router, user]);
  
  // 加载管理员数据
  const loadAdminData = async () => {
    try {
      setLoading(true);
      
      // 并行加载数据
      const [storageResponse, cacheResponse] = await Promise.all([
        api.get('/admin/storage/stats'),
        api.get('/cache_admin/stats')
      ]);
      
      setStorageStats(storageResponse.data);
      setCacheStats(cacheResponse.data);
    } catch (error) {
      console.error('加载管理员数据失败:', error);
      toast.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 清理存储
  const handleCleanupStorage = async () => {
    try {
      setIsCleaningStorage(true);
      const response = await api.post('/admin/storage/cleanup');
      
      toast.success('存储清理完成', {
        description: `已释放 ${formatFileSize(response.data.freed_space || 0)} 空间`
      });
      
      // 重新加载存储统计
      const storageResponse = await api.get('/admin/storage/stats');
      setStorageStats(storageResponse.data);
    } catch (error) {
      console.error('存储清理失败:', error);
      toast.error('存储清理失败');
    } finally {
      setIsCleaningStorage(false);
    }
  };
  
  // 清理缓存
  const handleClearCache = async () => {
    try {
      setIsClearingCache(true);
      await api.post('/cache_admin/clear');
      
      toast.success('缓存清理完成');
      
      // 重新加载缓存统计
      const cacheResponse = await api.get('/cache_admin/stats');
      setCacheStats(cacheResponse.data);
    } catch (error) {
      console.error('缓存清理失败:', error);
      toast.error('缓存清理失败');
    } finally {
      setIsClearingCache(false);
    }
  };
  
  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // 格式化百分比
  const formatPercent = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };
  
  if (loading || !isAdmin) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900"></div>
      </div>
    );
  }
  
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* 顶部导航 */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push('/home')}
                  className="flex items-center space-x-2"
                >
                  <BsArrowLeft className="w-4 h-4" />
                  <span>返回主页</span>
                </Button>
                <div className="h-6 w-px bg-gray-300" />
                <h1 className="text-2xl font-bold text-gray-900">管理员控制台</h1>
              </div>
              <div className="flex items-center space-x-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadAdminData}
                >
                  刷新数据
                </Button>
              </div>
            </div>
          </div>
        </header>
        
        {/* 主要内容 */}
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Tabs defaultValue="storage">
            <TabsList className="mb-6">
              <TabsTrigger value="storage">存储管理</TabsTrigger>
              <TabsTrigger value="cache">缓存管理</TabsTrigger>
            </TabsList>
            
            {/* 存储管理标签页 */}
            <TabsContent value="storage">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 存储概览 */}
                <Card>
                  <CardHeader>
                    <CardTitle>存储概览</CardTitle>
                    <CardDescription>系统存储使用情况</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {storageStats ? (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">总存储大小</div>
                            <div className="text-2xl font-bold">{formatFileSize(storageStats.total_size)}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">文件数量</div>
                            <div className="text-2xl font-bold">{storageStats.file_count}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">平均文件大小</div>
                            <div className="text-2xl font-bold">{formatFileSize(storageStats.average_size)}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">最大文件</div>
                            <div className="text-lg font-bold truncate">{formatFileSize(storageStats.largest_file?.size || 0)}</div>
                            <div className="text-xs text-gray-500 truncate">{storageStats.largest_file?.filename || 'N/A'}</div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">加载存储统计中...</div>
                    )}
                  </CardContent>
                  <CardFooter>
                    <Button
                      onClick={handleCleanupStorage}
                      disabled={isCleaningStorage || !storageStats}
                      className="w-full"
                    >
                      {isCleaningStorage ? '清理中...' : '清理存储'}
                    </Button>
                  </CardFooter>
                </Card>
                
                {/* 文件类型分布 */}
                <Card>
                  <CardHeader>
                    <CardTitle>文件类型分布</CardTitle>
                    <CardDescription>按文件类型统计</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {storageStats?.by_type ? (
                      <div className="space-y-4">
                        {Object.entries(storageStats.by_type).map(([type, data]) => (
                          <div key={type} className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                              <span className="text-sm font-medium">{type}</span>
                            </div>
                            <div className="text-sm">
                              {data.count} 个文件 / {formatFileSize(data.total_size)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">无文件类型数据</div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
            
            {/* 缓存管理标签页 */}
            <TabsContent value="cache">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 缓存概览 */}
                <Card>
                  <CardHeader>
                    <CardTitle>缓存概览</CardTitle>
                    <CardDescription>系统缓存使用情况</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {cacheStats ? (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">命中率</div>
                            <div className="text-2xl font-bold">{formatPercent(cacheStats.hit_rate)}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">未命中率</div>
                            <div className="text-2xl font-bold">{formatPercent(cacheStats.miss_rate)}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">缓存项数量</div>
                            <div className="text-2xl font-bold">{cacheStats.item_count}</div>
                          </div>
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <div className="text-sm text-gray-500">内存使用</div>
                            <div className="text-2xl font-bold">{formatFileSize(cacheStats.memory_usage)}</div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">加载缓存统计中...</div>
                    )}
                  </CardContent>
                  <CardFooter>
                    <Button
                      onClick={handleClearCache}
                      disabled={isClearingCache || !cacheStats}
                      className="w-full"
                    >
                      {isClearingCache ? '清理中...' : '清理缓存'}
                    </Button>
                  </CardFooter>
                </Card>
                
                {/* 缓存类型分布 */}
                <Card>
                  <CardHeader>
                    <CardTitle>缓存类型分布</CardTitle>
                    <CardDescription>按缓存类型统计</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {cacheStats?.types ? (
                      <div className="space-y-4">
                        {Object.entries(cacheStats.types).map(([type, data]) => (
                          <div key={type} className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <div className="w-2 h-2 rounded-full bg-green-500"></div>
                              <span className="text-sm font-medium">{type}</span>
                            </div>
                            <div className="text-sm">
                              {data.count} 项 / {formatFileSize(data.memory_usage)}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">无缓存类型数据</div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </ProtectedRoute>
  );
} 
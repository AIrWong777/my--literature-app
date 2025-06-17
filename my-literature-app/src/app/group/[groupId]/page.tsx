'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useAuth } from '@/context/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import api from '@/lib/api';
import { toast } from 'sonner';
import { BsSearch, BsDownload, BsEye, BsTrash, BsPeople, BsFiles, BsArrowLeft, BsArrowClockwise, BsBarChart } from "react-icons/bs";

// 接口定义
interface GroupInfo {
  id: string;
  name: string;
  institution: string;
  description: string;
  research_area: string;
}

interface GroupMember {
  id: string;
  username: string;
  phone_number: string;
}

interface Literature {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_time: string;
  uploader_name: string;
}

interface LiteratureStats {
  total_count: number;
  total_size: number;
  by_type: {
    [key: string]: {
      count: number;
      total_size: number;
    };
  };
  by_uploader: {
    [key: string]: {
      count: number;
      total_size: number;
    };
  };
  by_month: {
    [key: string]: number;
  };
}

export default function GroupPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const groupId = params.groupId as string;

  // 状态管理
  const [groupInfo, setGroupInfo] = useState<GroupInfo | null>(null);
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([]);
  const [literature, setLiterature] = useState<Literature[]>([]);
  const [deletedLiterature, setDeletedLiterature] = useState<Literature[]>([]);
  const [showDeletedItems, setShowDeletedItems] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'literature' | 'members' | 'deleted' | 'stats'>('literature');
  const [isLeavingGroup, setIsLeavingGroup] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  const [literatureStats, setLiteratureStats] = useState<LiteratureStats | null>(null);
  const [showStats, setShowStats] = useState(false);

  // 获取课题组信息
  const fetchGroupInfo = async () => {
    try {
      const response = await api.get(`/groups/${groupId}/info`);
      setGroupInfo(response.data);
    } catch (error) {
      console.error('获取课题组信息失败:', error);
      toast.error('获取课题组信息失败');
    }
  };

  // 获取课题组成员
  const fetchGroupMembers = async () => {
    try {
      const response = await api.get(`/groups/${groupId}/members`);
      setGroupMembers(response.data.members);
    } catch (error) {
      console.error('获取课题组成员失败:', error);
      toast.error('获取课题组成员失败');
    }
  };

  // 获取课题组文献
  const fetchGroupLiterature = async () => {
    try {
      const response = await api.get(`/literature/public/${groupId}`);
      setLiterature(response.data.literature);
    } catch (error) {
      console.error('获取课题组文献失败:', error);
      toast.error('获取课题组文献失败');
    }
  };

  // 获取已删除文献
  const fetchDeletedLiterature = async () => {
    try {
      const response = await api.get(`/literature/deleted/${groupId}`);
      setDeletedLiterature(response.data.literature || []);
    } catch (error) {
      console.error('获取已删除文献失败:', error);
      toast.error('获取已删除文献失败');
    }
  };

  // 获取文献统计
  const fetchLiteratureStats = async () => {
    try {
      const response = await api.get(`/literature/stats/${groupId}`);
      setLiteratureStats(response.data);
    } catch (error) {
      console.error('获取文献统计失败:', error);
      toast.error('获取文献统计失败');
    }
  };

  // 页面初始化
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
      return;
    }

    if (groupId) {
      Promise.all([
        fetchGroupInfo(),
        fetchGroupMembers(),
        fetchGroupLiterature(),
        fetchDeletedLiterature()
      ]).finally(() => {
        setLoading(false);
      });
    }
  }, [groupId, isAuthenticated, router]);

  // 文献搜索过滤
  const filteredLiterature = literature.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.uploader_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 文件大小格式化
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 下载文献
  const handleDownload = async (literatureId: string, filename: string) => {
    try {
      toast.loading('正在准备下载...');
      
      // 使用axios发起带认证的请求
      const response = await api.get(`/literature/download/${literatureId}`, {
        responseType: 'blob' // 重要：指定响应类型为blob
      });
      
      // 创建blob URL
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      // 创建下载链接
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // 清理
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('下载成功');
    } catch (error: any) {
      console.error('下载失败:', error);
      toast.error('下载失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 查看文献
  const handleView = async (literatureId: string) => {
    try {
      toast.loading('正在打开文献...');
      
      // 使用axios发起带认证的请求
      const response = await api.get(`/literature/view/file/${literatureId}`, {
        responseType: 'blob' // 重要：指定响应类型为blob
      });
      
      // 创建blob URL
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      
      // 在新窗口中打开
      const newWindow = window.open(url, '_blank');
      if (!newWindow) {
        toast.error('请允许弹窗以查看文献');
        return;
      }
      
      toast.success('文献已打开');
      
      // 延迟清理URL（给浏览器时间加载文件）
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
      }, 1000);
    } catch (error: any) {
      console.error('查看失败:', error);
      toast.error('查看失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 恢复文献
  const handleRestoreLiterature = async (literatureId: string) => {
    try {
      setIsRestoring(true);
      await api.post(`/literature/${literatureId}/restore`);
      toast.success('文献已恢复');
      
      // 刷新数据
      await fetchDeletedLiterature();
      await fetchGroupLiterature();
    } catch (error) {
      console.error('恢复文献失败:', error);
      toast.error('恢复文献失败');
    } finally {
      setIsRestoring(false);
    }
  };

  // 退出课题组函数
  const handleLeaveGroup = async () => {
    try {
      setIsLeavingGroup(true);
      await api.post(`/groups/${groupId}/leave`);
      toast.success('已退出课题组');
      router.push('/home');
    } catch (error) {
      console.error('退出课题组失败:', error);
      toast.error('退出课题组失败');
      setIsLeavingGroup(false);
    }
  };

  if (!isAuthenticated || loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!groupInfo) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-600 mb-2">课题组不存在</h2>
          <Button onClick={() => router.push('/home')}>返回主页</Button>
        </div>
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
                <h1 className="text-2xl font-bold text-gray-900">{groupInfo.name}</h1>
                <Badge variant="secondary">{groupInfo.research_area}</Badge>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">{groupInfo.institution}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLeaveConfirm(true)}
                  className="text-red-500 border-red-200 hover:bg-red-50"
                >
                  退出课题组
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* 添加退出确认对话框 */}
        {showLeaveConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
              <h3 className="text-lg font-medium mb-4">确认退出课题组</h3>
              <p className="text-gray-600 mb-6">
                您确定要退出"{groupInfo.name}"课题组吗？退出后将无法访问该课题组的文献，除非重新加入。
              </p>
              <div className="flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowLeaveConfirm(false)}
                  disabled={isLeavingGroup}
                >
                  取消
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleLeaveGroup}
                  disabled={isLeavingGroup}
                >
                  {isLeavingGroup ? '退出中...' : '确认退出'}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* 主要内容 */}
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* 课题组描述 */}
          {groupInfo.description && (
            <Card className="mb-6">
              <CardContent className="p-4">
                <p className="text-gray-700">{groupInfo.description}</p>
              </CardContent>
            </Card>
          )}

          {/* 标签页切换 */}
          <div className="flex space-x-1 mb-6">
            <Button
              variant={activeTab === 'literature' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('literature')}
              className="flex items-center space-x-2"
            >
              <BsFiles className="w-4 h-4" />
              <span>文献库 ({literature.length})</span>
            </Button>
            <Button
              variant={activeTab === 'members' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('members')}
              className="flex items-center space-x-2"
            >
              <BsPeople className="w-4 h-4" />
              <span>成员 ({groupMembers.length})</span>
            </Button>
            <Button
              variant={activeTab === 'deleted' ? 'default' : 'ghost'}
              onClick={() => {
                setActiveTab('deleted');
                fetchDeletedLiterature();
              }}
              className="flex items-center space-x-2"
            >
              <BsTrash className="w-4 h-4" />
              <span>回收站</span>
            </Button>
            <Button
              variant={activeTab === 'stats' ? 'default' : 'ghost'}
              onClick={() => {
                setActiveTab('stats');
                fetchLiteratureStats();
              }}
              className="flex items-center space-x-2"
            >
              <BsBarChart className="w-4 h-4" />
              <span>统计</span>
            </Button>
          </div>

          {/* 文献库标签页 */}
          {activeTab === 'literature' && (
            <div className="space-y-4">
              {/* 搜索栏 */}
              <div className="flex items-center space-x-4">
                <div className="relative flex-1 max-w-md">
                  <Input
                    type="text"
                    placeholder="搜索文献..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                  <BsSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                </div>
                <Button onClick={() => router.push('/main')} variant="outline">
                  上传文献
                </Button>
              </div>

              {/* 文献列表 */}
              <Card>
                <CardHeader>
                  <CardTitle>文献列表</CardTitle>
                </CardHeader>
                <CardContent>
                  {filteredLiterature.length === 0 ? (
                    <div className="text-center py-8">
                      <BsFiles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">
                        {searchQuery ? '没有找到匹配的文献' : '暂无文献，点击上传添加第一篇文献'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {filteredLiterature.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                        >
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 mb-1">{item.title}</h3>
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <span>{item.filename}</span>
                              <span>{formatFileSize(item.file_size)}</span>
                              <span>上传者: {item.uploader_name}</span>
                              <span>{new Date(item.upload_time).toLocaleDateString()}</span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleView(item.id)}
                              title="查看文献"
                            >
                              <BsEye className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDownload(item.id, item.filename)}
                              title="下载文献"
                            >
                              <BsDownload className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 成员标签页 */}
          {activeTab === 'members' && (
            <Card>
              <CardHeader>
                <CardTitle>课题组成员</CardTitle>
              </CardHeader>
              <CardContent>
                {groupMembers.length === 0 ? (
                  <div className="text-center py-8">
                    <BsPeople className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">暂无成员信息</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {groupMembers.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center space-x-3 p-4 border rounded-lg"
                      >
                        <Avatar>
                          <AvatarFallback>
                            {member.username.charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <h4 className="font-medium text-gray-900">{member.username}</h4>
                          <p className="text-sm text-gray-500">{member.phone_number}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 已删除文献标签页 */}
          {activeTab === 'deleted' && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>已删除文献</CardTitle>
                </CardHeader>
                <CardContent>
                  {deletedLiterature.length === 0 ? (
                    <div className="text-center py-8">
                      <BsTrash className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">回收站中没有文献</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {deletedLiterature.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                        >
                          <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-medium text-gray-900 truncate">
                              {item.title || item.filename}
                            </h3>
                            <div className="flex items-center text-xs text-gray-500 mt-1">
                              <span className="truncate">
                                {item.file_type} · {formatFileSize(item.file_size)} · 上传者: {item.uploader_name}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4 flex items-center space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRestoreLiterature(item.id)}
                              disabled={isRestoring}
                              className="flex items-center space-x-1"
                            >
                              <BsArrowClockwise className="w-3 h-3" />
                              <span>恢复</span>
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 统计标签页 */}
          {activeTab === 'stats' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>文献统计</CardTitle>
                  <CardDescription>课题组文献数据统计</CardDescription>
                </CardHeader>
                <CardContent>
                  {!literatureStats ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900 mx-auto"></div>
                      <p className="mt-2 text-gray-500">加载统计数据...</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* 基本统计 */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-500">文献总数</div>
                          <div className="text-2xl font-bold">{literatureStats.total_count}</div>
                        </div>
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-500">总存储大小</div>
                          <div className="text-2xl font-bold">{formatFileSize(literatureStats.total_size)}</div>
                        </div>
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <div className="text-sm text-gray-500">平均文件大小</div>
                          <div className="text-2xl font-bold">
                            {literatureStats.total_count > 0 
                              ? formatFileSize(literatureStats.total_size / literatureStats.total_count) 
                              : '0 B'}
                          </div>
                        </div>
                      </div>
                      
                      {/* 文件类型分布 */}
                      <div>
                        <h3 className="text-lg font-medium mb-3">文件类型分布</h3>
                        <div className="space-y-2">
                          {Object.entries(literatureStats.by_type || {}).map(([type, data]) => (
                            <div key={type} className="flex items-center">
                              <div 
                                className="h-2 bg-blue-500 rounded-full" 
                                style={{ 
                                  width: `${Math.max(5, (data.count / literatureStats.total_count) * 100)}%` 
                                }}
                              ></div>
                              <div className="ml-3 flex justify-between w-full">
                                <span className="text-sm font-medium">{type}</span>
                                <span className="text-sm text-gray-500">
                                  {data.count} 个文件 ({formatFileSize(data.total_size)})
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* 上传者分布 */}
                      <div>
                        <h3 className="text-lg font-medium mb-3">上传者分布</h3>
                        <div className="space-y-2">
                          {Object.entries(literatureStats.by_uploader || {}).map(([uploader, data]) => (
                            <div key={uploader} className="flex items-center">
                              <div 
                                className="h-2 bg-green-500 rounded-full" 
                                style={{ 
                                  width: `${Math.max(5, (data.count / literatureStats.total_count) * 100)}%` 
                                }}
                              ></div>
                              <div className="ml-3 flex justify-between w-full">
                                <span className="text-sm font-medium">{uploader}</span>
                                <span className="text-sm text-gray-500">
                                  {data.count} 个文献 ({formatFileSize(data.total_size)})
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* 月度上传趋势 */}
                      <div>
                        <h3 className="text-lg font-medium mb-3">月度上传趋势</h3>
                        <div className="h-40 flex items-end space-x-2">
                          {Object.entries(literatureStats.by_month || {})
                            .sort()
                            .map(([month, count]) => {
                              const maxCount = Math.max(...Object.values(literatureStats.by_month || {}));
                              const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
                              return (
                                <div key={month} className="flex flex-col items-center flex-1">
                                  <div 
                                    className="w-full bg-blue-400 rounded-t" 
                                    style={{ height: `${Math.max(5, height)}%` }}
                                  ></div>
                                  <div className="text-xs mt-1 text-gray-500">{month}</div>
                                </div>
                              );
                            })
                          }
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
} 
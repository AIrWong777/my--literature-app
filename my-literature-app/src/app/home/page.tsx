'use client';
import React, { useEffect, useState } from 'react';
import { Text } from '@/components/ui/text';
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from '@/components/ui/input';
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { AiOutlineUser } from "react-icons/ai";
import { BsSearch } from "react-icons/bs";
import ProtectedRoute from '@/components/ProtectedRoute'
import api from '@/lib/api';
import '@/app/globals.css';

// 新增导入
import { createResearchGroup } from '@/lib/api/researchGroup';
import { ResearchGroup } from '@/lib/api/types';
import { toast } from 'sonner'; // 使用 Sonner 的 toast

// 新增: 加入课题组对话框的Props接口
interface JoinGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void; // 新增成功回调
}

// 课题组信息接口
interface GroupInfo {
  id: string;
  name: string;
  institution: string;
  description: string;
  research_area: string;
}

// 新增: 加入课题组对话框组件
const JoinGroupDialog: React.FC<JoinGroupDialogProps> = ({ open, onOpenChange, onSuccess }) => {
  const [inviteCode, setInviteCode] = useState('');
  const [groupInfo, setGroupInfo] = useState<GroupInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState('');

  // 查询课题组信息
  const handleSearchGroup = async () => {
    if (!inviteCode.trim()) {
      setError('请输入邀请码');
      return;
    }

    setLoading(true);
    setError('');
    setGroupInfo(null);

    try {
      const response = await api.get(`/groups/info/${inviteCode.trim()}`);
      setGroupInfo(response.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('无效的邀请码，请检查后重试');
      } else {
        setError('查询课题组信息失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  // 加入课题组
  const handleJoinGroup = async () => {
    if (!groupInfo) return;

    setJoining(true);
    setError('');

    const toastId = toast.loading('正在加入课题组...');

    try {
      const params = new URLSearchParams();
      params.append('invitation_code', inviteCode.trim());
      
      const response = await api.post('/groups/join-by-code', params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      toast.success('加入成功', {
        description: '您已成功加入课题组',
        id: toastId
      });

      // 关闭对话框并重置状态
      onOpenChange(false);
      resetState();

      // 调用成功回调刷新课题组列表
      if (onSuccess) {
        onSuccess();
      }

    } catch (err: any) {
      let errorMsg = "加入课题组失败";
      if (err.response?.status === 400) {
        errorMsg = err.response.data.detail || '加入课题组失败';
      }
      
      toast.error('加入失败', {
        description: errorMsg,
        id: toastId
      });
      setError(errorMsg);
    } finally {
      setJoining(false);
    }
  };

  const handleInviteCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInviteCode(value);
    
    // 清除之前的状态
    if (groupInfo) {
      setGroupInfo(null);
    }
    if (error) {
      setError('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading && inviteCode.trim() && !groupInfo) {
      handleSearchGroup();
    }
  };

  const resetState = () => {
    setInviteCode('');
    setGroupInfo(null);
    setError('');
    setLoading(false);
    setJoining(false);
  };

  // 对话框关闭时重置状态
  const handleOpenChange = (newOpen: boolean) => {
    onOpenChange(newOpen);
    if (!newOpen) {
      resetState();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl font-semibold text-gray-900">加入课题组</DialogTitle>
          <p className="mt-2 text-sm text-gray-500">请输入课题组邀请码</p>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center">
              <Label htmlFor="inviteCode" className="text-sm font-medium text-gray-700">
                邀请码
              </Label>
              <span className="text-red-500 ml-1">*</span>
            </div>
            <div className="flex space-x-2">
              <Input
                id="inviteCode"
                value={inviteCode}
                onChange={handleInviteCodeChange}
                onKeyPress={handleKeyPress}
                placeholder="请输入8位邀请码"
                className={`flex-1 h-10 focus:ring-2 focus:ring-black focus:border-transparent ${
                  error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300'
                }`}
                disabled={loading || joining}
              />
              {!groupInfo && (
                <Button
                  onClick={handleSearchGroup}
                  disabled={loading || !inviteCode.trim()}
                  className="px-4 bg-black hover:bg-gray-800 text-white whitespace-nowrap"
                >
                  {loading ? '查询中...' : '查询'}
                </Button>
              )}
            </div>
          </div>

          {/* 课题组信息显示 */}
          {groupInfo && (
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium text-gray-900">课题组信息</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">名称：</span>
                  <span className="text-gray-900 font-medium">{groupInfo.name}</span>
                </div>
                <div>
                  <span className="text-gray-600">机构：</span>
                  <span className="text-gray-900">{groupInfo.institution}</span>
                </div>
                <div>
                  <span className="text-gray-600">研究领域：</span>
                  <span className="text-gray-900">{groupInfo.research_area}</span>
                </div>
                {groupInfo.description && (
                  <div>
                    <span className="text-gray-600">描述：</span>
                    <span className="text-gray-900">{groupInfo.description}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 错误信息 */}
        {error && (
          <Alert className="bg-red-50 text-red-800 border border-red-200">
            <AlertDescription>
              {error}
            </AlertDescription>
          </Alert>
        )}
        
        <div className="flex space-x-4 pt-2">
          {groupInfo ? (
            <>
              <Button
                onClick={handleJoinGroup}
                disabled={joining}
                className="flex-1 bg-black hover:bg-gray-800 text-white !rounded-button whitespace-nowrap cursor-pointer"
              >
                {joining ? '加入中...' : '加入'}
              </Button>
              <Button
                onClick={() => {
                  setGroupInfo(null);
                  setInviteCode('');
                  setError('');
                }}
                variant="outline"
                className="flex-1 border-black text-black hover:bg-gray-100 !rounded-button whitespace-nowrap cursor-pointer"
                disabled={joining}
              >
                重新查询
              </Button>
            </>
          ) : (
            <Button
              onClick={() => handleOpenChange(false)}
              variant="outline"
              className="w-full border-black text-black hover:bg-gray-100 !rounded-button whitespace-nowrap cursor-pointer"
              disabled={loading}
            >
              返回
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const [userName, setUsername] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // 创建课题组状态
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [createFormData, setCreateFormData] = useState({
    name: '',
    institution: '',
    description: '',
    research_area: ''
  });
  
  // 新增: 加入课题组状态
  const [isJoinDialogOpen, setIsJoinDialogOpen] = useState(false);
  
  // 新增: 创建加载状态
  const [isCreating, setIsCreating] = useState(false);
  
  // 新增: 用户研究组列表
  const [userGroups, setUserGroups] = useState<ResearchGroup[]>([]);

  // 在组件中添加管理员状态
  const [isAdmin, setIsAdmin] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setCreateFormData(prev => ({ ...prev, [name]: value }));
  };

  // 修改: 添加创建课题组的API调用 - 使用Sonner toast
  const handleCreateSubmit = async () => {
    // 验证必填字段
    if (!createFormData.name.trim()) {
      toast.error("课题组名称不能为空");
      return;
    }
    
    if (!createFormData.institution.trim()) {
      toast.error("所属机构不能为空");
      return;
    }
    
    // 显示加载状态
    const toastId = toast.loading("创建课题组中...", {
      description: "请稍候"
    });
    
    try {
      setIsCreating(true);
      
      // 调用创建研究组 API
      const response = await createResearchGroup(createFormData);
      
      // 显示成功提示
      toast.success("创建成功", {
        description: `课题组 "${response.data?.name ?? ''}" 已成功创建`,
        duration: 3000,
        id: toastId
      });
      
      // 重置表单并关闭对话框
      setCreateFormData({
        name: '',
        institution: '',
        description: '',
        research_area: ''
      });
      setIsCreateDialogOpen(false);
      
      // 刷新研究组列表
      await fetchUserGroups();
      
      console.log('课题组创建成功:', response.data);
      
    } catch (error: any) {
      // 处理错误
      console.error('创建课题组失败:', error);
      
      let errorMessage = '创建课题组失败，请稍后重试';
      
      // 根据错误状态码显示不同的错误信息
      if (error.response) {
        switch (error.response.status) {
          case 400:
            errorMessage = '参数错误：请检查填写的信息是否完整';
            break;
          case 401:
            errorMessage = '未授权：请重新登录';
            break;
          case 409:
            errorMessage = '课题组名称已存在，请使用其他名称';
            break;
          default:
            errorMessage = `服务器错误：${error.response.data.detail || error.message}`;
        }
      }
      
      // 显示错误提示
      toast.error("创建失败", {
        description: errorMessage,
        duration: 5000,
        id: toastId
      });
    } finally {
      setIsCreating(false);
    }
  };

  // 新增: 获取用户研究组列表
  const fetchUserGroups = async () => {
    try {
      const response = await api.get('/user/groups');
      setUserGroups(response.data.groups);
      console.log('用户研究组列表:', response.data.groups);
    } catch (error) {
      console.error('获取研究组失败', error);
      toast.error("获取研究组失败", {
        description: "无法加载您的研究组列表"
      });
    }
  };

  // 页面保护：未登录直接跳转
  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  // 拉取用户信息和研究组列表
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await api.get('/api/user/me');
        setUsername(response.data.username);
        // 检查是否为管理员
        setIsAdmin(response.data.is_admin === true);
      } catch (error) {
        console.error('获取用户信息失败');
        setUsername('未知用户');
        toast.error("获取用户信息失败");
      } finally {
        setLoading(false);
      }
    };
    
    if (isAuthenticated) {
      fetchUser();
      fetchUserGroups();
    }
  }, [isAuthenticated]);

  // 页面保护和加载状态
  if (!isAuthenticated || loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      {/* 顶部导航栏 */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <div className="flex items-center">
          <div className="w-6 h-6 mr-2 text-black">
            <i className="fas fa-file-alt"></i>
          </div>
          <h1 className="text-lg font-medium text-black">AI+协同文献管理平台</h1>
        </div>
        
        <div className="flex-1 mx-6">
          <div className="relative">
            <Input
              type="text"
              placeholder="搜索文献..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-400 text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-400">
              <BsSearch className="w-4 h-4" />
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <Button
            variant="ghost"
            className="mr-2"
            onClick={() => router.push('/main')}
            title="点击返回主界面"
          >
            {userName}
          </Button>
          {isAdmin && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/admin')}
              className="mr-2"
            >
              管理控制台
            </Button>
          )}
          {isAuthenticated && (
            <Button variant="outline" size="sm" onClick={logout}>
              退出登录
            </Button>
          )}
        </div>
      </header>
      <div className="flex justify-center bg-white px-4 sm:px-8 relative mt-12">
        <Card className="w-full max-w-none p-2 bg-gray-200 shadow-md rounded-lg h-100%">
          <div className="w-full bg-gray-200 flex flex-col items-center py-10">
            <AiOutlineUser className="w-24 h-24 rounded-full bg-white mb-4" />
            <div className="text-black text-2xl font-bold mb-1">{userName}</div>
            <div className="text-gray-400 mb-6">(个人主页)</div>
            <div className="flex gap-24 mb-6">
              <Button
                onClick={() => setIsCreateDialogOpen(true)}
                className="px-8 py-2 text-lg border border-white bg-black text-white hover:bg-gray-700 hover:text-white rounded-full"
                variant="outline"
              >
                创建课题组
              </Button>
              {/* 修改: 为加入课题组按钮添加点击事件 */}
              <Button
                onClick={() => setIsJoinDialogOpen(true)}
                className="px-8 py-2 text-lg border border-white bg-white text-black hover:bg-gray-100 rounded-full"
                variant="outline"
              >
                加入课题组
              </Button>
            </div>

            {/* 新增: 用户课题组列表 */}
            {userGroups.length > 0 && (
              <div className="w-full max-w-4xl mt-8">
                <h2 className="text-xl font-semibold text-black mb-4 text-center">我的课题组</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {userGroups.map((group) => (
                    <Card
                      key={group.id}
                      className="p-4 bg-white hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                      onClick={() => router.push(`/group/${group.id}`)}
                    >
                      <CardContent className="p-0">
                        <div className="space-y-2">
                          <h3 className="font-semibold text-lg text-black truncate">{group.name}</h3>
                          <p className="text-sm text-gray-600">{group.institution}</p>
                          <p className="text-sm text-gray-500 line-clamp-2">{group.description}</p>
                          <div className="flex items-center justify-between pt-2">
                            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                              {group.research_area}
                            </span>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-blue-600 hover:text-blue-800 text-xs"
                              onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/group/${group.id}`);
                              }}
                            >
                              进入 →
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* 新增: 空状态提示 */}
            {userGroups.length === 0 && (
              <div className="w-full max-w-md mt-8 text-center">
                <div className="text-gray-500 mb-4">
                  <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-600 mb-2">还没有加入任何课题组</h3>
                  <p className="text-sm text-gray-400 mb-4">创建一个新课题组或加入现有课题组开始协作</p>
                </div>
              </div>
            )}
          </div>
        </Card>
      
      {/* 创建课题组对话框 */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold">创建新课题组</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="name" className="text-right font-medium text-gray-700">
                课题组名称
              </label>
              <Input
                id="name"
                name="name"
                value={createFormData.name}
                onChange={handleInputChange}
                className="col-span-3"
                placeholder="请输入课题组名称"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="institution" className="text-right font-medium text-gray-700">
                所属机构
              </label>
              <Input
                id="institution"
                name="institution"
                value={createFormData.institution}
                onChange={handleInputChange}
                className="col-span-3"
                placeholder="请输入所属机构"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-start gap-4">
              <label htmlFor="description" className="text-right font-medium text-gray-700 pt-2">
                课题描述
              </label>
              <Textarea
                id="description"
                name="description"
                value={createFormData.description}
                onChange={handleInputChange}
                className="col-span-3"
                placeholder="请输入课题描述"
                rows={3}
              />
            </div>
            <div className="grid grid-cols-4 items-start gap-4">
              <label htmlFor="research_area" className="text-right font-medium text-gray-700 pt-2">
                研究方向
              </label>
              <Textarea
                id="research_area"
                name="research_area"
                value={createFormData.research_area}
                onChange={handleInputChange}
                className="col-span-3"
                placeholder="请输入研究方向"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter className="sm:justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateDialogOpen(false)}
              className="!rounded-button whitespace-nowrap cursor-pointer"
              disabled={isCreating}
            >
              返回
            </Button>
            <Button
              type="button"
              onClick={handleCreateSubmit}
              className="!rounded-button whitespace-nowrap cursor-pointer bg-black hover:bg-gray-800 text-white"
              disabled={isCreating}
            >
              {isCreating ? (
                <>
                  <span className="mr-2">创建中...</span>
                  <span className="animate-spin">⏳</span>
                </>
              ) : (
                "完成创建"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* 新增: 加入课题组对话框 */}
      <JoinGroupDialog 
        open={isJoinDialogOpen}
        onOpenChange={setIsJoinDialogOpen}
        onSuccess={fetchUserGroups}
      />
      </div>
    </ProtectedRoute>
  );
}
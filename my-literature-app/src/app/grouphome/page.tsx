// The exported code uses Tailwind CSS. Install Tailwind CSS in your dev environment to ensure all styles work.
'use client';
import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { LiteratureAPI } from '@/lib/api/literature';

const App: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, logout } = useAuth();
  const [inputValue, setInputValue] = useState('');
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showExitDialog, setShowExitDialog] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  
  // 课题组信息状态
  const [groupInfo, setGroupInfo] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentGroupId, setCurrentGroupId] = useState<string>('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // 从URL参数获取groupId
    const groupId = searchParams.get('groupId');
    if (!groupId) {
      router.push('/home');
      return;
    }

    setCurrentGroupId(groupId);
    loadGroupData(groupId);
  }, [isAuthenticated, searchParams]);

  const loadGroupData = async (groupId: string) => {
    try {
      setLoading(true);
      
      // 并行加载课题组信息和成员列表
      const [groupInfoRes, membersRes] = await Promise.all([
        LiteratureAPI.getGroupInfo(groupId),
        LiteratureAPI.getGroupMembers(groupId)
      ]);

      setGroupInfo(groupInfoRes);
      setMembers(membersRes.members || []);
    } catch (error) {
      console.error('加载课题组数据失败:', error);
      alert('加载课题组信息失败，请重试');
      router.push('/home');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    if (inputValue.trim()) {
      console.log('Sending message:', inputValue);
      setInputValue('');
    }
  };

  const copyInviteInfo = () => {
    if (!groupInfo) return;
    
    const textToCopy = `课题组名称：${groupInfo.name}\n课题组ID：${currentGroupId}\n邀请链接：${window.location.origin}/join?groupId=${currentGroupId}`;
    navigator.clipboard.writeText(textToCopy);
    alert('邀请信息已复制到剪贴板');
  };

  const handleExitGroup = async () => {
    setIsLeaving(true);
    try {
      await LiteratureAPI.leaveGroup(currentGroupId);
      alert('成功退出课题组');
      router.push('/home');
    } catch (error) {
      console.error('退出课题组失败:', error);
      alert('退出课题组失败，请重试');
    } finally {
      setIsLeaving(false);
    setShowExitDialog(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">加载课题组信息中...</p>
        </div>
      </div>
    );
  }

  if (!groupInfo) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">课题组信息加载失败</p>
          <Button onClick={() => router.push('/home')} className="mt-4">返回主页</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 w-full max-w-[1440px] mx-auto">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm py-4 px-6 flex items-center justify-between">
        <div className="flex items-center">
          <i className="fas fa-book-open text-blue-500 mr-3 text-xl"></i>
          <span className="font-medium text-gray-800 text-lg">文献管理平台</span>
        </div>
        <div className="flex items-center gap-5">
          <div className="relative">
            <Input
              type="text"
              placeholder="搜索文献..."
              className="w-64 pr-8 border-gray-200 text-sm"
            />
            <i className="fas fa-search absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"></i>
          </div>
          <i className="fas fa-cloud-upload-alt text-gray-600 cursor-pointer text-lg"></i>
          <Avatar className="h-9 w-9 cursor-pointer">
            <AvatarImage src="" alt="用户头像" />
            <AvatarFallback className="bg-gray-200 text-gray-700">张三</AvatarFallback>
          </Avatar>
        </div>
      </header>

      {/* 主要内容区域 */}
      <main className="p-8 min-h-[calc(1024px-72px)]">
        <div className="max-w-5xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{groupInfo.name}</h1>
              <p className="text-sm text-gray-500">ID: {currentGroupId}</p>
              <p className="text-sm text-gray-500 mt-1">{groupInfo.institution}</p>
              {groupInfo.description && (
                <p className="text-sm text-gray-600 mt-2">{groupInfo.description}</p>
              )}
            </div>
            
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-gray-800">成员列表</h2>
              <Button 
                variant="outline" 
                className="!rounded-button whitespace-nowrap border-gray-300 hover:bg-gray-100"
                onClick={() => setShowInviteDialog(true)}
              >
                <i className="fas fa-user-plus mr-2"></i>
                邀请成员
              </Button>
            </div>
            
            <div className="border rounded-lg overflow-hidden">
              <ScrollArea className="h-[400px]">
                <div className="divide-y">
                  {members.map((member) => (
                    <div key={member.id} className="flex items-center justify-between p-4 hover:bg-gray-50">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarImage src="" alt={member.username} />
                          <AvatarFallback className="bg-gray-200 text-gray-700">{member.username.charAt(0)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium text-gray-800">{member.username}</p>
                          <p className="text-sm text-gray-500">{member.phone_number}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
          
          <div className="flex justify-end">
            <Button 
              variant="destructive" 
              className="!rounded-button whitespace-nowrap text-white hover:bg-gray-800"
              onClick={() => setShowExitDialog(true)}
            >
              <i className="fas fa-sign-out-alt mr-2"></i>
              退出课题组
            </Button>
          </div>
        </div>
      </main>

      {/* 邀请成员弹窗 */}
      <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-center">邀请新成员</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <p className="text-sm text-gray-700">课题组名称：{groupInfo.name}</p>
              <p className="text-sm text-gray-700">课题组ID：{currentGroupId}</p>
              <p className="text-sm text-gray-700">邀请链接：{window.location.origin}/join?groupId={currentGroupId}</p>
            </div>
          </div>
          <DialogFooter>
            <Button 
              className="w-full !rounded-button whitespace-nowrap bg-black text-white hover:bg-gray-800"
              onClick={copyInviteInfo}
            >
              <i className="fas fa-copy mr-2"></i>
              复制信息
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 退出课题组弹窗 */}
      <Dialog open={showExitDialog} onOpenChange={setShowExitDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-center text-red-600">确认退出课题组</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <div className="text-center space-y-2">
              <p className="text-gray-700">是否确认退出课题组：</p>
              <p className="font-medium text-gray-900">"{groupInfo?.name}"</p>
              <p className="text-sm text-red-600">退出后将无法访问该课题组的文献和数据</p>
            </div>
          </div>
          <DialogFooter className="flex justify-center gap-4">
            <Button 
              className="!rounded-button whitespace-nowrap bg-red-600 text-white hover:bg-red-700"
              onClick={handleExitGroup}
              disabled={isLeaving}
            >
              {isLeaving ? '退出中...' : '确认退出'}
            </Button>
            <Button 
              variant="outline" 
              className="!rounded-button whitespace-nowrap border-gray-300"
              onClick={() => setShowExitDialog(false)}
              disabled={isLeaving}
            >
              取消
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default App;

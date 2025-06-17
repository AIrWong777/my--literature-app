'use client';

// The exported code uses Tailwind CSS. Install Tailwind CSS in your dev environment to ensure all styles work.

import React, { useState } from 'react';
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getGroupByInviteCode, joinGroupByCode } from '@/lib/api/researchGroup';
import { useRouter } from 'next/navigation';

interface GroupInfo {
  id: string;
  name: string;
  institution: string;
  description: string;
  research_area: string;
}

const App: React.FC = () => {
  const router = useRouter();
  const [inviteCode, setInviteCode] = useState('');
  const [groupInfo, setGroupInfo] = useState<GroupInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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
      const response = await getGroupByInviteCode(inviteCode.trim());
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

    try {
      const response = await joinGroupByCode(inviteCode.trim());
      setSuccess(response.data.message);
      
      // 延迟跳转到主页
      setTimeout(() => {
        router.push('/main');
      }, 2000);
    } catch (err: any) {
      if (err.response?.status === 400) {
        setError(err.response.data.detail || '加入课题组失败');
      } else {
        setError('加入课题组失败，请稍后重试');
      }
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
    if (success) {
      setSuccess('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading && inviteCode.trim() && !groupInfo) {
      handleSearchGroup();
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-white py-12 px-4">
      <div className="w-full max-w-md">
        <Card className="p-8 shadow-md border border-gray-100">
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-semibold text-gray-900">加入课题组</h1>
              <p className="mt-2 text-sm text-gray-500">请输入课题组邀请码</p>
            </div>
            
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

            {/* 成功信息 */}
            {success && (
              <Alert className="bg-green-50 text-green-800 border border-green-200">
                <AlertDescription>
                  {success} 正在跳转到主页...
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
                    {joining ? '加入中...' : '加入课题组'}
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
                  onClick={() => router.push('/main')}
                  variant="outline" 
                  className="w-full border-black text-black hover:bg-gray-100 !rounded-button whitespace-nowrap cursor-pointer"
                  disabled={loading}
                >
                  返回主页
                </Button>
              )}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default App;

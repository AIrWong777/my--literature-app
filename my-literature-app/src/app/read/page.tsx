// The exported code uses Tailwind CSS. Install Tailwind CSS in your dev environment to ensure all styles work.
'use client';
import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const App: React.FC = () => {
  const [question, setQuestion] = useState('');

  return (
    <div className="min-h-[1024px] w-full bg-white">
      {/* 顶部导航栏 */}
      <header className="h-[60px] px-6 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center">
          <i className="fas fa-book-open text-blue-500 text-2xl"></i>
          <span className="ml-2 text-lg font-medium">文献管理平台</span>
        </div>
        <div className="flex items-center">
          <div className="relative mr-4">
            <Input
              type="text"
              placeholder="搜索文献..."
              className="w-[300px] h-9 pl-9 text-sm border-gray-300"
            />
            <i className="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm"></i>
          </div>
          <Button variant="ghost" size="icon" className="mr-2 !rounded-button whitespace-nowrap cursor-pointer">
            <i className="fas fa-share-alt text-gray-500"></i>
          </Button>
          <Avatar className="h-10 w-10 cursor-pointer">
            <AvatarImage src="https://readdy.ai/api/search-image?query=professional%20portrait%20photo%20of%20asian%20man%20with%20glasses%2C%20minimalist%20style%2C%20clean%20background%2C%20high%20quality%2C%20professional%20look&width=100&height=100&seq=1&orientation=squarish" alt="张三" />
            <AvatarFallback>张三</AvatarFallback>
          </Avatar>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-6">
        {/* 文献标题区域 */}
        <div className="py-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold mb-3">深度学习在自然语言处理中的应用研究</h1>
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
            <span>作者：李四 等</span>
            <Badge variant="outline" className="bg-gray-100 text-gray-600 font-normal">深度学习</Badge>
            <Badge variant="outline" className="bg-gray-100 text-gray-600 font-normal">NLP</Badge>
            <span className="ml-auto">2023-12-20</span>
          </div>
        </div>

        {/* 功能按钮组 */}
        <div className="py-4 flex items-center gap-4 overflow-x-auto">
          <Button variant="outline" className="flex items-center gap-2 !rounded-button whitespace-nowrap cursor-pointer">
            <i className="fas fa-download"></i>
            <span>下载PDF</span>
          </Button>
          <Button variant="outline" className="flex items-center gap-2 !rounded-button whitespace-nowrap cursor-pointer">
            <i className="fas fa-highlighter"></i>
            <span>高亮工具</span>
          </Button>
          <Button variant="outline" className="flex items-center gap-2 !rounded-button whitespace-nowrap cursor-pointer">
            <i className="fas fa-quote-right"></i>
            <span>复制引用</span>
          </Button>
          <Button variant="outline" className="flex items-center gap-2 !rounded-button whitespace-nowrap cursor-pointer">
            <i className="fas fa-plus-circle"></i>
            <span>添加批注</span>
          </Button>
          <Button className="flex items-center gap-2 bg-black hover:bg-black/90 !rounded-button whitespace-nowrap cursor-pointer">
            <i className="fas fa-robot"></i>
            <span>AI助手</span>
          </Button>
        </div>

        {/* 主体内容区域 */}
        <div className="flex gap-6 py-6">
          {/* 左侧文献内容 */}
          <div className="w-[70%]">
            <div className="bg-white rounded-lg p-6">
              <section>
                <h2 className="text-lg font-bold mb-4">摘要</h2>
                <p className="text-base leading-7 mb-4">
                  随着人工智能技术的快速发展，深度学习在自然语言处理领域展现出了巨大的潜力和广泛的应用前景。本文系统地探讨了深度学习在自然语言处理中的应用研究...
                </p>
              </section>
              <section>
                <h2 className="text-lg font-bold mt-6 mb-4">1. 引言</h2>
                <p className="text-base leading-7 mb-4">
                  <span className="bg-[#FFF3D4]">自然语言处理是人工智能的重要分支，其目标是使计算机能够理解、生成人类语言。</span>
                  近年来，深度学习技术的突破为自然语言处理带来了革命性的进展。本文将详细讨论深度学习在自然语言处理中的具体应用及其影响。
                </p>
              </section>
              <section>
                <h2 className="text-lg font-bold mt-6 mb-4">2. 研究背景</h2>
                <p className="text-base leading-7 mb-4">
                  传统的自然语言处理方法主要依赖于人工设计的特征和规则，这种方法存在泛化能力差、维护成本高等问题。深度学习的出现解决了这些问题...
                </p>
              </section>
            </div>
          </div>

          {/* 右侧互动区域 */}
          <div className="w-[30%]">
            {/* AI助手 */}
            <Card className="mb-6 p-4 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="bg-blue-100 p-2 rounded-full">
                    <i className="fas fa-robot text-blue-500"></i>
                  </div>
                  <h3 className="font-medium">AI助手</h3>
                </div>
                <Button variant="ghost" size="sm" className="!rounded-button whitespace-nowrap cursor-pointer">
                  <i className="fas fa-expand-alt text-gray-500"></i>
                </Button>
              </div>
              <div className="relative">
                <Input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="有问题尽管问我..."
                  className="pr-10 text-sm"
                />
                <Button
                  className="absolute right-0 top-0 h-full aspect-square !rounded-button whitespace-nowrap cursor-pointer"
                  variant="ghost"
                >
                  <i className="fas fa-paper-plane text-blue-500"></i>
                </Button>
              </div>
            </Card>

            {/* 批注列表 */}
            <Card className="p-4 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium">批注列表</h3>
                <Badge variant="outline" className="bg-gray-100 text-gray-600 font-normal cursor-pointer">
                  <i className="fas fa-plus mr-1 text-xs"></i> 添加
                </Badge>
              </div>
              <ScrollArea className="h-[300px] pr-4">
                <div className="space-y-4">
                  <div className="border-l-2 border-blue-400 pl-3 py-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback>我</AvatarFallback>
                      </Avatar>
                      <span className="text-sm font-medium">我的批注</span>
                      <span className="text-xs text-gray-500 ml-auto">10:30</span>
                    </div>
                    <p className="text-sm text-gray-700">
                      这段对传统NLP方法的分析很到位，可以作为论文的重要参考。
                    </p>
                  </div>
                  <div className="border-l-2 border-green-400 pl-3 py-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback>王</AvatarFallback>
                      </Avatar>
                      <span className="text-sm font-medium">王教授</span>
                      <span className="text-xs text-gray-500 ml-auto">昨天</span>
                    </div>
                    <p className="text-sm text-gray-700">
                      这篇论文的方法论部分需要进一步完善，建议补充更多实验数据。
                    </p>
                  </div>
                  <div className="border-l-2 border-purple-400 pl-3 py-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback>赵</AvatarFallback>
                      </Avatar>
                      <span className="text-sm font-medium">赵研究员</span>
                      <span className="text-xs text-gray-500 ml-auto">05-25</span>
                    </div>
                    <p className="text-sm text-gray-700">
                      文中提到的深度学习模型在实际应用中可能会遇到计算资源不足的问题，值得讨论。
                    </p>
                  </div>
                </div>
              </ScrollArea>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

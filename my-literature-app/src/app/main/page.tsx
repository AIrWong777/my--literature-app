// The exported code uses Tailwind CSS. Install Tailwind CSS in your dev environment to ensure all styles work.
'use client';
import React, { useState, useEffect, useRef } from "react";
import { Card } from '@/components/ui/card';
import { Heading } from '@/components/ui/heading';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { AiOutlineFolderOpen } from "react-icons/ai";
import { RxShare2 } from "react-icons/rx";
import { BsSearch } from "react-icons/bs";
import { ChevronRight, Folder, File, Upload, X, Eye, Download, Trash2, MessageCircle, Send, Star, ThumbsUp, ThumbsDown, Lightbulb } from "lucide-react";
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/ProtectedRoute'
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Resizable } from 're-resizable';
import { LiteratureAPI } from '@/lib/api/literature';

// 类型定义
interface Document {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  file_type: string;
  upload_time: string;
  uploader_name?: string;
}

interface GroupLibrary {
  groupId: string;
  groupName: string;
  documents: Document[];
}

interface LibraryTree {
  private: Document[];
  groups: GroupLibrary[];
}

interface SelectedLibrary {
  type: 'private' | 'group';
  groupId?: string;
}

// AI助手相关类型
interface ConversationTurn {
  turn_id: string;
  turn_index: number;
  timestamp: string;
  question: string;
  answer: string;
  key_findings?: string[];
  limitations?: string;
  confidence: number;
  processing_time: number;
  user_rating?: number;
  sources?: Array<{
    content: string;
    page: number;
    confidence: number;
  }>;
}

interface AISession {
  session_id: string;
  literature_id: string;
  literature_title: string;
  created_at: string;
  last_activity: string;
  turn_count: number;
  preview: string;
}

interface AIAssistantState {
  isOpen: boolean;
  selectedLiterature: Document | null;
  currentSessionId: string | null;
  conversation: ConversationTurn[];
  isLoading: boolean;
  presetQuestions: string[];
  sessions: AISession[];
  showHistory: boolean;
}

const App: React.FC = () => {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuth();
  const [userName, setUsername] = useState('');
  const [searchQuery, setSearchQuery] = useState("");
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [privateLibraryExpanded, setPrivateLibraryExpanded] = useState(false);
  const [publicLibraryExpanded, setPublicLibraryExpanded] = useState(false);
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedLibrary, setSelectedLibrary] = useState<{type: 'private' | 'group', groupId?: string}>({ type: 'private' });
  
  // 上传相关状态
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 删除确认对话框状态
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [literatureToDelete, setLiteratureToDelete] = useState<Document | null>(null);
  const [deleteReason, setDeleteReason] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  // 搜索相关状态
  const [filteredLibraryTree, setFilteredLibraryTree] = useState<LibraryTree>({
    private: [],
    groups: [],
  });

  // AI助手状态
  const [aiAssistant, setAiAssistant] = useState<AIAssistantState>({
    isOpen: false,
    selectedLiterature: null,
    currentSessionId: null,
    conversation: [],
    isLoading: false,
    presetQuestions: [],
    sessions: [],
    showHistory: false,
  });

  // AI助手输入状态
  const [aiQuestion, setAiQuestion] = useState("");
  const [isAIThinking, setIsAIThinking] = useState(false);
  const aiInputRef = useRef<HTMLInputElement>(null);

  const [libraryTree, setLibraryTree] = useState<LibraryTree>({
    private: [],
    groups: [], // 支持多个课题组
  });

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = localStorage.getItem('token');
    axios.get('http://localhost:8000/api/user/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
   .then(res => {
      setUsername(res.data.username);
   })
    .catch(() => {
      logout();
      router.push('/login');
   });
    
    // 加载文献数据
    loadLibraryData();
  }, [isAuthenticated, logout, router]);

  // 加载文献库数据
  const loadLibraryData = async () => {
    try {
      // 获取私人文献
      const privateData = await LiteratureAPI.getPrivateLiterature();
      
      // 获取用户课题组
      const groupsData = await LiteratureAPI.getUserGroups();
      
      // 获取每个课题组的文献
      const groupsWithLiterature = await Promise.all(
        groupsData.groups.map(async (group: any) => {
          try {
            const literatureData = await LiteratureAPI.getGroupLiterature(group.id);
            return {
              groupId: group.id,
              groupName: group.name,
              documents: literatureData.literature || []
            };
          } catch (error) {
            console.error(`获取课题组 ${group.name} 文献失败:`, error);
            return {
              groupId: group.id,
              groupName: group.name,
              documents: []
            };
          }
        })
      );
      
      setLibraryTree({
        private: privateData.literature || [],
        groups: groupsWithLiterature
      });
    } catch (error) {
      console.error('加载文献库失败:', error);
    }
  };

  // 搜索过滤功能
  const filterLibraryData = (query: string) => {
    if (!query.trim()) {
      setFilteredLibraryTree(libraryTree);
      return;
    }

    const lowerQuery = query.toLowerCase();
    
    // 过滤私人文献
    const filteredPrivate = libraryTree.private.filter(doc =>
      doc.title.toLowerCase().includes(lowerQuery) ||
      doc.filename.toLowerCase().includes(lowerQuery) ||
      doc.file_type.toLowerCase().includes(lowerQuery)
    );

    // 过滤课题组文献
    const filteredGroups = libraryTree.groups.map(group => ({
      ...group,
      documents: group.documents.filter(doc =>
        doc.title.toLowerCase().includes(lowerQuery) ||
        doc.filename.toLowerCase().includes(lowerQuery) ||
        doc.file_type.toLowerCase().includes(lowerQuery) ||
        (doc.uploader_name && doc.uploader_name.toLowerCase().includes(lowerQuery))
      )
    }));

    setFilteredLibraryTree({
      private: filteredPrivate,
      groups: filteredGroups
    });
  };

  // 监听搜索查询变化
  useEffect(() => {
    filterLibraryData(searchQuery);
  }, [searchQuery, libraryTree]);

  // 文件拖拽处理
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        setUploadTitle(file.name.replace(/\.[^/.]+$/, "")); // 移除扩展名作为默认标题
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
        setUploadTitle(file.name.replace(/\.[^/.]+$/, "")); // 移除扩展名作为默认标题
      }
    }
  };

  const validateFile = (file: File): boolean => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (!allowedTypes.includes(file.type)) {
      alert('只支持PDF和Word文档格式');
      return false;
    }
    
    if (file.size > maxSize) {
      alert('文件大小不能超过50MB');
      return false;
    }
    
    return true;
  };

  const handleUpload = () => {
    setUploadDialogOpen(true);
    setSelectedFile(null);
    setUploadTitle("");
    setUploadProgress(0);
  };

  const handleCloseDialog = () => {
    setUploadDialogOpen(false);
    setSelectedFile(null);
    setUploadTitle("");
    setUploadProgress(0);
  };

  const handleConfirmUpload = async () => {
    if (!selectedFile) {
      alert('请先选择文件');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      let uploadResult;
      
      if (selectedLibrary.type === 'private') {
        // 上传到私人库
        uploadResult = await LiteratureAPI.uploadPrivateLiterature(
          selectedFile, 
          uploadTitle || undefined
        );
      } else if (selectedLibrary.groupId) {
        // 上传到课题组
        uploadResult = await LiteratureAPI.uploadGroupLiterature(
          selectedFile, 
          selectedLibrary.groupId, 
          uploadTitle || undefined
        );
      }

      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 100;
          }
          return prev + 10;
        });
      }, 100);

      // 上传成功后重新加载数据
      await loadLibraryData();
      
      setUploadProgress(100);
      setTimeout(() => {
        setIsUploading(false);
        setUploadDialogOpen(false);
        setSelectedFile(null);
        setUploadTitle("");
        setUploadProgress(0);
      }, 500);

      console.log('上传成功:', uploadResult);
    } catch (error) {
      console.error('上传失败:', error);
      alert('上传失败，请重试');
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化上传时间
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  // 查看文献
  const handleViewLiterature = async (literatureId: string, filename: string) => {
    try {
      const response = await LiteratureAPI.viewLiterature(literatureId);
      
      // 创建临时URL并在新窗口中打开
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      
      // 清理URL
      setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (error) {
      console.error('查看文献失败:', error);
      alert('查看文献失败，请重试');
    }
  };

  // 下载文献
  const handleDownloadLiterature = async (literatureId: string, filename: string) => {
    try {
      const response = await LiteratureAPI.downloadLiterature(literatureId);
      
      // 创建下载链接
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // 清理URL
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载文献失败:', error);
      alert('下载文献失败，请重试');
    }
  };

  // 打开删除确认对话框
  const handleDeleteLiterature = (doc: Document) => {
    setLiteratureToDelete(doc);
    setDeleteDialogOpen(true);
    setDeleteReason("");
  };

  // 确认删除文献
  const confirmDeleteLiterature = async () => {
    if (!literatureToDelete) return;

    setIsDeleting(true);
    try {
      await LiteratureAPI.deleteLiterature(literatureToDelete.id, deleteReason || undefined);
      
      // 重新加载数据
      await loadLibraryData();
      
      // 关闭对话框
      setDeleteDialogOpen(false);
      setLiteratureToDelete(null);
      setDeleteReason("");
      
      alert('文献删除成功');
    } catch (error) {
      console.error('删除文献失败:', error);
      alert('删除文献失败，请重试');
    } finally {
      setIsDeleting(false);
    }
  };

  // 取消删除
  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setLiteratureToDelete(null);
    setDeleteReason("");
  };

  // === AI助手相关函数 ===

  // 打开AI助手
  const openAIAssistant = async (literature: Document) => {
    setAiAssistant(prev => ({
      ...prev,
      isOpen: true,
      selectedLiterature: literature,
      isLoading: true,
    }));

    try {
      // 加载预设问题
      const presetData = await LiteratureAPI.getPresetQuestions(literature.id);
      
      // 加载该文献的会话历史
      const sessionsData = await LiteratureAPI.getAISessions({
        literature_id: literature.id,
        limit: 10
      });

      setAiAssistant(prev => ({
        ...prev,
        presetQuestions: presetData.questions || [],
        sessions: sessionsData.sessions || [],
        isLoading: false,
      }));
    } catch (error) {
      console.error('加载AI助手数据失败:', error);
      setAiAssistant(prev => ({
        ...prev,
        isLoading: false,
        presetQuestions: [
          "请总结这篇文献的核心论点",
          "这篇文献的主要研究方法是什么？",
          "文献中有哪些重要的实验结果？",
          "这篇文献的创新点在哪里？",
          "文献中提到了哪些局限性？"
        ],
      }));
    }
  };

  // 关闭AI助手
  const closeAIAssistant = () => {
    setAiAssistant(prev => ({
      ...prev,
      isOpen: false,
      selectedLiterature: null,
      currentSessionId: null,
      conversation: [],
      showHistory: false,
    }));
    setAiQuestion("");
  };

  // 发送AI问题
  const sendAIQuestion = async (question: string) => {
    if (!question.trim() || !aiAssistant.selectedLiterature) return;

    setIsAIThinking(true);
    setAiQuestion("");

    // 添加用户消息后滚动到底部
    setTimeout(() => {
      const chatBottom = document.getElementById('chat-bottom');
      if (chatBottom) {
        chatBottom.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);

    try {
      const response = await LiteratureAPI.askAI({
        question: question.trim(),
        literature_id: aiAssistant.selectedLiterature.id,
        session_id: aiAssistant.currentSessionId || undefined,
        max_sources: 5,
        include_history: true,
      });

      // 更新对话历史 - 添加安全检查
      const newTurn: ConversationTurn = {
        turn_id: response.turn_id || Date.now().toString(),
        turn_index: aiAssistant.conversation.length + 1,
        timestamp: new Date().toISOString(),
        question: question.trim(),
        answer: response.answer || "抱歉，无法生成答案",
        key_findings: Array.isArray(response.key_findings) ? response.key_findings : [],
        limitations: response.limitations || "",
        confidence: typeof response.confidence === 'number' ? response.confidence : 0.0,
        processing_time: typeof response.metadata?.processing_time === 'number' ? response.metadata.processing_time : 0.0,
        sources: Array.isArray(response.sources) ? response.sources.map((source: any) => ({
          content: source.text || "",
          page: source.chunk_index || 0,
          confidence: typeof source.similarity === 'number' ? source.similarity : 0.0
        })) : [],
      };

      setAiAssistant(prev => ({
        ...prev,
        currentSessionId: response.session_id || prev.currentSessionId,
        conversation: [...prev.conversation, newTurn],
      }));

      // AI回答完成后滚动到底部
      setTimeout(() => {
        const chatBottom = document.getElementById('chat-bottom');
        if (chatBottom) {
          chatBottom.scrollIntoView({ behavior: 'smooth' });
        }
      }, 200);

      // 重新加载会话列表
      if (aiAssistant.selectedLiterature) {
        try {
          const sessionsData = await LiteratureAPI.getAISessions({
            literature_id: aiAssistant.selectedLiterature.id,
            limit: 10
          });
          setAiAssistant(prev => ({
            ...prev,
            sessions: sessionsData.sessions || [],
          }));
        } catch (sessionError) {
          console.warn('重新加载会话列表失败:', sessionError);
        }
      }
    } catch (error) {
      console.error('AI问答失败:', error);
      alert('AI问答失败，请重试');
    } finally {
      setIsAIThinking(false);
    }
  };

  // 使用预设问题
  const usePresetQuestion = (question: string) => {
    setAiQuestion(question);
    if (aiInputRef.current) {
      aiInputRef.current.focus();
    }
  };

  // 加载会话历史
  const loadConversationHistory = async (sessionId: string) => {
    try {
      setAiAssistant(prev => ({ ...prev, isLoading: true }));
      
      const historyData = await LiteratureAPI.getConversationHistory(sessionId, {
        include_full_content: true,
        limit: 50
      });
      console.log("Fetched conversation history data:", JSON.stringify(historyData, null, 2));

      setAiAssistant(prev => ({
        ...prev,
        currentSessionId: sessionId,
        conversation: historyData.turns || [],
        isLoading: false,
        showHistory: false,
      }));
    } catch (error) {
      console.error('加载对话历史失败:', error);
      setAiAssistant(prev => ({ ...prev, isLoading: false }));
      alert('加载对话历史失败');
    }
  };

  // 删除会话
  const deleteConversation = async (sessionId: string) => {
    if (!confirm('确认删除此对话会话？')) return;

    try {
      await LiteratureAPI.deleteConversation(sessionId);
      
      // 重新加载会话列表
      if (aiAssistant.selectedLiterature) {
        const sessionsData = await LiteratureAPI.getAISessions({
          literature_id: aiAssistant.selectedLiterature.id,
          limit: 10
        });
        setAiAssistant(prev => ({
          ...prev,
          sessions: sessionsData.sessions || [],
          // 如果删除的是当前会话，清空对话
          currentSessionId: prev.currentSessionId === sessionId ? null : prev.currentSessionId,
          conversation: prev.currentSessionId === sessionId ? [] : prev.conversation,
        }));
      }
    } catch (error) {
      console.error('删除会话失败:', error);
      alert('删除会话失败');
    }
  };

  // 提交反馈
  const submitFeedback = async (turnId: string, rating: number, feedback?: string) => {
    try {
      await LiteratureAPI.submitFeedback({
        turn_id: turnId,
        rating,
        feedback,
      });

      // 更新本地对话中的评分
      setAiAssistant(prev => ({
        ...prev,
        conversation: prev.conversation.map(turn =>
          turn.turn_id === turnId ? { ...turn, user_rating: rating } : turn
        ),
      }));
    } catch (error) {
      console.error('提交反馈失败:', error);
      alert('提交反馈失败');
    }
  };

  // 格式化时间
  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // === 全局AI助手相关函数 ===

  // 处理全局AI问题
  const handleGlobalAIQuestion = async () => {
    if (!aiQuestion.trim()) return;

    setIsAIThinking(true);
    
    try {
      // 获取当前选中的文献列表
      let currentLiterature: Document[] = [];
      if (selectedLibrary.type === 'private') {
        currentLiterature = filteredLibraryTree.private;
      } else {
        const group = filteredLibraryTree.groups.find(g => g.groupId === selectedLibrary.groupId);
        currentLiterature = group ? group.documents : [];
      }

      if (currentLiterature.length === 0) {
        alert('当前没有可分析的文献，请先上传文献');
        setIsAIThinking(false);
        return;
      }

      // 调用多文献分析API
      const response = await LiteratureAPI.askMultipleLiterature({
        question: aiQuestion.trim(),
        literature_ids: currentLiterature.map(doc => doc.id),
        analysis_type: 'comprehensive', // 综合分析
        max_sources: 10,
      });

      // 在全局助手区域显示结果（简化版）
      alert(`AI助手回答：\n\n${response.answer}\n\n置信度: ${(response.confidence && typeof response.confidence === 'number' ? (response.confidence * 100).toFixed(1) : '未知')}%\n处理时间: ${(response.processing_time && typeof response.processing_time === 'number' ? response.processing_time.toFixed(1) : '未知')}秒`);
      
      setAiQuestion("");

    } catch (error) {
      console.error('全局AI问答失败:', error);
      
      // 如果API不存在，提供模拟回答
      const simulatedResponse = generateSimulatedResponse(aiQuestion.trim());
      alert(`AI助手回答（模拟）：\n\n${simulatedResponse}`);
      setAiQuestion("");
    } finally {
      setIsAIThinking(false);
    }
  };

  // 生成模拟回答（当后端API不可用时）
  const generateSimulatedResponse = (question: string): string => {
    const currentLiterature = selectedLibrary.type === 'private' 
      ? filteredLibraryTree.private 
      : (filteredLibraryTree.groups.find(g => g.groupId === selectedLibrary.groupId)?.documents || []);

    if (currentLiterature.length === 0) {
      return "当前文献库为空，建议您先上传一些文献再进行分析。";
    }

    const literatureCount = currentLiterature.length;
    const fileTypes = [...new Set(currentLiterature.map(doc => doc.file_type))];
    
    if (question.includes('总结') || question.includes('主题')) {
      return `基于当前${literatureCount}篇文献的分析：

📚 文献概况：
- 文献数量：${literatureCount}篇
- 文件类型：${fileTypes.join(', ')}
- 最新文献：${currentLiterature[0]?.title || '暂无'}

🔍 主要发现：
1. 您的文献库涵盖了多个研究领域
2. 建议按主题对文献进行分类整理
3. 可以考虑寻找研究间的关联性

💡 研究建议：
- 建议进一步分析文献间的引用关系
- 可以考虑进行系统性文献综述
- 关注研究方法的演进趋势

注：这是基于文献元数据的初步分析，完整分析需要AI服务支持。`;
    }

    if (question.includes('比较') || question.includes('差异')) {
      return `文献比较分析（基于${literatureCount}篇文献）：

📊 基础对比：
- 文献时间跨度：${formatDate(currentLiterature[currentLiterature.length-1]?.upload_time || '')} - ${formatDate(currentLiterature[0]?.upload_time || '')}
- 文件格式分布：${fileTypes.map(type => `${type}格式`).join('、')}

🔬 建议分析维度：
1. 研究方法对比
2. 实验设计差异
3. 结论一致性分析
4. 创新点识别

⚠️ 注意：详细的内容比较需要开启AI文本分析服务。`;
    }

    if (question.includes('方法') || question.includes('技术')) {
      return `研究方法总结（基于${literatureCount}篇文献）：

🛠️ 常见研究方法识别：
- 建议进行全文本挖掘以识别具体方法
- 可以按文献类型分析方法偏好
- 关注方法论的发展趋势

📈 技术演进分析：
- 时间序列分析
- 跨领域技术迁移
- 新兴技术识别

🎯 应用建议：
- 选择最适合您研究问题的方法
- 考虑方法组合的可能性
- 关注方法的局限性`;
    }

    return `感谢您的提问！基于当前${literatureCount}篇文献，我建议：

1. 📖 深入阅读核心文献
2. 🔍 识别研究空白和机会
3. 🎯 明确研究目标和方法
4. 📊 建立系统的分析框架

如需更详细的分析，请确保AI服务正常运行，或者尝试使用单篇文献的AI助手功能。`;
  };

  // 初始化文献库
  const togglePrivateLibrary = () => {
    setPrivateLibraryExpanded(!privateLibraryExpanded);
  };

  const togglePublicLibrary = () => {
    setPublicLibraryExpanded(!publicLibraryExpanded);
  };

  // 加入课题组
  const handleJoinGroup = async (newGroup: GroupLibrary) => {
    setLibraryTree(prev => ({
      ...prev,
      groups: [...prev.groups, newGroup]
    }));
  };

  // 退出课题组
  const handleLeaveGroup = (groupId: string) => {
    setLibraryTree(prev => ({
      ...prev,
      groups: prev.groups.filter(g => g.groupId !== groupId)
    }));
    // 如果当前选中的是被移除的组，切回私人库
    if (selectedLibrary.type === 'group' && selectedLibrary.groupId === groupId) {
      setSelectedLibrary({ type: 'private' });
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-white">
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
          {/* 用户名按钮，点击跳转到个人主页 */}
          <Button
            variant="ghost"
            className="mr-2"
            onClick={() => router.push('/home')}
            title="点击进入个人主页"
          >
            {userName}
          </Button>
          {/* 显示登录状态和退出按钮 */}
          {isAuthenticated && (
            <Button variant="outline" size="sm" onClick={logout}>
              退出登录
            </Button>
          )}
        </div>
      </header>

      <div className="flex flex-1">
        {/* 左侧导航栏 */}
       <aside className="w-64 border-r border-gray-200 bg-gray-50">
          <nav className="p-4 space-y-2">
            {/* 私人文献库 */}
            <Collapsible defaultOpen>
              <CollapsibleTrigger asChild>
                <button
                  className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded hover:bg-gray-200 transition-all
                    [&[data-state=open]>.chevron]:rotate-90
                    ${selectedLibrary.type === 'private' ? 'bg-gray-200 text-black' : 'text-gray-700'}`}
                  onClick={() => setSelectedLibrary({ type: 'private' })}
                >
                  <ChevronRight className="chevron mr-2 transition-transform" />
                  <Folder className="w-4 h-4 mr-2" />
                  个人文献库
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="pl-6 mt-1 space-y-1">
                  {libraryTree.private.length === 0 ? (
                    <span className="text-xs text-gray-400">暂无文献</span>
                  ) : (
                    libraryTree.private.map(doc => (
                      <div key={doc.id} className="flex items-center px-2 py-1 rounded hover:bg-gray-100 text-sm text-gray-700 cursor-pointer">
                        <File className="w-3 h-3 mr-2 text-gray-400" />
                        {doc.title}
                      </div>
                    ))
                  )}
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* 动态课题组文献库 */}
            {libraryTree.groups.map(group => (
              <Collapsible key={group.groupId}>
                <CollapsibleTrigger asChild>
                  <button
                    className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded hover:bg-gray-200 transition-all
                      [&[data-state=open]>.chevron]:rotate-90
                      ${selectedLibrary.type === 'group' && selectedLibrary.groupId === group.groupId ? 'bg-gray-200 text-black' : 'text-gray-700'}`}
                    onClick={() => setSelectedLibrary({ type: 'group', groupId: group.groupId })}
                  >
                    <ChevronRight className="chevron mr-2 transition-transform" />
                    <Folder className="w-4 h-4 mr-2" />
                    {group.groupName}
                  </button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <div className="pl-6 mt-1 space-y-1">
                    {group.documents.length === 0 ? (
                      <span className="text-xs text-gray-400">暂无文献</span>
                    ) : (
                      group.documents.map(doc => (
                        <div key={doc.id} className="flex items-center px-2 py-1 rounded hover:bg-gray-100 text-sm text-gray-700 cursor-pointer">
                          <File className="w-3 h-3 mr-2 text-gray-400" />
                          {doc.title}
                        </div>
                      ))
                    )}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </nav>
        </aside>

        {/* 主内容区 */}
        <main className="flex-1 p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-800">
              {selectedLibrary.type === 'private'
                ? '我的文献'
                : libraryTree.groups.find(g => g.groupId === selectedLibrary.groupId)?.groupName || '课题组文献'}
            </h2>
            <Button 
              onClick={handleUpload} 
              className="!rounded-button whitespace-nowrap bg-black hover:bg-gray-800 text-white"
            >
              <RxShare2 className="w-4 h-4 mr-0" />
              上传文献
            </Button>
          </div>

          {/* 主内容区根据选中库动态渲染 */}
          {selectedLibrary.type === 'private' ? (
            filteredLibraryTree.private.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[500px]">
                <div className="w-24 h-24 mb-4 bg-[#FFF5F0] rounded-lg flex items-center justify-center">
                  <AiOutlineFolderOpen className="text-6xl text-gray-300" />
                </div>
                <p className="mb-2 text-lg font-medium text-gray-700">
                  {searchQuery ? '没有找到匹配的文献' : '当前文献库还是空的'}
                </p>
                <p className="mb-6 text-sm text-gray-500">
                  {searchQuery ? '尝试调整搜索关键词' : '上传第一篇文献，开始研究之旅'}
                </p>
                {!searchQuery && (
                  <Button 
                    onClick={handleUpload} 
                    className="!rounded-button whitespace-nowrap bg-black hover:bg-gray-800 text-white"
                  >
                    上传文献
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {filteredLibraryTree.private.map(doc => (
                  <div 
                    key={doc.id}
                    className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-medium text-gray-800 flex-1">{doc.title}</h3>
                      <div className="flex space-x-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewLiterature(doc.id, doc.filename)}
                          className="text-blue-600 hover:text-blue-800"
                          title="查看文献"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadLiterature(doc.id, doc.filename)}
                          className="text-green-600 hover:text-green-800"
                          title="下载文献"
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openAIAssistant(doc)}
                          className="text-purple-600 hover:text-purple-800"
                          title="AI研究助手"
                        >
                          <MessageCircle className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteLiterature(doc)}
                          className="text-red-600 hover:text-red-800"
                          title="删除文献"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center mb-3 space-x-4">
                      <span className="text-sm text-gray-600">文件名：{doc.filename}</span>
                      <span className="text-sm text-gray-600">大小：{formatFileSize(doc.file_size)}</span>
                      <span className="text-sm text-gray-600">类型：{doc.file_type.toUpperCase()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-x-2">
                        <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-200">私人文献</Badge>
                        <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-200">{doc.file_type.toUpperCase()}</Badge>
                      </div>
                      <span className="text-sm text-gray-500">{formatDate(doc.upload_time)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (() => {
            const group = filteredLibraryTree.groups.find(g => g.groupId === selectedLibrary.groupId);
            if (!group || group.documents.length === 0) {
              return (
                <div className="flex flex-col items-center justify-center h-[500px]">
                  <div className="w-24 h-24 mb-4 bg-[#FFF5F0] rounded-lg flex items-center justify-center">
                    <AiOutlineFolderOpen className="text-6xl text-gray-300" />
                  </div>
                  <p className="mb-2 text-lg font-medium text-gray-700">
                    {searchQuery ? '没有找到匹配的文献' : '当前文献库还是空的'}
                  </p>
                  <p className="mb-6 text-sm text-gray-500">
                    {searchQuery ? '尝试调整搜索关键词' : '上传第一篇文献，开始研究之旅'}
                  </p>
                  {!searchQuery && (
                    <Button 
                      onClick={handleUpload} 
                      className="!rounded-button whitespace-nowrap bg-black hover:bg-gray-800 text-white"
                    >
                      上传文献
                    </Button>
                  )}
                </div>
              );
            }
            return (
              <div className="space-y-4">
                {group.documents.map(doc => (
                  <div 
                    key={doc.id}
                    className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-medium text-gray-800 flex-1">{doc.title}</h3>
                      <div className="flex space-x-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewLiterature(doc.id, doc.filename)}
                          className="text-blue-600 hover:text-blue-800"
                          title="查看文献"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadLiterature(doc.id, doc.filename)}
                          className="text-green-600 hover:text-green-800"
                          title="下载文献"
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openAIAssistant(doc)}
                          className="text-purple-600 hover:text-purple-800"
                          title="AI研究助手"
                        >
                          <MessageCircle className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteLiterature(doc)}
                          className="text-red-600 hover:text-red-800"
                          title="删除文献"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center mb-3 space-x-4">
                      <span className="text-sm text-gray-600">文件名：{doc.filename}</span>
                      <span className="text-sm text-gray-600">大小：{formatFileSize(doc.file_size)}</span>
                      <span className="text-sm text-gray-600">上传者：{doc.uploader_name}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="space-x-2">
                        <Badge className="bg-green-100 text-green-700 hover:bg-green-200">{group.groupName}</Badge>
                        <Badge className="bg-gray-100 text-gray-700 hover:bg-gray-200">{doc.file_type.toUpperCase()}</Badge>
                      </div>
                      <span className="text-sm text-gray-500">{formatDate(doc.upload_time)}</span>
                    </div>
                  </div>
                ))}
              </div>
            );
          })()}

          {/* 页面底部全局AI助手 */}
          {/* 暂时隐藏全局AI研究助手 */}
          {false && (
          <Resizable
            defaultSize={{
              width: '100%',
              height: 320,
            }}
            minHeight={200}
            maxHeight={600}
            enable={{
              top: false, right: false, bottom: true, left: false,
              topRight: false, bottomRight: false, bottomLeft: false, topLeft: false
            }}
            className="w-full border-t border-gray-200 bg-white shadow-lg mt-8"
          >
            <div className="p-4 max-w-7xl mx-auto h-full flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center mr-3">
                    <MessageCircle className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-800">全局AI研究助手</h3>
                    <p className="text-xs text-gray-500">支持多文献比较、跨文献分析等高级功能</p>
                  </div>
                </div>
                
                {/* 当前选中文献显示 */}
                <div className="flex items-center space-x-2">
                  {selectedLibrary.type === 'private' ? (
                    <Badge variant="outline" className="text-xs">
                      已选择 {filteredLibraryTree.private.length} 篇私人文献
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">
                      已选择课题组：{libraryTree.groups.find(g => g.groupId === selectedLibrary.groupId)?.groupName || '未知'}
                    </Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      // 清理缓存的功能
                      LiteratureAPI.clearCache('all').then(() => {
                        alert('AI缓存已清理');
                      }).catch(() => {
                        alert('清理缓存失败');
                      });
                    }}
                    className="text-gray-500 hover:text-gray-700"
                    title="清理AI缓存"
                  >
                    <Star className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg flex-1 overflow-auto">
                <div className="flex items-start">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center mr-2 flex-shrink-0">
                    <MessageCircle className="w-3 h-3 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-700 mb-2">
                      🤖 您好！我是您的全局AI研究助手，可以帮助您：
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                      <div className="flex items-center">
                        <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                        比较多篇文献的异同点
                      </div>
                      <div className="flex items-center">
                        <span className="w-2 h-2 bg-purple-400 rounded-full mr-2"></span>
                        总结当前文献库的研究趋势
                      </div>
                      <div className="flex items-center">
                        <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                        查找相关研究方法和技术
                      </div>
                      <div className="flex items-center">
                        <span className="w-2 h-2 bg-orange-400 rounded-full mr-2"></span>
                        生成研究建议和方向
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex space-x-2">
                <Input
                  type="text"
                  placeholder="例如：比较当前文献库中关于机器学习的方法有哪些差异？"
                  className="flex-1 border-gray-300 focus:ring-purple-400 text-sm"
                  value={aiQuestion}
                  onChange={(e) => setAiQuestion(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleGlobalAIQuestion();
                    }
                  }}
                  disabled={isAIThinking}
                />
                <Button 
                  className="!rounded-button whitespace-nowrap bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-6"
                  onClick={handleGlobalAIQuestion}
                  disabled={!aiQuestion.trim() || isAIThinking}
                >
                  {isAIThinking ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      思考中...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      发送
                    </>
                  )}
                </Button>
              </div>

              {/* 预设的全局问题按钮 */}
              <div className="flex flex-wrap gap-2 mt-3">
                {[
                  "总结当前文献库的主要研究主题",
                  "比较这些文献使用的研究方法",
                  "找出文献间的关联性和差异",
                  "生成基于这些文献的研究建议"
                ].map((question, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setAiQuestion(question);
                      if (aiInputRef.current) {
                        aiInputRef.current.focus();
                      }
                    }}
                    className="text-xs border-purple-200 text-purple-700 hover:bg-purple-50"
                    disabled={isAIThinking}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          </Resizable>
          )}
        </main>
      </div>

      {/* 上传文献对话框 */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>上传文献到{selectedLibrary.type === 'private' ? '个人库' : '课题组'}</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* 标题输入 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">文献标题（可选）</label>
              <Input
                type="text"
                placeholder="自定义文献标题，留空则使用文件名"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                disabled={isUploading}
                className="w-full"
              />
            </div>

            {/* 文件上传区域 */}
            <div 
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive 
                  ? 'border-blue-400 bg-blue-50' 
                  : selectedFile 
                    ? 'border-green-400 bg-green-50' 
                    : 'border-gray-300 bg-gray-50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {selectedFile ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-center">
                    <File className="w-8 h-8 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">{selectedFile.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                    disabled={isUploading}
                    className="text-red-600 hover:text-red-800"
                  >
                    <X className="w-4 h-4 mr-1" />
                    移除文件
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="mx-auto w-12 h-12 text-gray-400">
                    <Upload className="w-12 h-12" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">拖拽文件到此处或点击选择</p>
                    <p className="text-xs text-gray-500 mt-1">支持 PDF、Word 格式，最大 50MB</p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={isUploading}
                  />
                  <Button 
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading}
                    className="!rounded-button whitespace-nowrap bg-black hover:bg-gray-800 text-white text-sm"
                  >
                  选择文件
                </Button>
              </div>
              )}
            </div>
            
            {/* 上传进度 */}
            {isUploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">上传进度</span>
                  <span className="text-gray-600">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
          
          <DialogFooter className="sm:justify-end">
            <Button
              variant="outline"
              onClick={handleCloseDialog}
              disabled={isUploading}
              className="!rounded-button whitespace-nowrap"
            >
              取消
            </Button>
            <Button
              onClick={handleConfirmUpload}
              disabled={!selectedFile || isUploading}
              className="!rounded-button whitespace-nowrap bg-black hover:bg-gray-800 text-white"
            >
              {isUploading ? '上传中...' : '确认上传'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除文献确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-red-600">确认删除文献</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm text-red-800">
                <strong>警告：</strong>此操作将删除以下文献，删除后可以恢复。
              </p>
              {literatureToDelete && (
                <div className="mt-2 text-sm text-gray-700">
                  <p><strong>标题：</strong>{literatureToDelete.title}</p>
                  <p><strong>文件名：</strong>{literatureToDelete.filename}</p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                删除原因（可选）
              </label>
              <Input
                type="text"
                placeholder="请简要说明删除原因..."
                value={deleteReason}
                onChange={(e) => setDeleteReason(e.target.value)}
                disabled={isDeleting}
                className="w-full"
              />
            </div>
          </div>
          
          <DialogFooter className="sm:justify-end">
            <Button
              variant="outline"
              onClick={cancelDelete}
              disabled={isDeleting}
              className="!rounded-button whitespace-nowrap"
            >
              取消
            </Button>
            <Button
              onClick={confirmDeleteLiterature}
              disabled={isDeleting}
              className="!rounded-button whitespace-nowrap bg-red-600 hover:bg-red-700 text-white"
            >
              {isDeleting ? '删除中...' : '确认删除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI研究助手对话框 */}
      <Dialog open={aiAssistant.isOpen} onOpenChange={closeAIAssistant}>
        <DialogContent className="sm:max-w-4xl h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <MessageCircle className="w-5 h-5 text-purple-600" />
              <span>AI研究助手</span>
              {aiAssistant.selectedLiterature && (
                <Badge variant="outline" className="ml-2">
                  {aiAssistant.selectedLiterature.title}
                </Badge>
              )}
            </DialogTitle>
          </DialogHeader>
          
          <div className="flex-1 flex overflow-hidden">
            {/* 左侧：对话历史列表 */}
            <div className="w-1/4 border-r border-gray-200 flex flex-col">
              <div className="p-3 border-b border-gray-200">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium text-sm">对话历史</h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setAiAssistant(prev => ({ ...prev, showHistory: !prev.showHistory }))}
                  >
                    {aiAssistant.showHistory ? '隐藏' : '显示'}
                  </Button>
                </div>
                
                {aiAssistant.showHistory && (
                  <ScrollArea className="h-32">
                    <div className="space-y-1">
                      {aiAssistant.sessions.map(session => (
                        <div
                          key={session.session_id}
                          className={`p-2 rounded cursor-pointer hover:bg-gray-100 text-xs ${
                            session.session_id === aiAssistant.currentSessionId ? 'bg-purple-50 border border-purple-200' : ''
                          }`}
                          onClick={() => loadConversationHistory(session.session_id)}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1 min-w-0">
                              <p className="truncate font-medium">{session.preview}</p>
                              <p className="text-gray-500">{formatTime(session.last_activity)}</p>
                              <p className="text-gray-400">{session.turn_count} 轮对话</p>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteConversation(session.session_id);
                              }}
                              className="text-red-500 hover:text-red-700 p-1"
                            >
                              <X className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </div>

              {/* 预设问题 */}
              <div className="p-3">
                <h4 className="font-medium text-sm mb-2 flex items-center">
                  <Lightbulb className="w-4 h-4 mr-1 text-yellow-500" />
                  推荐问题
                </h4>
                <ScrollArea className="flex-1">
                  <div className="space-y-2">
                    {aiAssistant.presetQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => usePresetQuestion(question)}
                        className="w-full text-left p-2 text-xs bg-gray-50 hover:bg-gray-100 rounded border text-gray-700 transition-colors"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </div>

            {/* 右侧：对话区域 */}
            <div className="flex-1 flex flex-col">
              {/* 对话内容 */}
              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full">
                  <div className="p-4 space-y-4 min-h-full">
                    {aiAssistant.isLoading ? (
                      <div className="flex items-center justify-center h-full min-h-[300px]">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-2"></div>
                          <p className="text-gray-600">加载中...</p>
                        </div>
                      </div>
                    ) : aiAssistant.conversation.length === 0 ? (
                      <div className="flex items-center justify-center h-full min-h-[300px]">
                        <div className="text-center">
                          <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                          <p className="text-gray-600 mb-2">开始与AI助手对话</p>
                          <p className="text-sm text-gray-500">询问关于这篇文献的任何问题</p>
                        </div>
                      </div>
                    ) : (
                      <>
                        {aiAssistant.conversation.map((turn) => (
                          <div key={turn.turn_id} className="space-y-3">
                            {/* 用户问题 */}
                            <div className="flex justify-end">
                              <div className="bg-purple-600 text-white p-3 rounded-lg max-w-[80%] break-words">
                                <p className="text-sm">{turn.question}</p>
                                <p className="text-xs opacity-75 mt-1">{formatTime(turn.timestamp)}</p>
                              </div>
                            </div>

                            {/* AI回答 */}
                            <div className="flex justify-start">
                              <div className="bg-gray-100 p-3 rounded-lg max-w-[80%] break-words">
                                <div className="prose prose-sm max-w-none">
                                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{turn.answer}</p>
                                </div>
                                
                                {/* 关键发现信息框 */}
                                {turn.key_findings && turn.key_findings.length > 0 && (
                                  <div className="mt-3">
                                    <Collapsible>
                                      <CollapsibleTrigger asChild>
                                        <button className="flex items-center justify-between w-full p-2 bg-green-50 rounded border border-green-200 hover:bg-green-100 transition-colors">
                                          <span className="text-xs font-medium text-green-800 flex items-center">
                                            <span className="mr-1">🔍</span>
                                            关键发现 ({turn.key_findings.length}项)
                                          </span>
                                          <span className="text-green-600 text-xs">▼</span>
                                        </button>
                                      </CollapsibleTrigger>
                                      <CollapsibleContent>
                                        <div className="mt-2 p-2 bg-green-50 rounded border-l-4 border-green-300">
                                          <div className="space-y-1">
                                            {turn.key_findings.map((finding, idx) => (
                                              <div key={idx} className="text-xs text-green-800">
                                                <span className="font-medium">{idx + 1}.</span>
                                                <span className="ml-2">{finding}</span>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      </CollapsibleContent>
                                    </Collapsible>
                                  </div>
                                )}
                                
                                {/* 局限性与来源信息框 */}
                                {((turn.limitations && turn.limitations.trim()) || (turn.sources && turn.sources.length > 0)) && (
                                  <div className="mt-3">
                                    <Collapsible>
                                      <CollapsibleTrigger asChild>
                                        <button className="flex items-center justify-between w-full p-2 bg-blue-50 rounded border border-blue-200 hover:bg-blue-100 transition-colors">
                                          <span className="text-xs font-medium text-blue-800 flex items-center">
                                            <span className="mr-1">⚠️</span>
                                            局限性与来源
                                            {turn.sources && turn.sources.length > 0 && (
                                              <span className="ml-1">({turn.sources.length}个来源)</span>
                                            )}
                                          </span>
                                          <span className="text-blue-600 text-xs">▼</span>
                                        </button>
                                      </CollapsibleTrigger>
                                      <CollapsibleContent>
                                        <div className="mt-2 space-y-2">
                                          {/* 局限性说明 */}
                                          {turn.limitations && turn.limitations.trim() && (
                                            <div className="p-2 bg-yellow-50 rounded border-l-4 border-yellow-300">
                                              <h6 className="text-xs font-medium text-yellow-800 mb-1">局限性说明：</h6>
                                              <p className="text-xs text-yellow-700">{turn.limitations}</p>
                                            </div>
                                          )}
                                          
                                          {/* 参考来源 */}
                                          {turn.sources && turn.sources.length > 0 && (
                                            <div className="p-2 bg-blue-50 rounded border-l-4 border-blue-200">
                                              <h6 className="text-xs font-medium text-blue-800 mb-1">参考来源：</h6>
                                              <div className="space-y-1">
                                                {turn.sources.map((source, idx) => (
                                                  <div key={idx} className="text-xs text-blue-700">
                                                    <span className="font-medium">第{source.page}页</span>
                                                    <span className="ml-2">置信度: {(source.confidence && typeof source.confidence === 'number' ? (source.confidence * 100).toFixed(1) : '未知')}%</span>
                                                  </div>
                                                ))}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      </CollapsibleContent>
                                    </Collapsible>
                                  </div>
                                )}
                                
                                {/* 回答质量信息 */}
                                <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-200">
                                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                                    <span>置信度: {(turn.confidence && typeof turn.confidence === 'number' ? (turn.confidence * 100).toFixed(1) : '未知')}%</span>
                                    <span>用时: {(turn.processing_time && typeof turn.processing_time === 'number' ? turn.processing_time.toFixed(1) : '未知')}s</span>
                                  </div>
                                  
                                  {/* 反馈按钮 */}
                                  <div className="flex items-center space-x-1">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => submitFeedback(turn.turn_id, 1)}
                                      className={`p-1 ${turn.user_rating === 1 ? 'text-green-600' : 'text-gray-400 hover:text-green-600'}`}
                                    >
                                      <ThumbsUp className="w-3 h-3" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => submitFeedback(turn.turn_id, -1)}
                                      className={`p-1 ${turn.user_rating === -1 ? 'text-red-600' : 'text-gray-400 hover:text-red-600'}`}
                                    >
                                      <ThumbsDown className="w-3 h-3" />
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        {/* AI思考中指示器 */}
                        {isAIThinking && (
                          <div className="flex justify-start">
                            <div className="bg-gray-100 p-3 rounded-lg">
                              <div className="flex items-center space-x-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                                <span className="text-sm text-gray-600">AI正在思考...</span>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* 添加一个底部标记，用于自动滚动 */}
                        <div id="chat-bottom" />
                      </>
                    )}
                  </div>
                </ScrollArea>
              </div>

              {/* 输入区域 */}
              <div className="border-t border-gray-200 p-4">
                <div className="flex space-x-2">
                  <Input
                    ref={aiInputRef}
                    placeholder="请输入您的问题..."
                    value={aiQuestion}
                    onChange={(e) => setAiQuestion(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendAIQuestion(aiQuestion);
                      }
                    }}
                    disabled={isAIThinking}
                    className="flex-1"
                  />
                  <Button
                    onClick={() => sendAIQuestion(aiQuestion)}
                    disabled={!aiQuestion.trim() || isAIThinking}
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default App;

# RAG问答系统快速开始指南

## 🚀 环境准备

### 1. 安装依赖
```bash
# 安装新的RAG相关依赖
pip install google-genai cachetools structlog

# 或者重新安装所有依赖
pip install -r requirements.txt
```

### 2. 配置验证
确保以下配置正确：

**`.env` 文件检查**:
```bash
# 必需的配置
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
DATABASE_URL=sqlite:///./literature_system.db

# RAG相关配置（可选，有默认值）
VECTOR_DB_PATH=./vector_db
CHROMA_COLLECTION_PREFIX=group_
```

### 3. 系统状态检查
```bash
# 运行综合测试确保系统就绪
python test_ai_basic.py
```

预期输出：所有测试通过，包括：
- ✅ Google API连接
- ✅ Embedding服务
- ✅ 向量数据库
- ✅ 文本处理
- ✅ 文件处理

---

## 📝 实施步骤

### Step 1: 基础组件实现 (开始实施)

#### 1.1 创建配置更新
首先更新配置文件，添加RAG相关配置：

```bash
# 检查app/config.py中是否包含RAG配置
grep -n "RAG_" app/config.py
```

如果没有，需要添加：
```python
# RAG配置
RAG_MAX_CONTEXT_TOKENS = 3000
RAG_TOP_K_RETRIEVAL = 5
RAG_CONVERSATION_MAX_TURNS = 10
RAG_CACHE_TTL = 3600
RAG_AI_TIMEOUT = 30
```

#### 1.2 创建提示词构建器
```bash
# 创建提示词构建器
touch app/utils/prompt_builder.py
```

#### 1.3 创建答案处理器
```bash
# 创建答案处理器
touch app/utils/answer_processor.py
```

#### 1.4 创建RAG核心服务
```bash
# 创建RAG核心服务
touch app/utils/rag_service.py
```

### Step 2: 数据模型创建

#### 2.1 创建对话模型
```bash
# 创建对话相关模型
touch app/models/conversation.py
```

#### 2.2 数据库迁移准备
```bash
# 检查是否需要数据库迁移
ls -la *.db
```

### Step 3: API接口开发

#### 3.1 创建AI聊天路由
```bash
# 创建AI聊天路由
mkdir -p app/routers
touch app/routers/ai_chat.py
```

#### 3.2 创建测试文件
```bash
# 创建测试文件
mkdir -p tests
touch tests/test_rag_service.py
touch tests/test_conversation.py
touch tests/test_ai_chat_api.py
```

---

## 🔍 开发验证点

### 验证点1: 基础组件创建完成
**检查命令**:
```bash
# 检查所有必需文件是否存在
ls -la app/utils/prompt_builder.py
ls -la app/utils/answer_processor.py  
ls -la app/utils/rag_service.py
ls -la app/models/conversation.py
ls -la app/routers/ai_chat.py
```

**预期结果**: 所有文件存在

### 验证点2: 基础功能实现
**检查命令**:
```bash
# 测试RAG核心功能
python -c "from app.utils.rag_service import RAGService; print('RAG服务导入成功')"
```

**预期结果**: 无导入错误

### 验证点3: API接口可用
**检查命令**:
```bash
# 启动服务器
python run.py &

# 测试API可用性
curl -X GET "http://localhost:8001/docs"
```

**预期结果**: API文档页面可访问

### 验证点4: 端到端测试
**检查命令**:
```bash
# 运行完整的RAG测试
python tests/test_ai_chat_api.py
```

**预期结果**: 所有测试通过

---

## 🛠️ 开发工具和技巧

### 1. 实时日志监控
```bash
# 监控系统日志
tail -f literature_system.log | grep -E "(RAG|qa_|conversation)"
```

### 2. 性能分析
```bash
# 简单的性能测试
time python -c "
from app.utils.rag_service import RAGService
from app.utils.embedding_service import embedding_service
import time

start = time.time()
embedding = embedding_service.generate_query_embedding('测试问题')
print(f'Embedding生成时间: {time.time() - start:.2f}秒')
"
```

### 3. 缓存状态查看
```python
# 在Python REPL中查看缓存状态
from app.utils.cache_manager import cache_manager
print(cache_manager.get_cache_stats())
```

### 4. 数据库状态检查
```bash
# 检查向量数据库状态
python -c "
from app.utils.vector_store import vector_store
print(vector_store.health_check())
"
```

---

## 🔧 常见问题排除

### 问题1: Google API连接失败
**症状**: `User location is not supported for the API use`
**解决方案**: 
1. 检查API密钥是否正确
2. 确认网络连接（可能需要VPN）
3. 验证API配额是否充足

### 问题2: ChromaDB初始化失败
**症状**: `ImportError: cannot import name 'chromadb'`
**解决方案**:
```bash
pip uninstall chromadb
pip install chromadb==0.4.15
```

### 问题3: 向量维度不匹配
**症状**: `Embedding dimension mismatch`
**解决方案**:
1. 清理向量数据库：`rm -rf vector_db/*`
2. 重新生成向量数据

### 问题4: 内存使用过高
**症状**: 系统响应变慢
**解决方案**:
1. 减少缓存大小
2. 增加垃圾回收频率
3. 重启服务释放内存

### 问题5: RAG答案质量差
**症状**: 答案不相关或不准确
**解决方案**:
1. 调整检索参数（top_k值）
2. 优化提示词模板
3. 检查文档分块质量

---

## 📊 性能基准

### 预期性能指标
| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| 问答响应时间 | <5秒 | API调用计时 |
| Embedding生成 | <2秒 | 单独测试 |
| 向量检索 | <1秒 | 检索操作计时 |
| 缓存命中率 | >60% | 缓存统计 |
| 并发用户 | ≥20 | 压力测试 |

### 性能测试脚本
```python
# 创建简单的性能测试
import time
import asyncio
from app.utils.rag_service import RAGService

async def performance_test():
    rag_service = RAGService()
    
    # 测试问题列表
    questions = [
        "这篇文献的主要论点是什么？",
        "文献中使用了哪些研究方法？",
        "有什么创新点？",
        "存在哪些局限性？",
        "结论是什么？"
    ]
    
    # 测试性能
    total_time = 0
    for question in questions:
        start_time = time.time()
        
        # 模拟RAG处理（需要实际实现后测试）
        # result = await rag_service.process_question(question, "test_lit_id", "test_group_id")
        
        end_time = time.time()
        response_time = end_time - start_time
        total_time += response_time
        
        print(f"问题: {question[:20]}... 响应时间: {response_time:.2f}秒")
    
    avg_time = total_time / len(questions)
    print(f"\n平均响应时间: {avg_time:.2f}秒")

# 运行测试
# asyncio.run(performance_test())
```

---

## 📋 实施检查清单

### 开发准备 ✅
- [ ] 依赖安装完成
- [ ] 环境配置正确
- [ ] 基础功能测试通过
- [ ] 开发工具准备就绪

### 核心组件实现 🚧
- [ ] 提示词构建器
- [ ] 答案处理器
- [ ] RAG核心服务
- [ ] 对话管理器
- [ ] 缓存管理器

### API接口开发 ⏸️
- [ ] AI聊天路由
- [ ] 数据模型定义
- [ ] 权限验证
- [ ] 错误处理

### 测试验证 ⏸️
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 用户体验测试

### 优化完善 ⏸️
- [ ] 性能调优
- [ ] 错误处理优化
- [ ] 用户体验改进
- [ ] 文档完善

---

## 🎯 下一步行动

1. **立即开始**: 按照Step 1创建基础组件文件
2. **重点关注**: RAG核心服务的实现质量
3. **持续测试**: 每完成一个组件就进行测试验证
4. **性能监控**: 关注响应时间和资源使用
5. **用户体验**: 确保API接口友好易用

开始实施时，建议先完成一个最小可用版本（MVP），然后逐步优化和扩展功能。 
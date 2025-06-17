# 缓存管理器详细实现规划

## 🏗️ 架构设计

### 1. 核心类设计

```python
# app/utils/cache_manager.py

from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from cachetools import TTLCache, LRUCache
import threading
from dataclasses import dataclass

@dataclass
class CacheItem:
    """缓存项数据结构"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    ttl: Optional[int] = None
    tags: List[str] = None

class CacheStats:
    """缓存统计类"""
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.start_time = datetime.now()
    
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class BaseCacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        pass
    
    @abstractmethod
    def size(self) -> int:
        pass

class MemoryCacheBackend(BaseCacheBackend):
    """内存缓存后端"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self.lock:
            self.cache[key] = value
            return True
    
    def delete(self, key: str) -> bool:
        with self.lock:
            return self.cache.pop(key, None) is not None
    
    def clear(self) -> bool:
        with self.lock:
            self.cache.clear()
            return True
    
    def size(self) -> int:
        with self.lock:
            return len(self.cache)

class CacheManager:
    """缓存管理器主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stats = CacheStats()
        
        # 初始化不同类型的缓存
        self.embedding_cache = MemoryCacheBackend(
            maxsize=Config.RAG_CACHE_EMBEDDING_MAX_SIZE,
            ttl=Config.RAG_CACHE_TTL
        )
        
        self.answer_cache = MemoryCacheBackend(
            maxsize=Config.RAG_CACHE_ANSWER_MAX_SIZE,
            ttl=Config.RAG_CACHE_TTL // 2
        )
        
        self.chunk_cache = MemoryCacheBackend(
            maxsize=Config.RAG_CACHE_CHUNK_MAX_SIZE,
            ttl=Config.RAG_CACHE_TTL * 2
        )
        
        self.logger.info("缓存管理器初始化完成")
```

### 2. 缓存键生成策略

```python
class CacheKeyGenerator:
    """缓存键生成器"""
    
    @staticmethod
    def embedding_key(text: str, model: str = "default") -> str:
        """生成embedding缓存键"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
        return f"emb:{model}:{text_hash}"
    
    @staticmethod
    def answer_key(question: str, literature_id: str, context_hash: str) -> str:
        """生成答案缓存键"""
        question_hash = hashlib.md5(question.encode('utf-8')).hexdigest()[:8]
        return f"ans:{literature_id}:{question_hash}:{context_hash[:8]}"
    
    @staticmethod
    def chunk_key(literature_id: str, chunk_index: int) -> str:
        """生成文档块缓存键"""
        return f"chunk:{literature_id}:{chunk_index}"
    
    @staticmethod
    def context_hash(chunks: List[Dict]) -> str:
        """生成上下文哈希"""
        context_str = json.dumps([c.get('text', '')[:100] for c in chunks], sort_keys=True)
        return hashlib.md5(context_str.encode('utf-8')).hexdigest()[:16]
```

## 📅 分阶段实施计划

### Phase 1: 基础内存缓存 (3-4天)

#### Day 1: 核心架构实现
**任务清单:**
- [ ] 创建 `app/utils/cache_manager.py` 文件
- [ ] 实现 `BaseCacheBackend` 抽象类
- [ ] 实现 `MemoryCacheBackend` 内存缓存
- [ ] 实现 `CacheKeyGenerator` 键生成器
- [ ] 实现 `CacheStats` 统计类

**关键代码:**
```python
# 基础缓存管理器实现
class CacheManager:
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """获取embedding（带缓存）"""
        key = CacheKeyGenerator.embedding_key(text)
        cached = self.embedding_cache.get(key)
        
        if cached is not None:
            self.stats.hits += 1
            self.logger.debug(f"Embedding缓存命中: {key}")
            return cached
        
        self.stats.misses += 1
        return None
    
    def set_embedding(self, text: str, embedding: List[float]) -> bool:
        """设置embedding缓存"""
        key = CacheKeyGenerator.embedding_key(text)
        success = self.embedding_cache.set(key, embedding)
        
        if success:
            self.stats.sets += 1
            self.logger.debug(f"Embedding已缓存: {key}")
        
        return success
```

#### Day 2: 集成到现有服务
**任务清单:**
- [ ] 修改 `embedding_service.py` 集成缓存
- [ ] 修改 `rag_service.py` 集成答案缓存
- [ ] 修改 `vector_store.py` 集成文档块缓存
- [ ] 添加缓存配置参数

**集成示例:**
```python
# app/utils/embedding_service.py 修改
class EmbeddingService:
    def __init__(self):
        # ... 现有初始化代码
        self.cache_manager = cache_manager
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        # 1. 先检查缓存
        cached_embedding = self.cache_manager.get_embedding(text)
        if cached_embedding is not None:
            return cached_embedding
        
        # 2. 缓存未命中，生成新的embedding
        embedding = self._generate_google_embedding(text)
        
        # 3. 存入缓存
        if embedding:
            self.cache_manager.set_embedding(text, embedding)
        
        return embedding
```

#### Day 3: 答案缓存实现
**任务清单:**
- [ ] 实现答案缓存逻辑
- [ ] 处理上下文相关的缓存策略
- [ ] 实现缓存失效机制

**关键代码:**
```python
class CacheManager:
    def get_answer(self, question: str, literature_id: str, 
                   context_chunks: List[Dict]) -> Optional[Dict]:
        """获取答案缓存"""
        context_hash = CacheKeyGenerator.context_hash(context_chunks)
        key = CacheKeyGenerator.answer_key(question, literature_id, context_hash)
        
        cached = self.answer_cache.get(key)
        if cached is not None:
            self.stats.hits += 1
            # 更新时间戳
            cached['metadata']['cache_hit'] = True
            cached['metadata']['retrieved_at'] = datetime.now().isoformat()
            return cached
        
        self.stats.misses += 1
        return None
    
    def set_answer(self, question: str, literature_id: str, 
                   context_chunks: List[Dict], answer_data: Dict) -> bool:
        """设置答案缓存"""
        context_hash = CacheKeyGenerator.context_hash(context_chunks)
        key = CacheKeyGenerator.answer_key(question, literature_id, context_hash)
        
        # 添加缓存元数据
        cached_answer = answer_data.copy()
        cached_answer['metadata']['cached_at'] = datetime.now().isoformat()
        cached_answer['metadata']['context_hash'] = context_hash
        
        return self.answer_cache.set(key, cached_answer)
```

#### Day 4: 监控和调试
**任务清单:**
- [ ] 实现缓存统计接口
- [ ] 添加缓存监控日志
- [ ] 创建缓存调试工具
- [ ] 编写单元测试

### Phase 2: 高级缓存功能 (2-3天)

#### Day 5: TTL和淘汰策略
**任务清单:**
- [ ] 实现灵活的TTL设置
- [ ] 实现LRU + TTL混合淘汰
- [ ] 实现基于标签的批量清理
- [ ] 实现缓存预热机制

**高级淘汰策略:**
```python
class SmartEvictionStrategy:
    """智能淘汰策略"""
    
    def should_evict(self, item: CacheItem) -> bool:
        """判断是否应该淘汰缓存项"""
        now = datetime.now()
        
        # 1. TTL检查
        if item.ttl and (now - item.created_at).seconds > item.ttl:
            return True
        
        # 2. 访问频率检查
        item_age = (now - item.created_at).seconds
        if item_age > 3600 and item.access_count < 2:  # 1小时内访问少于2次
            return True
        
        # 3. 最后访问时间检查
        if (now - item.accessed_at).seconds > 1800:  # 30分钟未访问
            return True
        
        return False

class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
    
    async def warm_frequently_used_embeddings(self):
        """预热常用问题的embeddings"""
        common_questions = [
            "这篇文献的主要结论是什么？",
            "文献中的实验方法是什么？",
            "这项研究有什么创新点？"
        ]
        
        for question in common_questions:
            if not self.cache_manager.get_embedding(question):
                # 生成并缓存embedding
                embedding = await embedding_service.generate_embedding(question)
                if embedding:
                    self.cache_manager.set_embedding(question, embedding)
                    self.logger.info(f"预热embedding: {question[:30]}...")
```

#### Day 6-7: 持久化缓存
**任务清单:**
- [ ] 实现SQLite持久化缓存
- [ ] 实现缓存数据的序列化/反序列化
- [ ] 实现多层缓存协调机制
- [ ] 实现缓存数据恢复

### Phase 3: 性能优化 (1-2天)

#### Day 8: 性能调优
**任务清单:**
- [ ] 实现异步缓存操作
- [ ] 优化缓存键生成算法
- [ ] 实现批量缓存操作
- [ ] 内存使用优化

**异步缓存实现:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncCacheManager:
    """异步缓存管理器"""
    
    def __init__(self):
        self.sync_manager = CacheManager()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_embedding_async(self, text: str) -> Optional[List[float]]:
        """异步获取embedding"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.sync_manager.get_embedding, 
            text
        )
    
    async def set_embedding_async(self, text: str, embedding: List[float]) -> bool:
        """异步设置embedding"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.sync_manager.set_embedding,
            text, embedding
        )
```

## 🔧 配置和集成

### 1. 配置参数扩展

```python
# app/config.py 添加
class Config:
    # ... 现有配置
    
    # ===== 缓存配置 =====
    
    # 基础缓存设置
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = int(os.getenv("CACHE_DEFAULT_TTL", "3600"))  # 1小时
    
    # 内存缓存配置
    CACHE_EMBEDDING_SIZE: int = int(os.getenv("CACHE_EMBEDDING_SIZE", "1000"))
    CACHE_EMBEDDING_TTL: int = int(os.getenv("CACHE_EMBEDDING_TTL", "7200"))  # 2小时
    
    CACHE_ANSWER_SIZE: int = int(os.getenv("CACHE_ANSWER_SIZE", "500"))
    CACHE_ANSWER_TTL: int = int(os.getenv("CACHE_ANSWER_TTL", "1800"))  # 30分钟
    
    CACHE_CHUNK_SIZE: int = int(os.getenv("CACHE_CHUNK_SIZE", "2000"))
    CACHE_CHUNK_TTL: int = int(os.getenv("CACHE_CHUNK_TTL", "14400"))  # 4小时
    
    # 缓存行为配置
    CACHE_PRELOAD_ON_STARTUP: bool = os.getenv("CACHE_PRELOAD_ON_STARTUP", "false").lower() == "true"
    CACHE_STATS_ENABLED: bool = os.getenv("CACHE_STATS_ENABLED", "true").lower() == "true"
    CACHE_CLEANUP_INTERVAL: int = int(os.getenv("CACHE_CLEANUP_INTERVAL", "300"))  # 5分钟
    
    # 持久化缓存配置
    CACHE_PERSISTENT_ENABLED: bool = os.getenv("CACHE_PERSISTENT_ENABLED", "false").lower() == "true"
    CACHE_PERSISTENT_PATH: str = os.getenv("CACHE_PERSISTENT_PATH", "./cache_storage")
```

### 2. API接口扩展

```python
# app/routers/cache_admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.utils.cache_manager import cache_manager

router = APIRouter(prefix="/admin/cache", tags=["缓存管理"])

@router.get("/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    return {
        "embedding_cache": {
            "hits": cache_manager.stats.hits,
            "misses": cache_manager.stats.misses,
            "hit_rate": cache_manager.stats.hit_rate(),
            "size": cache_manager.embedding_cache.size()
        },
        "answer_cache": {
            "size": cache_manager.answer_cache.size()
        },
        "chunk_cache": {
            "size": cache_manager.chunk_cache.size()
        }
    }

@router.post("/clear")
async def clear_cache(cache_type: str = "all"):
    """清理缓存"""
    if cache_type == "all":
        cache_manager.clear_all()
    elif cache_type == "embedding":
        cache_manager.embedding_cache.clear()
    elif cache_type == "answer":
        cache_manager.answer_cache.clear()
    elif cache_type == "chunk":
        cache_manager.chunk_cache.clear()
    else:
        raise HTTPException(status_code=400, detail="无效的缓存类型")
    
    return {"message": f"缓存 {cache_type} 已清理"}

@router.post("/warm")
async def warm_cache():
    """预热缓存"""
    await cache_manager.warmer.warm_frequently_used_embeddings()
    return {"message": "缓存预热完成"}
```

## 📊 性能测试计划

### 1. 性能基准测试

```python
# test/test_cache_performance.py
import time
import asyncio
import pytest
from app.utils.cache_manager import cache_manager

class TestCachePerformance:
    
    def test_embedding_cache_performance(self):
        """测试embedding缓存性能"""
        test_texts = [f"测试文本 {i}" for i in range(100)]
        
        # 无缓存性能测试
        start_time = time.time()
        for text in test_texts:
            embedding_service.generate_embedding(text)
        no_cache_time = time.time() - start_time
        
        # 有缓存性能测试
        start_time = time.time()
        for text in test_texts:
            # 第二次调用应该命中缓存
            cache_manager.get_embedding(text)
        cache_time = time.time() - start_time
        
        improvement = (no_cache_time - cache_time) / no_cache_time * 100
        assert improvement > 90  # 至少90%的性能提升
        
    def test_memory_usage(self):
        """测试内存使用情况"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 大量数据写入缓存
        for i in range(1000):
            cache_manager.set_embedding(f"test_{i}", [0.1] * 768)
        
        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024 / 1024  # MB
        
        assert memory_increase < 100  # 内存增长不超过100MB
```

### 2. 负载测试

```python
async def load_test_cache():
    """缓存负载测试"""
    import aiohttp
    
    async def worker(session, worker_id):
        for i in range(100):
            async with session.post("/ai/ask", json={
                "question": f"测试问题 {worker_id}_{i}",
                "literature_id": "test_lit_id"
            }) as response:
                assert response.status == 200
    
    async with aiohttp.ClientSession() as session:
        tasks = [worker(session, i) for i in range(10)]
        await asyncio.gather(*tasks)
```

## 🚀 部署和运维

### 1. 监控和告警

```python
class CacheHealthMonitor:
    """缓存健康监控"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)
    
    def check_health(self) -> Dict[str, Any]:
        """检查缓存健康状况"""
        stats = self.cache_manager.stats
        
        # 检查命中率
        hit_rate = stats.hit_rate()
        hit_rate_status = "healthy" if hit_rate > 0.7 else "warning" if hit_rate > 0.4 else "critical"
        
        # 检查内存使用
        memory_usage = self._get_memory_usage()
        memory_status = "healthy" if memory_usage < 0.8 else "warning" if memory_usage < 0.9 else "critical"
        
        return {
            "overall_status": "healthy" if all(s == "healthy" for s in [hit_rate_status, memory_status]) else "degraded",
            "hit_rate": {
                "value": hit_rate,
                "status": hit_rate_status
            },
            "memory_usage": {
                "value": memory_usage,
                "status": memory_status
            },
            "cache_sizes": {
                "embedding": self.cache_manager.embedding_cache.size(),
                "answer": self.cache_manager.answer_cache.size(),
                "chunk": self.cache_manager.chunk_cache.size()
            }
        }
```

### 2. 自动化运维脚本

```bash
#!/bin/bash
# scripts/cache_maintenance.sh

# 缓存维护脚本
echo "开始缓存维护..."

# 1. 检查缓存健康状况
curl -s http://localhost:8000/admin/cache/stats | jq .

# 2. 清理过期缓存
if [ $(date +%H) -eq 2 ]; then  # 凌晨2点
    echo "执行缓存清理..."
    curl -X POST http://localhost:8000/admin/cache/clear?cache_type=expired
fi

# 3. 预热缓存
if [ $(date +%H) -eq 6 ]; then  # 早上6点
    echo "执行缓存预热..."
    curl -X POST http://localhost:8000/admin/cache/warm
fi

echo "缓存维护完成"
```

## 📈 预期收益评估

### 1. 性能提升预期

| 操作类型 | 无缓存响应时间 | 有缓存响应时间 | 提升幅度 |
|---------|---------------|---------------|----------|
| Embedding生成 | 2-5秒 | 10-50ms | **95-99%** |
| 相同问题回答 | 8-15秒 | 100-500ms | **92-96%** |
| 文档块检索 | 500ms-2s | 10-100ms | **80-95%** |

### 2. 成本节约预期

| 成本项 | 月度节约 | 年度节约 |
|--------|----------|----------|
| AI API调用费用 | 60-80% | $1000-5000 |
| 服务器计算资源 | 30-50% | $500-2000 |
| 用户等待时间成本 | 显著提升 | 用户满意度+++ |

### 3. 运维效益

- **系统响应能力**: 提升3-5倍
- **并发处理能力**: 提升2-3倍  
- **系统稳定性**: 减少API依赖，提升鲁棒性
- **用户体验**: 显著改善，特别是重复查询场景

这个实现规划提供了完整的技术路线图，确保缓存管理器能够有效提升系统性能和用户体验。 
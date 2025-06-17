"""
缓存管理器

实现基于内存的多层缓存系统，支持embedding、答案和文档块缓存
"""
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from cachetools import TTLCache, LRUCache

from app.config import Config

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
        self.lock = threading.Lock()
    
    def hit_rate(self) -> float:
        """计算缓存命中率"""
        with self.lock:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0
    
    def record_hit(self):
        """记录缓存命中"""
        with self.lock:
            self.hits += 1
    
    def record_miss(self):
        """记录缓存未命中"""
        with self.lock:
            self.misses += 1
    
    def record_set(self):
        """记录缓存设置"""
        with self.lock:
            self.sets += 1
    
    def record_delete(self):
        """记录缓存删除"""
        with self.lock:
            self.deletes += 1
    
    def record_eviction(self):
        """记录缓存淘汰"""
        with self.lock:
            self.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            uptime = (datetime.now() - self.start_time).total_seconds()
            # 直接计算命中率，避免嵌套锁调用
            total_ops = self.hits + self.misses
            hit_rate = self.hits / total_ops if total_ops > 0 else 0.0
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "sets": self.sets,
                "deletes": self.deletes,
                "evictions": self.evictions,
                "hit_rate": hit_rate,
                "total_operations": total_ops,
                "uptime_seconds": uptime
            }

class BaseCacheBackend(ABC):
    """缓存后端抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """清空缓存"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """获取缓存大小"""
        pass
    
    @abstractmethod
    def keys(self) -> List[str]:
        """获取所有键"""
        pass

class MemoryCacheBackend(BaseCacheBackend):
    """内存缓存后端"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600, cache_type: str = "generic"):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache_type = cache_type
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"初始化 {cache_type} 内存缓存: maxsize={maxsize}, ttl={ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            try:
                value = self.cache.get(key)
                if value is not None:
                    self.logger.debug(f"{self.cache_type} 缓存命中: {key}")
                return value
            except Exception as e:
                self.logger.error(f"{self.cache_type} 缓存获取失败: {key}, 错误: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        with self.lock:
            try:
                # 如果指定了TTL且与默认不同，需要特殊处理
                if ttl is not None and ttl != self.ttl:
                    # 为了简化实现，这里仍使用默认TTL
                    # 在高级版本中可以实现更复杂的TTL处理
                    pass
                
                self.cache[key] = value
                self.logger.debug(f"{self.cache_type} 缓存设置: {key}")
                return True
            except Exception as e:
                self.logger.error(f"{self.cache_type} 缓存设置失败: {key}, 错误: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self.lock:
            try:
                result = self.cache.pop(key, None) is not None
                if result:
                    self.logger.debug(f"{self.cache_type} 缓存删除: {key}")
                return result
            except Exception as e:
                self.logger.error(f"{self.cache_type} 缓存删除失败: {key}, 错误: {e}")
                return False
    
    def clear(self) -> bool:
        """清空缓存"""
        with self.lock:
            try:
                old_size = len(self.cache)
                self.cache.clear()
                self.logger.info(f"{self.cache_type} 缓存已清空，原大小: {old_size}")
                return True
            except Exception as e:
                self.logger.error(f"{self.cache_type} 缓存清空失败: {e}")
                return False
    
    def size(self) -> int:
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)
    
    def keys(self) -> List[str]:
        """获取所有键"""
        with self.lock:
            return list(self.cache.keys())
    
    def info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        with self.lock:
            return {
                "type": self.cache_type,
                "maxsize": self.maxsize,
                "current_size": len(self.cache),
                "ttl": self.ttl,
                "utilization": len(self.cache) / self.maxsize if self.maxsize > 0 else 0
            }

class CacheKeyGenerator:
    """缓存键生成器"""
    
    @staticmethod
    def embedding_key(text: str, model: str = "default") -> str:
        """生成embedding缓存键"""
        # 使用MD5哈希来确保键的唯一性和长度控制
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
        try:
            # 提取每个chunk的关键信息来生成稳定的哈希
            context_data = []
            for chunk in chunks:
                chunk_data = {
                    'text': chunk.get('text', '')[:100],  # 只取前100字符
                    'source': chunk.get('metadata', {}).get('source', ''),
                    'page': chunk.get('metadata', {}).get('page', 0)
                }
                context_data.append(chunk_data)
            
            context_str = json.dumps(context_data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(context_str.encode('utf-8')).hexdigest()[:16]
        except Exception as e:
            # 如果上下文处理失败，使用简单的哈希
            simple_context = str(len(chunks)) + str(chunks[0].get('text', '')[:50] if chunks else '')
            return hashlib.md5(simple_context.encode('utf-8')).hexdigest()[:16]

class CacheManager:
    """缓存管理器主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stats = CacheStats()
        
        # 获取配置参数，使用环境变量或默认值
        import os
        embedding_max_size = int(os.getenv("RAG_CACHE_EMBEDDING_MAX_SIZE", "1000"))
        answer_max_size = int(os.getenv("RAG_CACHE_ANSWER_MAX_SIZE", "500"))
        chunk_max_size = int(os.getenv("RAG_CACHE_CHUNK_MAX_SIZE", "2000"))
        cache_ttl = int(os.getenv("RAG_CACHE_TTL", "3600"))
        
        # 如果Config可用，优先使用Config的值
        try:
            embedding_max_size = Config.RAG_CACHE_EMBEDDING_MAX_SIZE
            answer_max_size = Config.RAG_CACHE_ANSWER_MAX_SIZE
            chunk_max_size = Config.RAG_CACHE_CHUNK_MAX_SIZE
            cache_ttl = Config.RAG_CACHE_TTL
        except:
            pass  # 使用默认值
        
        # 初始化不同类型的缓存
        self.embedding_cache = MemoryCacheBackend(
            maxsize=embedding_max_size,
            ttl=cache_ttl,
            cache_type="embedding"
        )
        
        self.answer_cache = MemoryCacheBackend(
            maxsize=answer_max_size,
            ttl=cache_ttl // 2,  # 答案缓存时间较短
            cache_type="answer"
        )
        
        self.chunk_cache = MemoryCacheBackend(
            maxsize=chunk_max_size,
            ttl=cache_ttl * 2,  # 文档块缓存时间较长
            cache_type="chunk"
        )
        
        self.logger.info("缓存管理器初始化完成")
    
    # ====== Embedding 缓存方法 ======
    
    def get_embedding(self, text: str, model: str = "default") -> Optional[List[float]]:
        """获取embedding（带缓存）"""
        key = CacheKeyGenerator.embedding_key(text, model)
        cached = self.embedding_cache.get(key)
        
        if cached is not None:
            self.stats.record_hit()
            self.logger.debug(f"Embedding缓存命中: {key}")
            return cached
        
        self.stats.record_miss()
        return None
    
    def set_embedding(self, text: str, embedding: List[float], model: str = "default") -> bool:
        """设置embedding缓存"""
        key = CacheKeyGenerator.embedding_key(text, model)
        success = self.embedding_cache.set(key, embedding)
        
        if success:
            self.stats.record_set()
            self.logger.debug(f"Embedding已缓存: {key}")
        
        return success
    
    # ====== 答案缓存方法 ======
    
    def get_answer(self, question: str, literature_id: str, 
                   context_chunks: List[Dict]) -> Optional[Dict]:
        """获取答案缓存"""
        try:
            context_hash = CacheKeyGenerator.context_hash(context_chunks)
            key = CacheKeyGenerator.answer_key(question, literature_id, context_hash)
            
            cached = self.answer_cache.get(key)
            if cached is not None:
                self.stats.record_hit()
                # 更新缓存元数据
                if isinstance(cached, dict) and 'metadata' in cached:
                    cached['metadata']['cache_hit'] = True
                    cached['metadata']['retrieved_at'] = datetime.now().isoformat()
                return cached
            
            self.stats.record_miss()
            return None
        except Exception as e:
            self.logger.error(f"获取答案缓存失败: {e}")
            self.stats.record_miss()
            return None
    
    def set_answer(self, question: str, literature_id: str, 
                   context_chunks: List[Dict], answer_data: Dict) -> bool:
        """设置答案缓存"""
        try:
            context_hash = CacheKeyGenerator.context_hash(context_chunks)
            key = CacheKeyGenerator.answer_key(question, literature_id, context_hash)
            
            # 添加缓存元数据
            cached_answer = answer_data.copy()
            if 'metadata' not in cached_answer:
                cached_answer['metadata'] = {}
            
            cached_answer['metadata']['cached_at'] = datetime.now().isoformat()
            cached_answer['metadata']['context_hash'] = context_hash
            cached_answer['metadata']['cache_hit'] = False
            
            success = self.answer_cache.set(key, cached_answer)
            if success:
                self.stats.record_set()
            
            return success
        except Exception as e:
            self.logger.error(f"设置答案缓存失败: {e}")
            return False
    
    # ====== 文档块缓存方法 ======
    
    def get_chunks(self, literature_id: str, chunk_indices: List[int]) -> Optional[List[Dict]]:
        """批量获取文档块缓存"""
        try:
            chunks = []
            cache_hits = 0
            
            for index in chunk_indices:
                key = CacheKeyGenerator.chunk_key(literature_id, index)
                cached_chunk = self.chunk_cache.get(key)
                
                if cached_chunk is not None:
                    chunks.append(cached_chunk)
                    cache_hits += 1
                else:
                    # 如果有任何一个块未命中，返回None，让调用方重新获取所有块
                    self.stats.record_miss()
                    return None
            
            if cache_hits > 0:
                self.stats.record_hit()
            
            return chunks if chunks else None
        except Exception as e:
            self.logger.error(f"批量获取文档块缓存失败: {e}")
            return None
    
    def set_chunks(self, literature_id: str, chunks: List[Tuple[int, Dict]]) -> bool:
        """批量设置文档块缓存"""
        try:
            success_count = 0
            
            for chunk_index, chunk_data in chunks:
                key = CacheKeyGenerator.chunk_key(literature_id, chunk_index)
                if self.chunk_cache.set(key, chunk_data):
                    success_count += 1
            
            if success_count > 0:
                self.stats.record_set()
            
            return success_count == len(chunks)
        except Exception as e:
            self.logger.error(f"批量设置文档块缓存失败: {e}")
            return False
    
    # ====== 管理方法 ======
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            embedding_cleared = self.embedding_cache.clear()
            answer_cleared = self.answer_cache.clear()
            chunk_cleared = self.chunk_cache.clear()
            
            self.logger.info("所有缓存已清空")
            return embedding_cleared and answer_cleared and chunk_cleared
        except Exception as e:
            self.logger.error(f"清空所有缓存失败: {e}")
            return False
    
    def clear_by_literature(self, literature_id: str) -> bool:
        """清空指定文献的相关缓存"""
        try:
            cleared_count = 0
            
            # 清理答案缓存中相关的项
            answer_keys = self.answer_cache.keys()
            for key in answer_keys:
                if f":{literature_id}:" in key:
                    if self.answer_cache.delete(key):
                        cleared_count += 1
            
            # 清理文档块缓存
            chunk_keys = self.chunk_cache.keys()
            for key in chunk_keys:
                if key.startswith(f"chunk:{literature_id}:"):
                    if self.chunk_cache.delete(key):
                        cleared_count += 1
            
            self.logger.info(f"清理文献 {literature_id} 相关缓存 {cleared_count} 项")
            return True
        except Exception as e:
            self.logger.error(f"清理文献缓存失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            return {
                "global_stats": self.stats.get_stats(),
                "embedding_cache": self.embedding_cache.info(),
                "answer_cache": self.answer_cache.info(),
                "chunk_cache": self.chunk_cache.info(),
                "total_memory_items": (
                    self.embedding_cache.size() + 
                    self.answer_cache.size() + 
                    self.chunk_cache.size()
                )
            }
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """缓存健康检查"""
        try:
            stats = self.get_stats()
            hit_rate = stats.get("global_stats", {}).get("hit_rate", 0)
            
            # 检查命中率
            if hit_rate >= 0.6:
                hit_rate_status = "healthy"
            elif hit_rate >= 0.4:
                hit_rate_status = "warning"
            else:
                hit_rate_status = "critical"
            
            # 检查缓存使用率
            total_utilization = 0
            cache_count = 0
            
            for cache_name in ["embedding_cache", "answer_cache", "chunk_cache"]:
                cache_info = stats.get(cache_name, {})
                utilization = cache_info.get("utilization", 0)
                total_utilization += utilization
                cache_count += 1
            
            avg_utilization = total_utilization / cache_count if cache_count > 0 else 0
            
            if avg_utilization < 0.8:
                memory_status = "healthy"
            elif avg_utilization < 0.9:
                memory_status = "warning"
            else:
                memory_status = "critical"
            
            overall_status = "healthy"
            if hit_rate_status != "healthy" or memory_status != "healthy":
                overall_status = "warning" if "critical" not in [hit_rate_status, memory_status] else "critical"
            
            return {
                "status": overall_status,
                "hit_rate": {
                    "value": hit_rate,
                    "status": hit_rate_status
                },
                "memory_usage": {
                    "value": avg_utilization,
                    "status": memory_status
                },
                "details": stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"缓存健康检查失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# 创建全局缓存管理器实例
cache_manager = CacheManager() 
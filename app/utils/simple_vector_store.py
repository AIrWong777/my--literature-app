"""
简化向量存储实现
使用内存存储和余弦相似度计算，作为ChromaDB的临时替代方案
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from app.config import settings

# 配置日志
logger = logging.getLogger(__name__)

class SimpleVectorStore:
    """简化向量存储类"""
    
    def __init__(self):
        self.collections = {}  # 存储所有集合
        self.storage_path = os.path.join(settings.VECTOR_DB_PATH, "simple_store.json")
        self._ensure_storage_dir()
        self._load_from_disk()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        except Exception as e:
            logger.error(f"创建存储目录失败: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载数据"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.collections = data.get('collections', {})
                logger.info(f"从磁盘加载了 {len(self.collections)} 个集合")
        except Exception as e:
            logger.error(f"从磁盘加载数据失败: {e}")
            self.collections = {}
    
    def _save_to_disk(self):
        """保存数据到磁盘"""
        try:
            data = {'collections': self.collections}
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据到磁盘失败: {e}")
    
    def is_available(self) -> bool:
        """检查向量数据库是否可用"""
        return True  # 简化版本总是可用
    
    def get_collection_name(self, group_id: str) -> str:
        """获取研究组对应的集合名称"""
        return f"{settings.VECTOR_DB_COLLECTION_PREFIX}{group_id}"
    
    def create_collection_for_group(self, group_id: str) -> bool:
        """为研究组创建向量集合"""
        try:
            collection_name = self.get_collection_name(group_id)
            
            if collection_name not in self.collections:
                self.collections[collection_name] = {
                    "group_id": group_id,
                    "documents": [],
                    "embeddings": [],
                    "metadatas": [],
                    "ids": []
                }
                self._save_to_disk()
                logger.info(f"为研究组 {group_id} 创建向量集合: {collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"创建向量集合失败: {e}")
            return False
    
    def get_or_create_collection(self, group_id: str):
        """获取或创建集合"""
        collection_name = self.get_collection_name(group_id)
        
        if collection_name not in self.collections:
            self.create_collection_for_group(group_id)
        
        return self.collections.get(collection_name)
    
    def store_document_chunks(
        self, 
        chunks_data: List[Dict], 
        embeddings: List[List[float]], 
        literature_id: str, 
        group_id: str
    ) -> bool:
        """存储文档块到向量数据库"""
        if len(chunks_data) != len(embeddings):
            logger.error("文档块数量与向量数量不匹配")
            return False
        
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                logger.error(f"无法获取研究组 {group_id} 的向量集合")
                return False
            
            # 添加数据到集合
            for i, chunk in enumerate(chunks_data):
                collection["ids"].append(chunk["chunk_id"])
                collection["documents"].append(chunk["text"])
                collection["embeddings"].append(embeddings[i])
                
                metadata = {
                    "literature_id": chunk["literature_id"],
                    "group_id": chunk["group_id"],
                    "chunk_index": chunk["chunk_index"],
                    "literature_title": chunk.get("literature_title", ""),
                    "chunk_length": chunk["chunk_length"]
                }
                collection["metadatas"].append(metadata)
            
            self._save_to_disk()
            logger.info(f"成功存储 {len(chunks_data)} 个文档块到向量数据库")
            return True
            
        except Exception as e:
            logger.error(f"存储文档块失败: {e}")
            return False
    
    def delete_document_chunks(self, literature_id: str, group_id: str) -> bool:
        """删除文献对应的所有向量"""
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                logger.warning(f"研究组 {group_id} 的向量集合不存在")
                return True
            
            # 找到要删除的索引
            indices_to_remove = []
            for i, metadata in enumerate(collection["metadatas"]):
                if metadata.get("literature_id") == literature_id:
                    indices_to_remove.append(i)
            
            # 从后往前删除，避免索引变化
            for i in reversed(indices_to_remove):
                collection["ids"].pop(i)
                collection["documents"].pop(i)
                collection["embeddings"].pop(i)
                collection["metadatas"].pop(i)
            
            self._save_to_disk()
            logger.info(f"删除文献 {literature_id} 的 {len(indices_to_remove)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"删除文档向量失败: {e}")
            return False
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            # 转换为numpy数组
            a = np.array(vec1)
            b = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {e}")
            return 0.0
    
    def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        group_id: str, 
        literature_id: Optional[str] = None, 
        top_k: int = None
    ) -> List[Dict]:
        """搜索相似的文档块"""
        top_k = top_k or settings.MAX_RETRIEVAL_DOCS
        
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                logger.warning(f"研究组 {group_id} 的向量集合不存在")
                return []
            
            # 计算相似度
            similarities = []
            for i, embedding in enumerate(collection["embeddings"]):
                metadata = collection["metadatas"][i]
                
                # 如果指定了文献ID，则过滤
                if literature_id and metadata.get("literature_id") != literature_id:
                    continue
                
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append({
                    "index": i,
                    "similarity": similarity,
                    "text": collection["documents"][i],
                    "metadata": metadata
                })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # 取前top_k个结果
            results = similarities[:top_k]
            
            # 格式化结果
            search_results = []
            for result in results:
                search_result = {
                    "text": result["text"],
                    "metadata": result["metadata"],
                    "similarity": result["similarity"],
                    "literature_id": result["metadata"]["literature_id"],
                    "chunk_index": result["metadata"]["chunk_index"],
                    "literature_title": result["metadata"].get("literature_title", "")
                }
                search_results.append(search_result)
            
            logger.info(f"相似度搜索完成，返回 {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []
    
    def get_collection_stats(self, group_id: str) -> Dict:
        """获取集合统计信息"""
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                return {"error": "集合不存在"}
            
            # 统计文献数量
            literature_ids = set()
            for metadata in collection["metadatas"]:
                literature_ids.add(metadata["literature_id"])
            
            stats = {
                "collection_name": self.get_collection_name(group_id),
                "total_chunks": len(collection["documents"]),
                "total_literature": len(literature_ids),
                "literature_ids": list(literature_ids)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {"error": str(e)}
    
    def reset_collection(self, group_id: str) -> bool:
        """重置集合（删除所有数据）"""
        try:
            collection_name = self.get_collection_name(group_id)
            
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            # 重新创建空集合
            success = self.create_collection_for_group(group_id)
            if success:
                logger.info(f"重置集合: {collection_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"重置集合失败: {e}")
            return False
    
    def health_check(self) -> Dict:
        """健康检查"""
        try:
            return {
                "status": "healthy",
                "client_type": "SimpleVectorStore",
                "data_path": self.storage_path,
                "collections_count": len(self.collections),
                "collections": list(self.collections.keys())
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 创建全局简化向量存储实例
simple_vector_store = SimpleVectorStore() 
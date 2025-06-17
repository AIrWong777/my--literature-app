"""
向量数据库管理
使用ChromaDB进行文档向量存储和检索
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from app.config import settings

# 配置日志
logger = logging.getLogger(__name__)

class VectorStore:
    """向量数据库管理类"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化ChromaDB客户端"""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            # 确保向量数据库目录存在
            settings.ensure_vector_db_dir_exists()
            
            # 创建持久化客户端
            self.client = chromadb.PersistentClient(
                path=settings.VECTOR_DB_PATH,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            logger.info(f"ChromaDB客户端初始化成功，数据路径: {settings.VECTOR_DB_PATH}")
            
        except ImportError as e:
            logger.error(f"ChromaDB库导入失败: {e}")
            self.client = None
        except Exception as e:
            logger.error(f"初始化ChromaDB客户端失败: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查向量数据库是否可用"""
        return self.client is not None
    
    def get_collection_name(self, group_id: str) -> str:
        """获取研究组对应的集合名称"""
        # 处理私人文献的情况
        if group_id is None:
            return f"{settings.VECTOR_DB_COLLECTION_PREFIX}private"
        return f"{settings.VECTOR_DB_COLLECTION_PREFIX}{group_id}"
    
    def create_collection_for_group(self, group_id: str) -> bool:
        """为研究组创建向量集合"""
        if not self.is_available():
            logger.error("向量数据库不可用")
            return False
        
        try:
            collection_name = self.get_collection_name(group_id)
            
            # 检查集合是否已存在
            try:
                existing_collection = self.client.get_collection(collection_name)
                logger.info(f"集合 {collection_name} 已存在")
                return True
            except:
                # 集合不存在，创建新集合
                pass
            
            # 创建新集合
            collection_metadata = {
                "group_id": group_id if group_id is not None else "private",
                "created_at": str(int(os.times().elapsed))  # 使用简单的时间戳
            }
            
            collection = self.client.create_collection(
                name=collection_name,
                metadata=collection_metadata
            )
            
            logger.info(f"为研究组 {group_id} 创建向量集合: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建向量集合失败: {e}")
            return False
    
    def get_or_create_collection(self, group_id: str):
        """获取或创建集合"""
        if not self.is_available():
            return None
        
        try:
            collection_name = self.get_collection_name(group_id)
            
            # 尝试获取现有集合
            try:
                collection = self.client.get_collection(collection_name)
                return collection
            except:
                # 集合不存在，创建新集合
                if self.create_collection_for_group(group_id):
                    return self.client.get_collection(collection_name)
                return None
                
        except Exception as e:
            logger.error(f"获取或创建集合失败: {e}")
            return None
    
    def store_document_chunks_with_embeddings(
        self, 
        chunks_data: List[Dict], 
        literature_id: str, 
        group_id: str
    ) -> bool:
        """
        存储文档块到向量数据库（自动生成embeddings）
        
        Args:
            chunks_data: 文档块数据列表
            literature_id: 文献ID
            group_id: 研究组ID
            
        Returns:
            bool: 是否存储成功
        """
        if not self.is_available():
            logger.error("向量数据库不可用")
            return False
        
        try:
            # 自动生成embeddings
            from .embedding_service import embedding_service
            texts = [chunk['text'] for chunk in chunks_data]
            embeddings, failed = embedding_service.batch_generate_embeddings(texts)
            
            if not embeddings or len(embeddings) != len(chunks_data):
                logger.error("Embedding生成失败或数量不匹配")
                return False
            
            return self.store_document_chunks(chunks_data, embeddings, literature_id, group_id)
            
        except Exception as e:
            logger.error(f"存储文档块失败: {e}")
            return False

    def store_document_chunks(
        self, 
        chunks_data: List[Dict], 
        embeddings: List[List[float]], 
        literature_id: str, 
        group_id: str
    ) -> bool:
        """
        存储文档块到向量数据库
        
        Args:
            chunks_data: 文档块数据列表
            embeddings: 对应的向量列表
            literature_id: 文献ID
            group_id: 研究组ID
            
        Returns:
            bool: 是否存储成功
        """
        if not self.is_available():
            logger.error("向量数据库不可用")
            return False
        
        if len(chunks_data) != len(embeddings):
            logger.error("文档块数量与向量数量不匹配")
            return False
        
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                logger.error(f"无法获取研究组 {group_id} 的向量集合")
                return False
            
            # 准备数据
            ids = [chunk["chunk_id"] for chunk in chunks_data]
            documents = [chunk["text"] for chunk in chunks_data]
            metadatas = []
            
            for chunk in chunks_data:
                metadata = {
                    "literature_id": chunk["literature_id"],
                    "group_id": chunk["group_id"] if chunk["group_id"] is not None else "private",
                    "chunk_index": str(chunk["chunk_index"]),  # 确保是字符串
                    "literature_title": chunk.get("literature_title", ""),
                    "chunk_length": str(chunk["chunk_length"])  # 确保是字符串
                }
                metadatas.append(metadata)
            
            # 存储到向量数据库
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"成功存储 {len(chunks_data)} 个文档块到向量数据库")
            return True
            
        except Exception as e:
            logger.error(f"存储文档块失败: {e}")
            return False
    
    def delete_document_chunks(self, literature_id: str, group_id: str) -> bool:
        """
        删除文献对应的所有向量
        
        Args:
            literature_id: 文献ID
            group_id: 研究组ID
            
        Returns:
            bool: 是否删除成功
        """
        if not self.is_available():
            logger.error("向量数据库不可用")
            return False
        
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                logger.warning(f"研究组 {group_id} 的向量集合不存在")
                return True
            
            # 查询该文献的所有向量
            results = collection.get(
                where={"literature_id": literature_id}
            )
            
            if results["ids"]:
                # 删除找到的向量
                collection.delete(ids=results["ids"])
                logger.info(f"删除文献 {literature_id} 的 {len(results['ids'])} 个向量")
            else:
                logger.info(f"文献 {literature_id} 没有找到对应的向量")
            
            return True
            
        except Exception as e:
            logger.error(f"删除文档向量失败: {e}")
            return False
    
    def search_similar_chunks_by_query(
        self, 
        query: str, 
        group_id: str, 
        literature_id: Optional[str] = None, 
        top_k: int = None
    ) -> List[Dict]:
        """
        使用查询文本搜索相似的文档块（自动生成embedding）
        
        Args:
            query: 查询文本
            group_id: 研究组ID
            literature_id: 可选的文献ID（限制搜索范围）
            top_k: 返回的最大结果数
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 自动生成查询embedding
            from .embedding_service import embedding_service
            query_embedding = embedding_service.generate_query_embedding(query)
            
            if not query_embedding:
                logger.error("查询embedding生成失败")
                return []
            
            return self.search_similar_chunks(query_embedding, group_id, literature_id, top_k)
            
        except Exception as e:
            logger.error(f"查询搜索失败: {e}")
            return []
    
    def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        group_id: str, 
        literature_id: Optional[str] = None, 
        top_k: int = None
    ) -> List[Dict]:
        """
        搜索相似的文档块
        
        Args:
            query_embedding: 查询向量
            group_id: 研究组ID
            literature_id: 可选的文献ID（限制搜索范围）
            top_k: 返回的最大结果数
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not self.is_available():
            logger.error("向量数据库不可用")
            return []
        
        top_k = top_k or settings.MAX_RETRIEVAL_DOCS
        
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                logger.warning(f"研究组 {group_id} 的向量集合不存在")
                return []
            
            # 构建查询条件 - 修复私人文献的group_id处理
            actual_group_id = group_id if group_id is not None else "private"
            
            if literature_id:
                # 如果指定了文献ID，同时过滤group_id和literature_id
                where_condition = {
                    "$and": [
                        {"group_id": {"$eq": actual_group_id}},
                        {"literature_id": {"$eq": literature_id}}
                    ]
                }
            else:
                # 只过滤group_id
                where_condition = {"group_id": {"$eq": actual_group_id}}
            
            # 执行相似度搜索
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_condition,
                include=["documents", "metadatas", "distances"]
            )
            
            logger.debug(f"ChromaDB查询参数: n_results={top_k}, where={where_condition}")
            logger.debug(f"ChromaDB原始结果: {len(results.get('documents', [[]])[0])} 个文档")
            
            # 格式化结果
            search_results = []
            if results["documents"] and results["documents"][0]:
                logger.debug("开始处理查询结果...")
                for i in range(len(results["documents"][0])):
                    # 修复相似度计算：对于余弦距离，相似度 = 1 - 距离
                    # 但需要确保结果在合理范围内
                    distance = results["distances"][0][i]
                    
                    # ChromaDB默认使用L2距离，我们需要处理不同的距离度量
                    # 对于L2距离，我们使用基于距离的相似度计算
                    if distance <= 0:
                        similarity = 1.0  # 完全相同
                    elif distance >= 2.0:
                        similarity = 0.0  # 完全不相似
                    else:
                        # 将L2距离转换为0-1的相似度分数
                        similarity = max(0.0, 1.0 - (distance / 2.0))
                    
                    logger.debug(f"结果 {i}: raw_distance={distance:.4f}, calculated_similarity={similarity:.4f}")
                    
                    result = {
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity": similarity,  # 现在应该在[0,1]范围内
                        "raw_distance": distance,  # 保留原始距离用于调试
                        "literature_id": results["metadatas"][0][i]["literature_id"],
                        "chunk_index": results["metadatas"][0][i]["chunk_index"],
                        "literature_title": results["metadatas"][0][i].get("literature_title", "")
                    }
                    search_results.append(result)
            
            logger.info(f"相似度搜索完成，返回 {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []
    
    def get_collection_stats(self, group_id: str) -> Dict:
        """
        获取集合统计信息
        
        Args:
            group_id: 研究组ID
            
        Returns:
            Dict: 统计信息
        """
        if not self.is_available():
            return {"error": "向量数据库不可用"}
        
        try:
            collection = self.get_or_create_collection(group_id)
            if not collection:
                return {"error": "集合不存在"}
            
            # 获取集合中的文档数量
            count = collection.count()
            
            # 获取所有文献ID
            all_results = collection.get(include=["metadatas"])
            literature_ids = set()
            if all_results["metadatas"]:
                for metadata in all_results["metadatas"]:
                    literature_ids.add(metadata["literature_id"])
            
            stats = {
                "collection_name": self.get_collection_name(group_id),
                "total_chunks": count,
                "total_literature": len(literature_ids),
                "literature_ids": list(literature_ids)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {"error": str(e)}
    
    def reset_collection(self, group_id: str) -> bool:
        """
        重置集合（删除所有数据）
        
        Args:
            group_id: 研究组ID
            
        Returns:
            bool: 是否重置成功
        """
        if not self.is_available():
            logger.error("向量数据库不可用")
            return False
        
        try:
            collection_name = self.get_collection_name(group_id)
            
            # 删除现有集合
            try:
                self.client.delete_collection(collection_name)
                logger.info(f"删除集合: {collection_name}")
            except:
                pass  # 集合可能不存在
            
            # 重新创建集合
            return self.create_collection_for_group(group_id)
            
        except Exception as e:
            logger.error(f"重置集合失败: {e}")
            return False
    
    def health_check(self) -> Dict:
        """
        健康检查
        
        Returns:
            Dict: 健康状态信息
        """
        if not self.is_available():
            return {
                "status": "unhealthy",
                "error": "ChromaDB客户端未初始化"
            }
        
        try:
            # 尝试列出所有集合
            collections = self.client.list_collections()
            
            return {
                "status": "healthy",
                "client_type": "ChromaDB",
                "data_path": settings.VECTOR_DB_PATH,
                "collections_count": len(collections),
                "collections": [col.name for col in collections]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# 创建全局向量存储实例
try:
    vector_store = VectorStore()
    if not vector_store.is_available():
        # 如果ChromaDB不可用，使用简化版本
        from .simple_vector_store import simple_vector_store
        vector_store = simple_vector_store
        logger.info("ChromaDB不可用，使用简化向量存储")
except Exception as e:
    logger.error(f"初始化向量存储失败: {e}")
    # 使用简化版本作为备用
    from .simple_vector_store import simple_vector_store
    vector_store = simple_vector_store
    logger.info("使用简化向量存储作为备用")
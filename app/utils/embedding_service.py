"""
Embedding服务
支持OpenAI和Google的文本向量化服务
"""

import time
import logging
from typing import List, Optional, Dict, Tuple
from app.config import settings
from app.utils.cache_manager import cache_manager

# 配置日志
logger = logging.getLogger(__name__)

class EmbeddingService:
    """文本向量化服务类"""
    
    def __init__(self):
        self.provider = settings.get_ai_provider()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化AI客户端"""
        try:
            if self.provider == "openai":
                self._initialize_openai_client()
            elif self.provider == "google":
                self._initialize_google_client()
            else:
                logger.warning("未配置AI服务提供商")
                
        except Exception as e:
            logger.error(f"初始化AI客户端失败: {e}")
            self.client = None
    
    def _initialize_openai_client(self):
        """初始化OpenAI客户端"""
        try:
            import openai
            
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API密钥未配置")
            
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI客户端初始化成功")
            
        except ImportError:
            logger.error("OpenAI库未安装")
            raise
        except Exception as e:
            logger.error(f"初始化OpenAI客户端失败: {e}")
            raise
    
    def _initialize_google_client(self):
        """初始化Google客户端"""
        try:
            from google import genai
            
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API密钥未配置")
            
            # 使用新的SDK创建客户端
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            logger.info("Google GenAI客户端初始化成功")
            
        except ImportError as e:
            logger.error(f"Google GenAI库导入失败: {e}")
            raise
        except Exception as e:
            logger.error(f"初始化Google客户端失败: {e}")
            raise
    
    def is_available(self) -> bool:
        """检查embedding服务是否可用"""
        return self.client is not None and self.provider != "none"
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成单个文本的embedding（带缓存支持）
        
        Args:
            text: 要向量化的文本
            
        Returns:
            Optional[List[float]]: 向量，失败时返回None
        """
        if not self.is_available():
            logger.error("Embedding服务不可用")
            return None
        
        if not text or not text.strip():
            logger.warning("输入文本为空")
            return None
        
        # 1. 先检查缓存
        cached_embedding = cache_manager.get_embedding(text, self.provider)
        if cached_embedding is not None:
            logger.debug(f"Embedding缓存命中: {text[:30]}...")
            return cached_embedding
        
        # 2. 缓存未命中，生成新的embedding
        try:
            if self.provider == "openai":
                embedding = self._generate_openai_embedding(text)
            elif self.provider == "google":
                embedding = self._generate_google_embedding(text)
            else:
                logger.error(f"不支持的AI提供商: {self.provider}")
                return None
            
            # 3. 存入缓存
            if embedding:
                cache_manager.set_embedding(text, embedding, self.provider)
                logger.debug(f"Embedding已缓存: {text[:30]}...")
            
            return embedding
                
        except Exception as e:
            logger.error(f"生成embedding失败: {e}")
            return None
    
    def _generate_openai_embedding(self, text: str) -> Optional[List[float]]:
        """使用OpenAI API生成embedding"""
        try:
            response = self.client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"OpenAI embedding生成成功，维度: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding生成失败: {e}")
            return None
    
    def _generate_google_embedding(self, text: str) -> Optional[List[float]]:
        """使用Google API生成embedding"""
        try:
            from google.genai import types
            
            # 使用新的SDK生成embedding
            response = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            
            # 获取embedding值
            if response.embeddings and len(response.embeddings) > 0:
                embedding = response.embeddings[0].values
                logger.debug(f"Google embedding生成成功，维度: {len(embedding)}")
                return embedding
            else:
                logger.error("未获取到embedding响应")
                return None
            
        except Exception as e:
            logger.error(f"Google embedding生成失败: {e}")
            logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
            return None
    
    def batch_generate_embeddings(
        self, 
        texts: List[str], 
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> Tuple[List[List[float]], List[str]]:
        """
        批量生成embeddings
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            delay_between_batches: 批次间延迟（秒）
            
        Returns:
            Tuple[List[List[float]], List[str]]: (成功的embeddings, 失败的文本)
        """
        if not self.is_available():
            logger.error("Embedding服务不可用")
            return [], texts
        
        embeddings = []
        failed_texts = []
        
        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            batch_embeddings = []
            batch_failed = []
            
            for text in batch_texts:
                embedding = self.generate_embedding(text)
                if embedding:
                    batch_embeddings.append(embedding)
                else:
                    batch_failed.append(text)
                    logger.warning(f"文本embedding生成失败: {text[:50]}...")
            
            embeddings.extend(batch_embeddings)
            failed_texts.extend(batch_failed)
            
            # 批次间延迟，避免API限制
            if i + batch_size < len(texts):
                time.sleep(delay_between_batches)
        
        success_rate = len(embeddings) / len(texts) * 100
        logger.info(f"批量embedding生成完成: {len(embeddings)}/{len(texts)} 成功 ({success_rate:.1f}%)")
        
        return embeddings, failed_texts
    
    def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        生成查询文本的embedding（可能与文档embedding有不同的处理）
        
        Args:
            query: 查询文本
            
        Returns:
            Optional[List[float]]: 查询向量
        """
        if not query or not query.strip():
            logger.warning("查询文本为空")
            return None
        
        # 对于查询文本，可能需要特殊处理
        if self.provider == "google":
            try:
                from google.genai import types
                
                # 使用新的SDK生成查询embedding
                response = self.client.models.embed_content(
                    model="text-embedding-004",
                    contents=query,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_QUERY"
                    )
                )
                
                # 获取embedding值
                if response.embeddings and len(response.embeddings) > 0:
                    return response.embeddings[0].values
                else:
                    logger.error("未获取到查询embedding响应")
                    return None
                    
            except Exception as e:
                logger.error(f"Google查询embedding生成失败: {e}")
                logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
                # 使用通用方法作为备用
                return self.generate_embedding(query)
        else:
            # OpenAI和其他提供商使用相同的方法
            return self.generate_embedding(query)
    
    def test_connection(self) -> Dict:
        """
        测试连接和服务可用性
        
        Returns:
            Dict: 测试结果
        """
        if not self.is_available():
            return {
                "status": "failed",
                "provider": self.provider,
                "error": "服务不可用"
            }
        
        try:
            # 使用简单文本测试
            test_text = "这是一个测试文本。"
            start_time = time.time()
            
            embedding = self.generate_embedding(test_text)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if embedding:
                return {
                    "status": "success",
                    "provider": self.provider,
                    "model": self._get_model_name(),
                    "embedding_dimension": len(embedding),
                    "response_time_seconds": round(response_time, 3)
                }
            else:
                return {
                    "status": "failed",
                    "provider": self.provider,
                    "error": "embedding生成失败"
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "provider": self.provider,
                "error": str(e)
            }
    
    def _get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        if self.provider == "openai":
            return settings.OPENAI_EMBEDDING_MODEL
        elif self.provider == "google":
            return settings.GEMINI_EMBEDDING_MODEL
        else:
            return "unknown"
    
    def get_embedding_info(self) -> Dict:
        """
        获取embedding服务信息
        
        Returns:
            Dict: 服务信息
        """
        return {
            "provider": self.provider,
            "model": self._get_model_name(),
            "available": self.is_available(),
            "api_key_configured": bool(
                settings.OPENAI_API_KEY if self.provider == "openai" 
                else settings.GOOGLE_API_KEY if self.provider == "google" 
                else False
            )
        }

# 创建全局embedding服务实例
embedding_service = EmbeddingService()
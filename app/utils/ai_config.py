"""
AI服务配置和初始化
支持Google Gemini和OpenAI
"""

import os
import logging
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self):
        self.provider = settings.get_ai_provider()
        self.llm_client = None
        self.embedding_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化AI客户端"""
        try:
            if self.provider == "google":
                self._initialize_google_clients()
            elif self.provider == "openai":
                self._initialize_openai_clients()
            else:
                logger.warning("未配置AI服务提供商")
        except Exception as e:
            logger.error(f"初始化AI客户端失败: {e}")
    
    def _initialize_google_clients(self):
        """初始化Google Gemini客户端"""
        try:
            import google.generativeai as genai
            from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
            
            # 配置Google AI
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            
            # 初始化LLM客户端
            self.llm_client = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1,
                max_tokens=settings.MAX_TOKENS_PER_REQUEST
            )
            
            # 初始化Embedding客户端
            self.embedding_client = GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key=settings.GOOGLE_API_KEY
            )
            
            logger.info("Google Gemini客户端初始化成功")
            
        except ImportError as e:
            logger.error(f"Google AI依赖包未安装: {e}")
            raise
        except Exception as e:
            logger.error(f"Google Gemini客户端初始化失败: {e}")
            raise
    
    def _initialize_openai_clients(self):
        """初始化OpenAI客户端"""
        try:
            from langchain_openai import ChatOpenAI, OpenAIEmbeddings
            
            # 初始化LLM客户端
            self.llm_client = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.1,
                max_tokens=settings.MAX_TOKENS_PER_REQUEST
            )
            
            # 初始化Embedding客户端
            self.embedding_client = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            logger.info("OpenAI客户端初始化成功")
            
        except ImportError as e:
            logger.error(f"OpenAI依赖包未安装: {e}")
            raise
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
    
    def get_llm_client(self):
        """获取LLM客户端"""
        if not self.llm_client:
            raise RuntimeError("LLM客户端未初始化")
        return self.llm_client
    
    def get_embedding_client(self):
        """获取Embedding客户端"""
        if not self.embedding_client:
            raise RuntimeError("Embedding客户端未初始化")
        return self.embedding_client
    
    def test_connection(self) -> tuple[bool, str]:
        """测试AI服务连接"""
        try:
            if self.provider == "google":
                return self._test_google_connection()
            elif self.provider == "openai":
                return self._test_openai_connection()
            else:
                return False, "未配置AI服务"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
    
    def _test_google_connection(self) -> tuple[bool, str]:
        """测试Google Gemini连接"""
        try:
            # 测试LLM
            response = self.llm_client.invoke("Hello")
            
            # 测试Embedding
            embeddings = self.embedding_client.embed_query("test")
            
            return True, f"Google Gemini连接正常 (模型: {settings.GEMINI_MODEL})"
        except Exception as e:
            return False, f"Google Gemini连接失败: {str(e)}"
    
    def _test_openai_connection(self) -> tuple[bool, str]:
        """测试OpenAI连接"""
        try:
            # 测试LLM
            response = self.llm_client.invoke("Hello")
            
            # 测试Embedding
            embeddings = self.embedding_client.embed_query("test")
            
            return True, f"OpenAI连接正常 (模型: {settings.OPENAI_MODEL})"
        except Exception as e:
            return False, f"OpenAI连接失败: {str(e)}"
    
    def get_provider_info(self) -> dict:
        """获取AI服务提供商信息"""
        if self.provider == "google":
            return {
                "provider": "Google Gemini",
                "llm_model": settings.GEMINI_MODEL,
                "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
                "cost": "免费",
                "rate_limit": "每分钟15次请求"
            }
        elif self.provider == "openai":
            return {
                "provider": "OpenAI",
                "llm_model": settings.OPENAI_MODEL,
                "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
                "cost": "付费",
                "rate_limit": "根据套餐"
            }
        else:
            return {
                "provider": "未配置",
                "llm_model": "N/A",
                "embedding_model": "N/A",
                "cost": "N/A",
                "rate_limit": "N/A"
            }

# 创建全局AI服务管理器实例
ai_manager = None

def get_ai_manager() -> AIServiceManager:
    """获取AI服务管理器实例（单例模式）"""
    global ai_manager
    if ai_manager is None:
        ai_manager = AIServiceManager()
    return ai_manager

def initialize_ai_service() -> tuple[bool, str]:
    """初始化AI服务"""
    try:
        manager = get_ai_manager()
        return manager.test_connection()
    except Exception as e:
        return False, f"AI服务初始化失败: {str(e)}" 
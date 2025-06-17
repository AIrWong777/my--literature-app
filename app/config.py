"""
应用配置文件
定义文件存储、上传限制、AI服务等配置
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # ===== 应用基础配置 =====
    APP_NAME: str = "文献管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # ===== JWT配置 =====
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 默认30天
    
    # ===== 文件存储配置 =====
    UPLOAD_ROOT_DIR = os.getenv("UPLOAD_DIR", "./uploads")  # 文件存储根目录
    
    # 允许的文件类型
    ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.doc']  # 只允许PDF和Word文档
    
    # 文件大小限制（字节）
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB
    
    # 文件类型MIME映射
    FILE_TYPE_MAPPING = {
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.doc': 'application/msword',
        '.html': 'text/html',
        '.htm': 'text/html',
        '.txt': 'text/plain'
    }
    
    # ===== AI服务配置 =====
    
    # Google Gemini配置（推荐免费选项）
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    
    # 备用OpenAI配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    # AI处理参数
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_RETRIEVAL_DOCS: int = int(os.getenv("MAX_RETRIEVAL_DOCS", "5"))
    MAX_TOKENS_PER_REQUEST: int = int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000"))
    AI_REQUEST_TIMEOUT: int = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))
    
    # 向量数据库配置
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./vector_db")
    VECTOR_DB_COLLECTION_PREFIX: str = "literature_group_"
    
    # ===== RAG问答系统配置 =====
    
    # RAG核心参数
    RAG_MAX_CONTEXT_TOKENS: int = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "4000"))
    RAG_TOP_K_RETRIEVAL: int = int(os.getenv("RAG_TOP_K_RETRIEVAL", "5"))
    RAG_CONVERSATION_MAX_TURNS: int = int(os.getenv("RAG_CONVERSATION_MAX_TURNS", "10"))
    RAG_CACHE_TTL: int = int(os.getenv("RAG_CACHE_TTL", "3600"))  # 1小时
    RAG_AI_TIMEOUT: int = int(os.getenv("RAG_AI_TIMEOUT", "30"))  # 30秒
    MAX_CHUNK_LENGTH_FOR_PROMPT = 800 # 每个块在提示词中的最大字符数
    
    # 答案质量控制
    RAG_MIN_CONFIDENCE: float = float(os.getenv("RAG_MIN_CONFIDENCE", "0.3"))
    RAG_MAX_ANSWER_LENGTH: int = int(os.getenv("RAG_MAX_ANSWER_LENGTH", "2000"))
    RAG_MIN_ANSWER_LENGTH: int = int(os.getenv("RAG_MIN_ANSWER_LENGTH", "10"))
    
    # 缓存配置
    RAG_CACHE_EMBEDDING_MAX_SIZE: int = int(os.getenv("RAG_CACHE_EMBEDDING_MAX_SIZE", "1000"))
    RAG_CACHE_ANSWER_MAX_SIZE: int = int(os.getenv("RAG_CACHE_ANSWER_MAX_SIZE", "500"))
    RAG_CACHE_CHUNK_MAX_SIZE: int = int(os.getenv("RAG_CACHE_CHUNK_MAX_SIZE", "2000"))
    
    # ===== 日志配置 =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "literature_system.log")
    
    # ===== 原有文件存储方法 =====
    
    @classmethod
    def get_upload_dir(cls, group_id: str) -> str:
        """获取指定研究组的上传目录路径"""
        return os.path.join(cls.UPLOAD_ROOT_DIR, group_id)
    
    @classmethod
    def ensure_upload_dir_exists(cls, group_id: str) -> str:
        """确保上传目录存在，如果不存在则创建"""
        upload_dir = cls.get_upload_dir(group_id)
        Path(upload_dir).mkdir(parents=True, exist_ok=True)
        return upload_dir
    
    @classmethod
    def is_allowed_file_type(cls, filename: str) -> bool:
        """检查文件类型是否被允许"""
        file_ext = Path(filename).suffix.lower()
        return file_ext in cls.ALLOWED_FILE_TYPES
    
    @classmethod
    def get_file_type(cls, filename: str) -> str:
        """获取文件类型"""
        return Path(filename).suffix.lower()
    
    @classmethod
    def is_file_size_valid(cls, file_size: int) -> bool:
        """检查文件大小是否在允许范围内"""
        return 0 < file_size <= cls.MAX_FILE_SIZE
    
    # ===== 新增AI相关方法 =====
    
    @classmethod
    def get_ai_provider(cls) -> str:
        """获取当前配置的AI服务提供商"""
        if cls.GOOGLE_API_KEY:
            return "google"
        elif cls.OPENAI_API_KEY:
            return "openai"
        else:
            return "none"
    
    @classmethod
    def validate_ai_config(cls) -> Tuple[bool, str]:
        """验证AI配置是否完整"""
        provider = cls.get_ai_provider()
        
        if provider == "google":
            if not cls.GOOGLE_API_KEY:
                return False, "Google API密钥未配置"
            return True, f"Google Gemini配置正常 (模型: {cls.GEMINI_MODEL})"
        
        elif provider == "openai":
            if not cls.OPENAI_API_KEY:
                return False, "OpenAI API密钥未配置"
            return True, f"OpenAI配置正常 (模型: {cls.OPENAI_MODEL})"
        
        else:
            return False, "未配置任何AI服务提供商，请在.env文件中设置GOOGLE_API_KEY或OPENAI_API_KEY"
    
    @classmethod
    def get_vector_db_path(cls, group_id: str = None) -> str:
        """获取向量数据库路径"""
        if group_id:
            return os.path.join(cls.VECTOR_DB_PATH, f"{cls.VECTOR_DB_COLLECTION_PREFIX}{group_id}")
        return cls.VECTOR_DB_PATH
    
    @classmethod
    def ensure_vector_db_dir_exists(cls) -> str:
        """确保向量数据库目录存在"""
        Path(cls.VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
        return cls.VECTOR_DB_PATH
    
    @classmethod
    def get_content_type(cls, filename: str) -> str:
        """根据文件扩展名获取Content-Type"""
        file_ext = cls.get_file_type(filename)
        return cls.FILE_TYPE_MAPPING.get(file_ext, 'application/octet-stream')
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """获取配置摘要信息"""
        ai_provider = cls.get_ai_provider()
        ai_valid, ai_message = cls.validate_ai_config()
        
        return {
            "app_name": cls.APP_NAME,
            "app_version": cls.APP_VERSION,
            "debug": cls.DEBUG,
            "upload_dir": cls.UPLOAD_ROOT_DIR,
            "max_file_size_mb": cls.MAX_FILE_SIZE // (1024 * 1024),
            "allowed_file_types": cls.ALLOWED_FILE_TYPES,
            "ai_provider": ai_provider,
            "ai_config_valid": ai_valid,
            "ai_message": ai_message,
            "vector_db_path": cls.VECTOR_DB_PATH,
            "chunk_size": cls.CHUNK_SIZE,
            "max_retrieval_docs": cls.MAX_RETRIEVAL_DOCS
        }

# 创建配置实例（保持向后兼容）
config = Config()

# 新的设置实例（推荐使用）
settings = Config()

if not settings.SECRET_KEY:
    raise ValueError(
        "A SECRET_KEY must be set in the environment variables. "
        "Please create a .env file and set the SECRET_KEY. "
        "It should be a long, random string."
    )

# 导出常用配置（保持向后兼容）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./literature_system.db")
SECRET_KEY = settings.SECRET_KEY
UPLOAD_DIR = settings.UPLOAD_ROOT_DIR
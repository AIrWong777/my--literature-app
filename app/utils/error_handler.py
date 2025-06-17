"""
错误处理工具模块
提供统一的错误处理和日志记录功能
"""

import logging
import traceback
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('literature_system.log', encoding='utf-8')  # 输出到文件
    ]
)

logger = logging.getLogger(__name__)

class LiteratureSystemError(Exception):
    """系统自定义异常基类"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class FileUploadError(LiteratureSystemError):
    """文件上传相关错误"""
    pass

class PermissionError(LiteratureSystemError):
    """权限相关错误"""
    pass

class ValidationError(LiteratureSystemError):
    """验证相关错误"""
    pass

def log_error(operation: str, error: Exception, user_id: str = None, extra_info: Dict[str, Any] = None):
    """
    记录错误日志
    
    Args:
        operation: 操作名称
        error: 异常对象
        user_id: 用户ID
        extra_info: 额外信息
    """
    error_info = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
    }
    
    if extra_info:
        error_info.update(extra_info)
    
    logger.error(f"操作失败: {error_info}")
    
    # 记录详细的堆栈跟踪（仅在调试模式下）
    if os.getenv("DEBUG", "false").lower() == "true":
        logger.debug(f"堆栈跟踪: {traceback.format_exc()}")

def log_success(operation: str, user_id: str = None, extra_info: Dict[str, Any] = None):
    """
    记录成功操作日志
    
    Args:
        operation: 操作名称
        user_id: 用户ID
        extra_info: 额外信息
    """
    success_info = {
        "operation": operation,
        "user_id": user_id,
        "status": "success"
    }
    
    if extra_info:
        success_info.update(extra_info)
    
    logger.info(f"操作成功: {success_info}")

def handle_file_upload_error(error: Exception, filename: str = None, user_id: str = None) -> HTTPException:
    """
    处理文件上传错误
    
    Args:
        error: 异常对象
        filename: 文件名
        user_id: 用户ID
        
    Returns:
        HTTPException: 格式化的HTTP异常
    """
    extra_info = {"filename": filename} if filename else {}
    
    if isinstance(error, FileUploadError):
        log_error("file_upload", error, user_id, extra_info)
        return HTTPException(status_code=400, detail=error.message)
    
    elif isinstance(error, PermissionError):
        log_error("file_upload_permission", error, user_id, extra_info)
        return HTTPException(status_code=403, detail=error.message)
    
    elif isinstance(error, ValidationError):
        log_error("file_upload_validation", error, user_id, extra_info)
        return HTTPException(status_code=400, detail=error.message)
    
    elif isinstance(error, OSError):
        # 文件系统错误
        log_error("file_system", error, user_id, extra_info)
        return HTTPException(status_code=500, detail="文件存储失败，请稍后重试")
    
    elif isinstance(error, SQLAlchemyError):
        # 数据库错误
        log_error("database", error, user_id, extra_info)
        return HTTPException(status_code=500, detail="数据库操作失败，请稍后重试")
    
    else:
        # 未知错误
        log_error("unknown", error, user_id, extra_info)
        return HTTPException(status_code=500, detail="系统内部错误，请稍后重试")

def handle_permission_error(error: Exception, operation: str, user_id: str = None) -> HTTPException:
    """
    处理权限相关错误
    
    Args:
        error: 异常对象
        operation: 操作名称
        user_id: 用户ID
        
    Returns:
        HTTPException: 格式化的HTTP异常
    """
    log_error(f"permission_{operation}", error, user_id)
    
    if "不存在" in str(error):
        return HTTPException(status_code=404, detail=str(error))
    elif "无权" in str(error) or "权限" in str(error):
        return HTTPException(status_code=403, detail=str(error))
    else:
        return HTTPException(status_code=400, detail=str(error))

def validate_file_upload(file, group_id: str, user_id: str) -> None:
    """
    验证文件上传的各项条件
    
    Args:
        file: 上传的文件对象
        group_id: 研究组ID
        user_id: 用户ID
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    # 检查文件名
    if not file.filename:
        raise ValidationError("文件名不能为空")
    
    # 检查文件名长度
    if len(file.filename) > 255:
        raise ValidationError("文件名过长，请使用较短的文件名")
    
    # 检查研究组ID格式
    if not group_id or len(group_id.strip()) == 0:
        raise ValidationError("研究组ID不能为空")

def safe_file_operation(operation_name: str, operation_func, *args, **kwargs):
    """
    安全执行文件操作
    
    Args:
        operation_name: 操作名称
        operation_func: 操作函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        操作结果
        
    Raises:
        FileUploadError: 文件操作失败时抛出
    """
    try:
        result = operation_func(*args, **kwargs)
        log_success(operation_name)
        return result
    except OSError as e:
        if "No space left on device" in str(e):
            raise FileUploadError("存储空间不足，无法保存文件")
        elif "Permission denied" in str(e):
            raise FileUploadError("文件保存权限不足")
        else:
            raise FileUploadError(f"文件操作失败: {str(e)}")
    except Exception as e:
        raise FileUploadError(f"文件操作异常: {str(e)}")

def get_user_friendly_error_message(error: Exception) -> str:
    """
    获取用户友好的错误消息
    
    Args:
        error: 异常对象
        
    Returns:
        str: 用户友好的错误消息
    """
    error_messages = {
        "Connection refused": "服务暂时不可用，请稍后重试",
        "Timeout": "操作超时，请检查网络连接",
        "Permission denied": "权限不足，请联系管理员",
        "No space left": "存储空间不足，请联系管理员",
        "File not found": "文件未找到",
        "Invalid file": "文件格式不正确",
    }
    
    error_str = str(error).lower()
    
    for key, message in error_messages.items():
        if key.lower() in error_str:
            return message
    
    # 如果是自定义异常，直接返回消息
    if isinstance(error, LiteratureSystemError):
        return error.message
    
    # 默认消息
    return "操作失败，请稍后重试"
"""
文件处理工具模块
负责文件上传、验证、存储等功能
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
import logging
import shutil
import mimetypes
from urllib.parse import quote
import unicodedata
import re

from app.config import config
from app.utils.storage_manager import ensure_group_directory, get_unique_filename

logger = logging.getLogger(__name__)

# 上传根目录
UPLOAD_ROOT = "uploads"

# 允许的文件类型
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.md'}

# 确保上传目录存在
os.makedirs(UPLOAD_ROOT, exist_ok=True)

def normalize_filename(filename: str) -> str:
    """
    规范化文件名，处理中文和特殊字符
    """
    # 确保文件名是UTF-8编码
    if isinstance(filename, bytes):
        try:
            filename = filename.decode('utf-8')
        except UnicodeDecodeError:
            try:
                filename = filename.decode('latin-1')
            except:
                filename = "unknown_file"
    
    # 规范化Unicode字符
    filename = unicodedata.normalize('NFC', filename)
    
    # 移除不安全的文件名字符
    filename = re.sub(r'[\\/*?:"<>|]', '_', filename)
    
    return filename

def validate_file_type(filename: str) -> bool:
    """
    验证文件类型是否被允许
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否为允许的文件类型
    """
    file_ext = Path(filename).suffix.lower()
    is_allowed = file_ext in ALLOWED_EXTENSIONS
    logger.info(f"验证文件类型: {filename} -> {file_ext} -> {'允许' if is_allowed else '不允许'}")
    return is_allowed

def validate_file_size(file_size: int) -> bool:
    """
    验证文件大小是否在允许范围内
    
    Args:
        file_size: 文件大小（字节）
        
    Returns:
        bool: 是否在允许范围内
    """
    return file_size <= config.MAX_FILE_SIZE

def generate_file_path(group_dir: str, filename: str) -> tuple[str, str]:
    """
    生成文件存储路径
    返回: (完整路径, 相对路径)
    """
    # 规范化文件名
    filename = normalize_filename(filename)
    
    # 确保研究组目录存在
    group_path = os.path.join(UPLOAD_ROOT, group_dir)
    logger.info(f"确保研究组目录存在: {group_path}")
    os.makedirs(group_path, exist_ok=True)
    
    # 检查目录写入权限
    if not os.access(group_path, os.W_OK):
        logger.error(f"研究组目录 {group_dir} 没有写入权限")
        raise HTTPException(status_code=500, detail="存储目录无写入权限")
    
    logger.info(f"研究组目录 {group_dir} 写入权限正常")
    
    # 生成唯一文件名（处理文件名冲突）
    logger.info(f"生成唯一文件名: {filename} in {group_dir}")
    
    # 检查文件是否已存在
    full_path = os.path.join(group_path, filename)
    relative_path = os.path.join(group_dir, filename)
    
    counter = 1
    base_name, ext = os.path.splitext(filename)
    
    # 如果文件已存在，添加数字后缀
    while os.path.exists(full_path):
        new_filename = f"{base_name}_{counter}{ext}"
        full_path = os.path.join(group_path, new_filename)
        relative_path = os.path.join(group_dir, new_filename)
        counter += 1
    
    if counter > 1:
        logger.info(f"文件名已存在，使用新名称: {os.path.basename(full_path)}")
    else:
        logger.info(f"文件名 {filename} 可直接使用")
    
    return full_path, relative_path

async def save_uploaded_file(file: UploadFile, destination: str) -> bool:
    """
    保存上传的文件到指定路径
    返回: 是否成功
    """
    try:
        # 确保目标目录存在
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # 使用with语句确保文件正确关闭
        with open(destination, "wb") as buffer:
            # 分块读取和写入文件
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文件保存成功: {destination}")
        return True
        
    except Exception as e:
        logger.error(f"保存文件失败 {destination}: {str(e)}")
        return False

    finally:
        # 确保文件指针重置，以便后续可能的操作
        await file.seek(0)

def validate_upload_file(file: UploadFile) -> tuple[bool, str]:
    """
    验证上传的文件
    返回: (是否有效, 错误信息)
    """
    logger.info(f"开始验证文件: {file.filename}")
    
    # 检查文件名
    if not file.filename:
        return False, "文件名不能为空"
    
    # 规范化文件名
    file.filename = normalize_filename(file.filename)
    
    # 检查文件扩展名
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        allowed_exts = ', '.join(ALLOWED_EXTENSIONS)
        logger.info(f"文件类型不允许: {file.filename} -> {ext} -> 不在 {allowed_exts} 中")
        return False, f"不支持的文件类型。允许的类型: {allowed_exts}"
    
    logger.info(f"验证文件类型: {file.filename} -> {ext} -> 允许")
    
    # 文件大小限制 (50MB)
    # FastAPI 会自动处理文件大小，这里可以添加额外的检查
    
    logger.info(f"文件验证通过: {file.filename}")
    return True, ""

def get_file_info(file: UploadFile) -> dict:
    """
    获取文件信息
    """
    # 规范化文件名
    filename = normalize_filename(file.filename)
    
    _, ext = os.path.splitext(filename.lower())
    
    # 获取MIME类型
    content_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    
    return {
        "filename": filename,
        "file_type": ext,
        "content_type": content_type,
        "file_size": 0  # 实际大小需要在保存后获取
    }

def cleanup_file(file_path: str) -> bool:
    """
    清理文件（删除物理文件）
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 清理是否成功
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"文件清理成功: {file_path}")
            return True
        else:
            logger.warning(f"文件不存在，无需清理: {file_path}")
            return True
    except Exception as e:
        logger.error(f"文件清理失败: {e}")
        return False

def get_file_stats(file_path: str) -> Optional[dict]:
    """
    获取文件统计信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        Optional[dict]: 文件统计信息，如果文件不存在返回None
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime
        }
    except Exception as e:
        logger.error(f"获取文件统计失败: {e}")
        return None

def get_safe_filename_for_headers(filename: str) -> str:
    """
    获取适用于HTTP头的安全文件名（处理中文等特殊字符）
    """
    # 规范化文件名
    filename = normalize_filename(filename)
    
    # 使用RFC 5987编码，支持UTF-8
    filename_encoded = quote(filename.encode('utf-8'))
    return f"filename*=UTF-8''{filename_encoded}"
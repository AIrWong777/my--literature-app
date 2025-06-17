"""
存储目录管理模块
负责文件存储目录的创建、管理和维护
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import sys
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('literature_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from app.config import config

class StorageManager:
    """存储管理器"""
    
    def __init__(self):
        self.upload_root = Path(config.UPLOAD_ROOT_DIR)
        logger.info(f"初始化存储管理器，上传根目录: {self.upload_root}")
        self._ensure_upload_root()
    
    def _ensure_upload_root(self):
        """确保上传根目录存在并有正确的权限"""
        try:
            self.upload_root.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保上传根目录存在: {self.upload_root}")
            
            # 测试写入权限
            test_file = self.upload_root / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                logger.info("上传根目录写入权限正常")
            except Exception as e:
                logger.error(f"上传根目录写入权限测试失败: {e}")
                raise
                
        except Exception as e:
            logger.error(f"创建上传根目录失败: {e}")
            raise
    
    def ensure_group_directory(self, group_id: str) -> str:
        """
        确保研究组目录存在
        
        Args:
            group_id: 研究组ID
            
        Returns:
            str: 目录路径
        """
        try:
            group_dir = self.upload_root / group_id
            group_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保研究组目录存在: {group_dir}")
            
            # 测试写入权限
            test_file = group_dir / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                logger.info(f"研究组目录 {group_id} 写入权限正常")
            except Exception as e:
                logger.error(f"研究组目录 {group_id} 写入权限测试失败: {e}")
                raise
            
            return str(group_dir)
            
        except Exception as e:
            logger.error(f"创建研究组目录失败: {e}")
            raise
    
    def get_group_directory_info(self, group_id: str) -> Dict:
        """
        获取研究组目录信息
        
        Args:
            group_id: 研究组ID
            
        Returns:
            Dict: 目录信息
        """
        group_dir = self.upload_root / group_id
        
        if not group_dir.exists():
            return {
                "exists": False,
                "path": str(group_dir),
                "file_count": 0,
                "total_size": 0,
                "files": []
            }
        
        files = []
        total_size = 0
        
        for file_path in group_dir.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                total_size += file_size
                
                files.append({
                    "name": file_path.name,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                    "path": str(file_path)
                })
        
        return {
            "exists": True,
            "path": str(group_dir),
            "file_count": len(files),
            "total_size": total_size,
            "files": files
        }
    
    def generate_unique_filename(self, group_id: str, original_filename: str) -> str:
        """
        生成唯一的文件名，处理文件名冲突
        
        Args:
            group_id: 研究组ID
            original_filename: 原始文件名
            
        Returns:
            str: 唯一的文件名
        """
        try:
            group_dir = self.upload_root / group_id
            file_path = Path(original_filename)
            name_stem = file_path.stem
            suffix = file_path.suffix
            
            logger.info(f"生成唯一文件名: {original_filename} in {group_id}")
            
            # 如果文件不存在，直接返回原始文件名
            target_path = group_dir / original_filename
            if not target_path.exists():
                logger.info(f"文件名 {original_filename} 可直接使用")
                return original_filename
            
            # 文件存在，生成带数字后缀的文件名
            counter = 1
            while True:
                new_filename = f"{name_stem}_{counter}{suffix}"
                target_path = group_dir / new_filename
                
                if not target_path.exists():
                    logger.info(f"生成新文件名: {original_filename} -> {new_filename}")
                    return new_filename
                
                counter += 1
                
                # 防止无限循环
                if counter > 1000:
                    import uuid
                    unique_filename = f"{name_stem}_{uuid.uuid4().hex[:8]}{suffix}"
                    logger.warning(f"文件名冲突过多，使用UUID: {unique_filename}")
                    return unique_filename
                    
        except Exception as e:
            logger.error(f"生成唯一文件名失败: {e}")
            raise
    
    def get_storage_statistics(self) -> Dict:
        """
        获取存储统计信息
        
        Returns:
            Dict: 存储统计
        """
        if not self.upload_root.exists():
            return {
                "total_groups": 0,
                "total_files": 0,
                "total_size": 0,
                "groups": []
            }
        
        groups = []
        total_files = 0
        total_size = 0
        
        for group_dir in self.upload_root.iterdir():
            if group_dir.is_dir():
                group_info = self.get_group_directory_info(group_dir.name)
                groups.append({
                    "group_id": group_dir.name,
                    "file_count": group_info["file_count"],
                    "total_size": group_info["total_size"]
                })
                total_files += group_info["file_count"]
                total_size += group_info["total_size"]
        
        return {
            "total_groups": len(groups),
            "total_files": total_files,
            "total_size": total_size,
            "groups": groups
        }
    
    def cleanup_empty_directories(self) -> List[str]:
        """
        清理空目录
        
        Returns:
            List[str]: 被清理的目录列表
        """
        cleaned_dirs = []
        
        if not self.upload_root.exists():
            return cleaned_dirs
        
        for group_dir in self.upload_root.iterdir():
            if group_dir.is_dir():
                # 检查目录是否为空
                if not any(group_dir.iterdir()):
                    try:
                        group_dir.rmdir()
                        cleaned_dirs.append(str(group_dir))
                        logger.info(f"清理空目录: {group_dir}")
                    except OSError as e:
                        logger.error(f"清理目录失败 {group_dir}: {e}")
        
        return cleaned_dirs
    
    def validate_storage_integrity(self) -> Dict:
        """
        验证存储完整性
        
        Returns:
            Dict: 验证结果
        """
        issues = []
        
        if not self.upload_root.exists():
            issues.append("上传根目录不存在")
            return {"valid": False, "issues": issues}
        
        # 检查权限
        try:
            test_file = self.upload_root / "test_write_permission"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            issues.append(f"上传目录写权限不足: {e}")
        
        # 检查磁盘空间
        try:
            stat = shutil.disk_usage(self.upload_root)
            free_space_mb = stat.free // (1024 * 1024)
            if free_space_mb < 100:  # 少于100MB
                issues.append(f"磁盘空间不足: 仅剩 {free_space_mb}MB")
        except Exception as e:
            issues.append(f"无法检查磁盘空间: {e}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

# 创建全局存储管理器实例
_storage_manager = StorageManager()

def ensure_group_directory(group_id: str) -> str:
    """确保研究组目录存在"""
    return _storage_manager.ensure_group_directory(group_id)

def get_unique_filename(group_id: str, filename: str) -> str:
    """生成唯一的文件名"""
    return _storage_manager.generate_unique_filename(group_id, filename)

def get_storage_stats() -> Dict:
    """获取存储统计信息"""
    return _storage_manager.get_storage_statistics()

def cleanup_storage() -> List[str]:
    """清理存储"""
    return _storage_manager.cleanup_empty_directories()

def validate_storage() -> Dict:
    """验证存储完整性"""
    return _storage_manager.validate_storage_integrity()
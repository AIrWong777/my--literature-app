"""
文献管理模块
负责文献的生命周期管理，包括软删除、恢复等功能
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.models.literature import Literature
from app.models.user import User
from app.models.research_group import ResearchGroup
from app.utils.auth_helper import verify_group_membership

logger = logging.getLogger(__name__)

class LiteratureManager:
    """文献管理器"""
    
    @staticmethod
    def soft_delete_literature(
        literature_id: str, 
        user_id: str, 
        db: Session,
        reason: str = None
    ) -> bool:
        """
        软删除文献（将状态设置为deleted）
        
        Args:
            literature_id: 文献ID
            user_id: 操作用户ID
            db: 数据库会话
            reason: 删除原因
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 查找文献
            literature = db.query(Literature).filter(
                Literature.id == literature_id,
                Literature.status == 'active'
            ).first()
            
            if not literature:
                logger.warning(f"文献不存在或已删除: {literature_id}")
                return False
            
            # 验证权限：只有上传者或研究组成员可以删除
            if literature.uploaded_by != user_id:
                # 检查是否为研究组成员
                if not verify_group_membership(user_id, literature.research_group_id, db):
                    logger.warning(f"用户 {user_id} 无权删除文献 {literature_id}")
                    return False
            
            # 执行软删除
            literature.status = 'deleted'
            literature.deleted_at = datetime.utcnow()
            literature.deleted_by = user_id
            literature.delete_reason = reason
            
            db.commit()
            
            logger.info(f"文献软删除成功: {literature_id} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"文献软删除失败: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def restore_literature(
        literature_id: str, 
        user_id: str, 
        db: Session
    ) -> bool:
        """
        恢复已删除的文献
        
        Args:
            literature_id: 文献ID
            user_id: 操作用户ID
            db: 数据库会话
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            # 查找已删除的文献
            literature = db.query(Literature).filter(
                Literature.id == literature_id,
                Literature.status == 'deleted'
            ).first()
            
            if not literature:
                logger.warning(f"文献不存在或未删除: {literature_id}")
                return False
            
            # 验证权限：只有删除者或研究组成员可以恢复
            if literature.deleted_by != user_id:
                if not verify_group_membership(user_id, literature.research_group_id, db):
                    logger.warning(f"用户 {user_id} 无权恢复文献 {literature_id}")
                    return False
            
            # 执行恢复
            literature.status = 'active'
            literature.deleted_at = None
            literature.deleted_by = None
            literature.delete_reason = None
            literature.restored_at = datetime.utcnow()
            literature.restored_by = user_id
            
            db.commit()
            
            logger.info(f"文献恢复成功: {literature_id} by {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"文献恢复失败: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_deleted_literature(
        group_id: str, 
        user_id: str, 
        db: Session
    ) -> List[Dict]:
        """
        获取研究组的已删除文献列表
        
        Args:
            group_id: 研究组ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            List[Dict]: 已删除文献列表
        """
        try:
            # 验证用户是否为研究组成员
            if not verify_group_membership(user_id, group_id, db):
                logger.warning(f"用户 {user_id} 无权查看研究组 {group_id} 的删除文献")
                return []
            
            # 查询已删除的文献
            deleted_literature = db.query(Literature, User.username).join(
                User, Literature.uploaded_by == User.id
            ).filter(
                Literature.research_group_id == group_id,
                Literature.status == 'deleted'
            ).order_by(Literature.deleted_at.desc()).all()
            
            result = []
            for lit, uploader_name in deleted_literature:
                # 获取删除者信息
                deleter = db.query(User).filter(User.id == lit.deleted_by).first()
                deleter_name = deleter.username if deleter else "未知"
                
                result.append({
                    "id": lit.id,
                    "title": lit.title,
                    "filename": lit.filename,
                    "file_size": lit.file_size,
                    "file_type": lit.file_type,
                    "upload_time": lit.upload_time,
                    "uploader_name": uploader_name,
                    "deleted_at": lit.deleted_at,
                    "deleted_by": deleter_name,
                    "delete_reason": lit.delete_reason
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取删除文献列表失败: {e}")
            return []
    
    @staticmethod
    def get_literature_statistics(group_id: str, db: Session) -> Dict:
        """
        获取研究组文献统计信息
        
        Args:
            group_id: 研究组ID
            db: 数据库会话
            
        Returns:
            Dict: 统计信息
        """
        try:
            # 活跃文献统计
            active_count = db.query(Literature).filter(
                Literature.research_group_id == group_id,
                Literature.status == 'active'
            ).count()
            
            # 已删除文献统计
            deleted_count = db.query(Literature).filter(
                Literature.research_group_id == group_id,
                Literature.status == 'deleted'
            ).count()
            
            # 总文件大小
            from sqlalchemy import func
            total_size = db.query(func.sum(Literature.file_size)).filter(
                Literature.research_group_id == group_id,
                Literature.status == 'active'
            ).scalar() or 0
            
            # 文件类型分布
            type_distribution = db.query(
                Literature.file_type,
                func.count(Literature.id)
            ).filter(
                Literature.research_group_id == group_id,
                Literature.status == 'active'
            ).group_by(Literature.file_type).all()
            
            return {
                "active_count": active_count,
                "deleted_count": deleted_count,
                "total_count": active_count + deleted_count,
                "total_size": total_size,
                "type_distribution": dict(type_distribution)
            }
            
        except Exception as e:
            logger.error(f"获取文献统计失败: {e}")
            return {
                "active_count": 0,
                "deleted_count": 0,
                "total_count": 0,
                "total_size": 0,
                "type_distribution": {}
            }

# 创建全局文献管理器实例
literature_manager = LiteratureManager()

def soft_delete_literature(literature_id: str, user_id: str, db: Session, reason: str = None) -> bool:
    """软删除文献的便捷函数"""
    return literature_manager.soft_delete_literature(literature_id, user_id, db, reason)

def restore_literature(literature_id: str, user_id: str, db: Session) -> bool:
    """恢复文献的便捷函数"""
    return literature_manager.restore_literature(literature_id, user_id, db)

def get_deleted_literature(group_id: str, user_id: str, db: Session) -> List[Dict]:
    """获取删除文献列表的便捷函数"""
    return literature_manager.get_deleted_literature(group_id, user_id, db)

def get_literature_stats(group_id: str, db: Session) -> Dict:
    """获取文献统计的便捷函数"""
    return literature_manager.get_literature_statistics(group_id, db)
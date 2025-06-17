"""
异步文献处理模块
用于异步处理文献的文本提取、分块和向量化
"""

import threading
import time
import logging
from typing import Optional, Dict, Callable
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.literature import Literature
from app.utils.text_extractor import extract_text_from_file, extract_metadata_from_file
from app.utils.text_processor import split_text_into_chunks, prepare_chunks_for_embedding
from app.utils.embedding_service import embedding_service
from app.utils.vector_store import vector_store
from app.utils.error_handler import log_error, log_success

# 配置日志
logger = logging.getLogger(__name__)

class AsyncProcessor:
    """异步文献处理器"""
    
    def __init__(self):
        self.processing_tasks = {}  # 存储正在处理的任务
        self.task_results = {}     # 存储任务结果
    
    def process_literature_async(
        self, 
        literature_id: str, 
        callback: Optional[Callable] = None
    ) -> str:
        """
        异步处理文献
        
        Args:
            literature_id: 文献ID
            callback: 完成后的回调函数
            
        Returns:
            str: 任务ID
        """
        task_id = f"process_{literature_id}_{int(time.time())}"
        
        # 检查是否已在处理中
        if literature_id in self.processing_tasks:
            logger.warning(f"文献 {literature_id} 已在处理中")
            return self.processing_tasks[literature_id]
        
        # 创建处理线程
        thread = threading.Thread(
            target=self._process_literature_worker,
            args=(task_id, literature_id, callback),
            daemon=True
        )
        
        # 记录任务
        self.processing_tasks[literature_id] = task_id
        self.task_results[task_id] = {
            "status": "processing",
            "literature_id": literature_id,
            "start_time": time.time(),
            "progress": 0,
            "message": "开始处理文献"
        }
        
        # 启动线程
        thread.start()
        logger.info(f"启动异步处理任务: {task_id} for 文献 {literature_id}")
        
        return task_id
    
    def _process_literature_worker(
        self, 
        task_id: str, 
        literature_id: str, 
        callback: Optional[Callable]
    ):
        """
        文献处理工作线程
        
        Args:
            task_id: 任务ID
            literature_id: 文献ID
            callback: 回调函数
        """
        try:
            # 更新进度
            self._update_task_progress(task_id, 10, "获取文献信息")
            
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 获取文献信息
                literature = db.query(Literature).filter(Literature.id == literature_id).first()
                if not literature:
                    raise Exception(f"文献 {literature_id} 不存在")
                
                if literature.status != 'active':
                    raise Exception(f"文献 {literature_id} 状态异常: {literature.status}")
                
                # 更新进度
                self._update_task_progress(task_id, 20, "提取文本内容")
                
                # 构建完整文件路径
                from app.config import settings
                import os
                full_file_path = os.path.join(settings.UPLOAD_ROOT_DIR, literature.file_path)
                
                # 提取文本
                extracted_text = extract_text_from_file(full_file_path)
                if not extracted_text or not extracted_text.strip():
                    raise Exception("文本提取失败或文本为空")
                
                # 更新进度
                self._update_task_progress(task_id, 40, "分割文本块")
                
                # 分割文本
                chunks = split_text_into_chunks(extracted_text)
                if not chunks:
                    raise Exception("文本分块失败")
                
                # 准备文本块数据
                chunks_data = prepare_chunks_for_embedding(
                    chunks, 
                    literature_id, 
                    literature.research_group_id,
                    literature.title
                )
                
                # 更新进度
                self._update_task_progress(task_id, 60, f"生成向量 ({len(chunks)} 个文本块)")
                
                # 生成embeddings
                embeddings, failed_texts = embedding_service.batch_generate_embeddings(
                    [chunk["text"] for chunk in chunks_data]
                )
                
                if not embeddings:
                    raise Exception("向量生成失败")
                
                if len(embeddings) != len(chunks_data):
                    logger.warning(f"部分文本块向量生成失败: {len(failed_texts)} 个失败")
                    # 只保留成功的chunks
                    chunks_data = chunks_data[:len(embeddings)]
                
                # 更新进度
                self._update_task_progress(task_id, 80, "存储向量数据")
                
                # 先删除旧的向量（如果存在）
                vector_store.delete_document_chunks(literature_id, literature.research_group_id)
                
                # 存储新的向量
                success = vector_store.store_document_chunks(
                    chunks_data, 
                    embeddings, 
                    literature_id, 
                    literature.research_group_id
                )
                
                if not success:
                    raise Exception("向量存储失败")
                
                # 更新文献状态（可选：添加处理状态字段）
                # literature.processed_at = datetime.utcnow()
                # db.commit()
                
                # 完成处理
                self._complete_task(
                    task_id, 
                    True, 
                    f"成功处理 {len(chunks_data)} 个文本块",
                    {
                        "chunks_count": len(chunks_data),
                        "embeddings_count": len(embeddings),
                        "failed_count": len(failed_texts),
                        "text_length": len(extracted_text)
                    }
                )
                
                # 记录成功日志
                log_success("literature_processing", literature_id, {
                    "task_id": task_id,
                    "chunks_count": len(chunks_data),
                    "text_length": len(extracted_text)
                })
                
                # 调用回调函数
                if callback:
                    try:
                        callback(task_id, True, "处理成功")
                    except Exception as e:
                        logger.error(f"回调函数执行失败: {e}")
                
            finally:
                db.close()
                
        except Exception as e:
            error_msg = f"文献处理失败: {str(e)}"
            logger.error(error_msg)
            
            # 记录错误
            self._complete_task(task_id, False, error_msg)
            
            # 记录错误日志
            log_error("literature_processing", e, extra_info={
                "task_id": task_id,
                "literature_id": literature_id
            })
            
            # 调用回调函数
            if callback:
                try:
                    callback(task_id, False, error_msg)
                except Exception as cb_e:
                    logger.error(f"回调函数执行失败: {cb_e}")
        
        finally:
            # 清理任务记录
            if literature_id in self.processing_tasks:
                del self.processing_tasks[literature_id]
    
    def _update_task_progress(self, task_id: str, progress: int, message: str):
        """更新任务进度"""
        if task_id in self.task_results:
            self.task_results[task_id].update({
                "progress": progress,
                "message": message,
                "updated_at": time.time()
            })
            logger.info(f"任务 {task_id} 进度: {progress}% - {message}")
    
    def _complete_task(self, task_id: str, success: bool, message: str, data: Dict = None):
        """完成任务"""
        if task_id in self.task_results:
            self.task_results[task_id].update({
                "status": "completed" if success else "failed",
                "progress": 100 if success else -1,
                "message": message,
                "completed_at": time.time(),
                "success": success,
                "data": data or {}
            })
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict]: 任务状态信息
        """
        return self.task_results.get(task_id)
    
    def get_literature_processing_status(self, literature_id: str) -> Optional[Dict]:
        """
        获取文献处理状态
        
        Args:
            literature_id: 文献ID
            
        Returns:
            Optional[Dict]: 处理状态信息
        """
        task_id = self.processing_tasks.get(literature_id)
        if task_id:
            return self.get_task_status(task_id)
        return None
    
    def is_literature_processing(self, literature_id: str) -> bool:
        """
        检查文献是否正在处理中
        
        Args:
            literature_id: 文献ID
            
        Returns:
            bool: 是否正在处理
        """
        return literature_id in self.processing_tasks
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务（注意：已启动的线程无法强制停止）
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功标记为取消
        """
        if task_id in self.task_results:
            task_info = self.task_results[task_id]
            if task_info["status"] == "processing":
                task_info.update({
                    "status": "cancelled",
                    "message": "任务已取消",
                    "cancelled_at": time.time()
                })
                logger.info(f"任务 {task_id} 已标记为取消")
                return True
        return False
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """
        清理旧的任务记录
        
        Args:
            max_age_hours: 最大保留时间（小时）
        """
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        tasks_to_remove = []
        for task_id, task_info in self.task_results.items():
            task_age = current_time - task_info.get("start_time", current_time)
            if task_age > max_age_seconds and task_info["status"] != "processing":
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.task_results[task_id]
            logger.info(f"清理旧任务记录: {task_id}")
        
        if tasks_to_remove:
            logger.info(f"清理了 {len(tasks_to_remove)} 个旧任务记录")
    
    def get_all_tasks_status(self) -> Dict:
        """
        获取所有任务状态概览
        
        Returns:
            Dict: 任务状态概览
        """
        processing_count = sum(1 for task in self.task_results.values() if task["status"] == "processing")
        completed_count = sum(1 for task in self.task_results.values() if task["status"] == "completed")
        failed_count = sum(1 for task in self.task_results.values() if task["status"] == "failed")
        
        return {
            "total_tasks": len(self.task_results),
            "processing": processing_count,
            "completed": completed_count,
            "failed": failed_count,
            "active_literature": list(self.processing_tasks.keys())
        }

# 创建全局异步处理器实例
async_processor = AsyncProcessor()

def process_literature_background(literature_id: str) -> str:
    """
    便捷函数：在后台处理文献
    
    Args:
        literature_id: 文献ID
        
    Returns:
        str: 任务ID
    """
    return async_processor.process_literature_async(literature_id)

def get_processing_status(literature_id: str) -> Optional[Dict]:
    """
    便捷函数：获取文献处理状态
    
    Args:
        literature_id: 文献ID
        
    Returns:
        Optional[Dict]: 处理状态
    """
    return async_processor.get_literature_processing_status(literature_id) 
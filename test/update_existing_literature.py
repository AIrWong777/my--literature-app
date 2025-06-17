#!/usr/bin/env python3
"""
数据库更新脚本

为现有文献生成文本块和embedding，批量处理已上传的文献
"""
import sys
import os
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.literature import Literature
from app.models.research_group import ResearchGroup
from app.utils.async_processor import AsyncProcessor
from app.utils.vector_store import vector_store
from app.utils.embedding_service import embedding_service
from app.utils.text_extractor import extract_text_from_file
from app.utils.text_processor import split_text_into_chunks
from app.utils.error_handler import log_error, log_success

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('update_literature.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LiteratureUpdater:
    """文献更新器"""
    
    def __init__(self):
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.total_count = 0
        self.processor = AsyncProcessor()
        
    def get_literature_list(self, db: Session, group_id: Optional[str] = None, 
                           limit: Optional[int] = None) -> List[Literature]:
        """获取需要处理的文献列表"""
        try:
            query = db.query(Literature).filter(Literature.status == "active")
            
            if group_id:
                query = query.filter(Literature.group_id == group_id)
            
            if limit:
                query = query.limit(limit)
            
            literature_list = query.all()
            logger.info(f"找到 {len(literature_list)} 个需要处理的文献")
            return literature_list
            
        except Exception as e:
            logger.error(f"获取文献列表失败: {e}")
            return []
    
    def check_literature_processed(self, literature_id: str, group_id: str) -> bool:
        """检查文献是否已经处理过"""
        try:
            # 检查向量数据库中是否已有该文献的数据
            chunks = vector_store.get_literature_chunks(literature_id, group_id)
            return len(chunks) > 0
        except:
            return False
    
    async def process_single_literature(self, literature: Literature, 
                                      force_update: bool = False) -> bool:
        """处理单个文献"""
        literature_id = literature.id
        group_id = literature.group_id
        file_path = literature.file_path
        
        try:
            logger.info(f"开始处理文献: {literature.title} (ID: {literature_id})")
            
            # 检查是否已处理
            if not force_update and self.check_literature_processed(literature_id, group_id):
                logger.info(f"文献 {literature_id} 已处理过，跳过")
                self.skipped_count += 1
                return True
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文献文件不存在: {file_path}")
                self.error_count += 1
                return False
            
            # 1. 提取文本
            logger.info(f"提取文本: {file_path}")
            text_content = extract_text_from_file(file_path)
            
            if not text_content or len(text_content.strip()) < 100:
                logger.warning(f"文献 {literature_id} 文本内容太少或为空，跳过")
                self.skipped_count += 1
                return True
            
            # 2. 文本分块
            logger.info(f"文本分块: {len(text_content)} 字符")
            chunks = split_text_into_chunks(
                text_content, 
                chunk_size=1000, 
                overlap=200
            )
            
            if not chunks:
                logger.warning(f"文献 {literature_id} 分块失败，跳过")
                self.skipped_count += 1
                return True
            
            logger.info(f"生成了 {len(chunks)} 个文本块")
            
            # 3. 生成embeddings
            logger.info("生成embeddings...")
            embeddings = []
            failed_chunks = []
            
            for i, chunk in enumerate(chunks):
                try:
                    embedding = embedding_service.generate_embedding(chunk)
                    if embedding:
                        embeddings.append(embedding)
                    else:
                        failed_chunks.append(i)
                        logger.warning(f"文档块 {i} embedding生成失败")
                except Exception as e:
                    failed_chunks.append(i)
                    logger.warning(f"文档块 {i} embedding生成异常: {e}")
                
                # 添加小延迟避免API限制
                if i % 10 == 0:
                    await asyncio.sleep(0.1)
            
            if not embeddings:
                logger.error(f"文献 {literature_id} 所有embedding生成都失败")
                self.error_count += 1
                return False
            
            # 移除失败的块
            if failed_chunks:
                chunks = [chunk for i, chunk in enumerate(chunks) if i not in failed_chunks]
                logger.info(f"移除 {len(failed_chunks)} 个失败的块，剩余 {len(chunks)} 个")
            
            # 4. 存储到向量数据库
            logger.info("存储到向量数据库...")
            
            # 如果强制更新，先删除现有数据
            if force_update:
                vector_store.delete_literature_chunks(literature_id, group_id)
                logger.info(f"已删除文献 {literature_id} 的现有向量数据")
            
            # 准备文档块数据
            chunk_data_list = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_data = {
                    "text": chunk,
                    "literature_id": literature_id,
                    "group_id": group_id,
                    "chunk_index": i,
                    "metadata": {
                        "source": literature.title,
                        "file_path": file_path,
                        "chunk_length": len(chunk),
                        "processed_at": datetime.now().isoformat()
                    }
                }
                chunk_data_list.append(chunk_data)
            
            # 批量存储
            success = await vector_store.store_document_chunks_async(
                chunks=chunk_data_list,
                embeddings=embeddings,
                literature_id=literature_id,
                group_id=group_id
            )
            
            if success:
                logger.info(f"✅ 文献 {literature_id} 处理完成: {len(chunks)} 个块")
                self.success_count += 1
                
                # 记录成功日志
                log_success("literature_processing", literature_id, {
                    "title": literature.title,
                    "chunks_count": len(chunks),
                    "embeddings_count": len(embeddings),
                    "text_length": len(text_content)
                })
                return True
            else:
                logger.error(f"❌ 文献 {literature_id} 向量存储失败")
                self.error_count += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ 处理文献 {literature_id} 时发生异常: {e}")
            log_error("literature_processing", e, extra_info={
                "literature_id": literature_id,
                "title": literature.title,
                "file_path": file_path
            })
            self.error_count += 1
            return False
        finally:
            self.processed_count += 1
    
    async def update_literature_batch(self, db: Session, group_id: Optional[str] = None,
                                    limit: Optional[int] = None, 
                                    force_update: bool = False,
                                    max_concurrent: int = 3) -> Dict:
        """批量更新文献"""
        start_time = datetime.now()
        logger.info("🚀 开始批量更新文献...")
        
        # 获取文献列表
        literature_list = self.get_literature_list(db, group_id, limit)
        self.total_count = len(literature_list)
        
        if self.total_count == 0:
            logger.warning("没有找到需要处理的文献")
            return self._get_summary(start_time)
        
        logger.info(f"准备处理 {self.total_count} 个文献 (最大并发: {max_concurrent})")
        
        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(lit):
            async with semaphore:
                return await self.process_single_literature(lit, force_update)
        
        # 批量处理
        tasks = [process_with_semaphore(lit) for lit in literature_list]
        
        # 显示进度
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                await task
                progress = (i + 1) / self.total_count * 100
                logger.info(f"进度: {i+1}/{self.total_count} ({progress:.1f}%)")
            except Exception as e:
                logger.error(f"任务执行异常: {e}")
        
        return self._get_summary(start_time)
    
    def _get_summary(self, start_time: datetime) -> Dict:
        """获取处理总结"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_literature": self.total_count,
            "processed": self.processed_count,
            "success": self.success_count,
            "errors": self.error_count,
            "skipped": self.skipped_count,
            "success_rate": (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
        }
        
        logger.info("=" * 60)
        logger.info("📊 处理总结")
        logger.info("=" * 60)
        logger.info(f"总文献数: {summary['total_literature']}")
        logger.info(f"已处理: {summary['processed']}")
        logger.info(f"成功: {summary['success']}")
        logger.info(f"失败: {summary['errors']}")
        logger.info(f"跳过: {summary['skipped']}")
        logger.info(f"成功率: {summary['success_rate']:.1f}%")
        logger.info(f"总耗时: {summary['duration_seconds']:.1f}秒")
        
        return summary
    
    async def verify_processing_results(self, db: Session, group_id: Optional[str] = None) -> Dict:
        """验证处理结果"""
        logger.info("🔍 验证处理结果...")
        
        literature_list = self.get_literature_list(db, group_id)
        verification_results = {
            "total_literature": len(literature_list),
            "processed_literature": 0,
            "unprocessed_literature": 0,
            "vector_stats": {},
            "details": []
        }
        
        for literature in literature_list:
            try:
                # 检查向量数据库中的数据
                chunks = vector_store.get_literature_chunks(
                    literature.id, literature.group_id
                )
                
                is_processed = len(chunks) > 0
                if is_processed:
                    verification_results["processed_literature"] += 1
                else:
                    verification_results["unprocessed_literature"] += 1
                
                verification_results["details"].append({
                    "literature_id": literature.id,
                    "title": literature.title,
                    "is_processed": is_processed,
                    "chunks_count": len(chunks)
                })
                
            except Exception as e:
                logger.error(f"验证文献 {literature.id} 时出错: {e}")
                verification_results["details"].append({
                    "literature_id": literature.id,
                    "title": literature.title,
                    "is_processed": False,
                    "error": str(e)
                })
        
        # 获取向量数据库统计
        try:
            verification_results["vector_stats"] = vector_store.get_stats()
        except Exception as e:
            logger.error(f"获取向量数据库统计失败: {e}")
        
        logger.info(f"验证完成: {verification_results['processed_literature']}/{verification_results['total_literature']} 个文献已处理")
        
        return verification_results

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="更新现有文献的向量数据")
    parser.add_argument("--group-id", help="指定研究组ID (可选)")
    parser.add_argument("--limit", type=int, help="限制处理数量 (可选)")
    parser.add_argument("--force", action="store_true", help="强制更新已处理的文献")
    parser.add_argument("--verify-only", action="store_true", help="只验证不处理")
    parser.add_argument("--max-concurrent", type=int, default=3, help="最大并发数")
    
    args = parser.parse_args()
    
    # 初始化数据库连接
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        updater = LiteratureUpdater()
        
        if args.verify_only:
            # 只验证
            verification_results = await updater.verify_processing_results(db, args.group_id)
            
            # 保存验证结果
            import json
            with open('verification_results.json', 'w', encoding='utf-8') as f:
                json.dump(verification_results, f, ensure_ascii=False, indent=2)
            
            logger.info("验证结果已保存到: verification_results.json")
        else:
            # 执行更新
            summary = await updater.update_literature_batch(
                db=db,
                group_id=args.group_id,
                limit=args.limit,
                force_update=args.force,
                max_concurrent=args.max_concurrent
            )
            
            # 保存处理结果
            import json
            with open('update_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info("处理结果已保存到: update_summary.json")
            
            # 如果有错误，退出时返回错误码
            if summary['errors'] > 0:
                logger.warning("部分文献处理失败，请查看日志")
                sys.exit(1)
            else:
                logger.info("🎉 所有文献处理完成！")
                sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("用户中断了处理过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行过程中发生异常: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 
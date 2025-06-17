#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库迁移脚本：修改literature表结构以支持私人文献
"""

import sys
import logging
from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_database():
    """修改数据库表结构"""
    try:
        logger.info("开始数据库迁移...")
        
        # 创建数据库引擎
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                # SQLite特定的查询表结构方法
                result = connection.execute(text("PRAGMA table_info(literature)"))
                columns = result.fetchall()
                
                # 查找research_group_id列
                research_group_col = None
                for col in columns:
                    if col[1] == 'research_group_id':  # col[1]是列名
                        research_group_col = col
                        break
                
                if research_group_col:
                    logger.info(f"找到research_group_id列: {research_group_col}")
                    notnull = research_group_col[3]  # col[3]是notnull标志
                    
                    if notnull == 1:  # 1表示NOT NULL
                        logger.info("research_group_id字段当前为NOT NULL，需要修改")
                        
                        # SQLite不支持直接ALTER COLUMN，需要重建表
                        logger.info("开始重建表以修改字段约束...")
                        
                        # 1. 创建新表
                        connection.execute(text("""
                            CREATE TABLE literature_new (
                                id TEXT PRIMARY KEY,
                                title TEXT NOT NULL,
                                filename TEXT NOT NULL,
                                file_path TEXT NOT NULL,
                                file_size INTEGER NOT NULL,
                                file_type TEXT NOT NULL,
                                upload_time DATETIME NOT NULL,
                                uploaded_by TEXT NOT NULL,
                                research_group_id TEXT,  -- 允许为NULL
                                status TEXT NOT NULL DEFAULT 'active',
                                deleted_at DATETIME,
                                deleted_by TEXT,
                                delete_reason TEXT,
                                restored_at DATETIME,
                                restored_by TEXT,
                                FOREIGN KEY (uploaded_by) REFERENCES users(id),
                                FOREIGN KEY (research_group_id) REFERENCES research_groups(id),
                                FOREIGN KEY (deleted_by) REFERENCES users(id),
                                FOREIGN KEY (restored_by) REFERENCES users(id)
                            )
                        """))
                        
                        # 2. 复制数据
                        connection.execute(text("""
                            INSERT INTO literature_new (
                                id, title, filename, file_path, file_size, file_type,
                                upload_time, uploaded_by, research_group_id, status,
                                deleted_at, deleted_by, delete_reason, restored_at, restored_by
                            )
                            SELECT 
                                id, title, filename, file_path, file_size, file_type,
                                upload_time, uploaded_by, research_group_id, status,
                                deleted_at, deleted_by, delete_reason, restored_at, restored_by
                            FROM literature
                        """))
                        
                        # 3. 删除旧表
                        connection.execute(text("DROP TABLE literature"))
                        
                        # 4. 重命名新表
                        connection.execute(text("ALTER TABLE literature_new RENAME TO literature"))
                        
                        logger.info("成功重建表，research_group_id字段现在允许为NULL")
                    else:
                        logger.info("research_group_id字段已经允许NULL，无需修改")
                else:
                    logger.error("未找到research_group_id字段")
                    return False
                
                # 提交事务
                trans.commit()
                logger.info("数据库迁移完成")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"迁移过程中出错，已回滚: {e}")
                return False
                
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        logger.info("✅ 数据库迁移成功完成")
        sys.exit(0)
    else:
        logger.error("❌ 数据库迁移失败")
        sys.exit(1) 
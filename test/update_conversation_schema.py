#!/usr/bin/env python3
"""
修改对话会话表结构，支持私人文献的AI对话

更新时间：2025年5月30日
更新内容：将qa_sessions表的group_id字段修改为允许NULL，以支持私人文献的AI对话功能
"""
import sqlite3
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_database(db_path: str) -> str:
    """备份数据库"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        # 简单的文件复制作为备份
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"备份数据库失败: {e}")
        raise

def update_qa_sessions_table(cursor):
    """更新qa_sessions表结构"""
    try:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qa_sessions'")
        if not cursor.fetchone():
            logger.info("qa_sessions表不存在，跳过修改")
            return
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(qa_sessions)")
        columns = cursor.fetchall()
        logger.info(f"当前qa_sessions表结构: {columns}")
        
        # 检查group_id字段是否存在且不允许为空
        group_id_column = None
        for col in columns:
            if col[1] == 'group_id':  # col[1]是列名
                group_id_column = col
                break
        
        if not group_id_column:
            logger.info("group_id字段不存在，跳过修改")
            return
        
        if group_id_column[3] == 0:  # col[3]是notnull标志，0表示允许null，1表示不允许null
            logger.info("group_id字段已经允许为空，无需修改")
            return
            
        logger.info("开始修改qa_sessions表结构...")
        
        # SQLite不支持直接修改列的NULL约束，需要重建表
        
        # 1. 创建新表
        create_new_table_sql = """
        CREATE TABLE qa_sessions_new (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            group_id TEXT,  -- 修改为允许NULL
            literature_id TEXT NOT NULL,
            session_title TEXT,
            start_time DATETIME NOT NULL,
            last_activity DATETIME NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            turn_count INTEGER NOT NULL DEFAULT 0,
            total_questions INTEGER NOT NULL DEFAULT 0,
            total_answers INTEGER NOT NULL DEFAULT 0,
            avg_confidence REAL NOT NULL DEFAULT 0.0,
            session_metadata TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (group_id) REFERENCES research_groups (id),
            FOREIGN KEY (literature_id) REFERENCES literature (id)
        )
        """
        cursor.execute(create_new_table_sql)
        
        # 2. 复制数据
        cursor.execute("""
        INSERT INTO qa_sessions_new 
        SELECT * FROM qa_sessions
        """)
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE qa_sessions")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE qa_sessions_new RENAME TO qa_sessions")
        
        logger.info("qa_sessions表结构修改完成")
        
    except Exception as e:
        logger.error(f"修改qa_sessions表失败: {e}")
        raise

def main():
    """主函数"""
    # 数据库文件路径
    db_path = "literature_system.db"
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return
    
    try:
        # 备份数据库
        backup_path = backup_database(db_path)
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # 更新qa_sessions表
            update_qa_sessions_table(cursor)
            
            # 提交事务
            conn.commit()
            logger.info("数据库结构更新成功！")
            
        except Exception as e:
            # 回滚事务
            conn.rollback()
            logger.error(f"更新失败，已回滚: {e}")
            raise
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"数据库更新失败: {e}")
        print(f"如果出现问题，可以从备份恢复: {backup_path}")

if __name__ == "__main__":
    main() 
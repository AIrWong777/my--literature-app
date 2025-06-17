#!/usr/bin/env python3
"""
修复qa_sessions表的group_id字段，使其允许为空
"""
import sqlite3
import os
import shutil
from datetime import datetime

def main():
    db_path = "literature_system.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    # 备份数据库
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"数据库已备份到: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查qa_sessions表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qa_sessions'")
        if not cursor.fetchone():
            print("qa_sessions表不存在，无需修改")
            return
        
        # 删除qa_sessions表（如果存在）
        print("删除现有的qa_sessions表...")
        cursor.execute("DROP TABLE IF EXISTS qa_sessions")
        
        # 重新创建qa_sessions表，group_id允许为空
        print("重新创建qa_sessions表...")
        create_table_sql = """
        CREATE TABLE qa_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            group_id TEXT NULL,  -- 允许为空
            literature_id TEXT NOT NULL,
            session_title TEXT,
            start_time DATETIME NOT NULL,
            last_activity DATETIME NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            turn_count INTEGER NOT NULL DEFAULT 0,
            total_questions INTEGER NOT NULL DEFAULT 0,
            total_answers INTEGER NOT NULL DEFAULT 0,
            avg_confidence REAL NOT NULL DEFAULT 0.0,
            session_metadata TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (group_id) REFERENCES research_groups (id),
            FOREIGN KEY (literature_id) REFERENCES literature (id)
        )
        """
        cursor.execute(create_table_sql)
        
        # 同样处理conversation_turns表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_turns'")
        if not cursor.fetchone():
            print("创建conversation_turns表...")
            create_turns_table_sql = """
            CREATE TABLE conversation_turns (
                turn_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                question TEXT NOT NULL,
                question_metadata TEXT,
                answer TEXT,
                answer_metadata TEXT,
                confidence REAL DEFAULT 0.0,
                quality_scores TEXT,
                chunks_used INTEGER DEFAULT 0,
                retrieval_metadata TEXT,
                processing_time REAL DEFAULT 0.0,
                prompt_tokens INTEGER DEFAULT 0,
                user_rating INTEGER,
                user_feedback TEXT,
                is_successful INTEGER DEFAULT 1,
                error_type TEXT,
                FOREIGN KEY (session_id) REFERENCES qa_sessions (session_id)
            )
            """
            cursor.execute(create_turns_table_sql)
        
        conn.commit()
        print("数据库表结构修复完成！")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(qa_sessions)")
        columns = cursor.fetchall()
        print("\n修复后的qa_sessions表结构:")
        for col in columns:
            print(f"  {col[1]}: {col[2]} {'NOT NULL' if col[3] else 'NULL'}")
        
    except Exception as e:
        print(f"修复失败: {e}")
        # 恢复备份
        shutil.copy2(backup_path, db_path)
        print(f"已从备份恢复数据库")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 
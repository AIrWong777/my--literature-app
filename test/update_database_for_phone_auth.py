"""
数据库更新脚本：为用户表添加手机号登录支持

这个脚本会：
1. 为现有用户表添加 phone_number 和 refresh_token 字段
2. 为现有用户生成默认手机号（测试用途）
3. 更新表结构以支持新的认证系统
"""

import sqlite3
import uuid
from app.database import SQLALCHEMY_DATABASE_URL

def update_database():
    # 连接到SQLite数据库
    db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有phone_number字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'phone_number' not in columns:
            print("添加 phone_number 字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
            
        if 'refresh_token' not in columns:
            print("添加 refresh_token 字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN refresh_token TEXT")
        
        # 为现有用户生成默认手机号（如果没有的话）
        cursor.execute("SELECT id, username FROM users WHERE phone_number IS NULL OR phone_number = ''")
        users_without_phone = cursor.fetchall()
        
        for user_id, username in users_without_phone:
            # 生成一个基于用户名的测试手机号（11位数字）
            test_phone = f"1{hash(username) % 10000000000:010d}"
            cursor.execute("UPDATE users SET phone_number = ? WHERE id = ?", (test_phone, user_id))
            print(f"为用户 {username} 生成测试手机号: {test_phone}")
        
        # 创建唯一索引
        try:
            cursor.execute("CREATE UNIQUE INDEX idx_users_phone_number ON users(phone_number)")
            print("创建手机号唯一索引...")
        except sqlite3.Error as e:
            if "already exists" not in str(e):
                print(f"创建索引时出错: {e}")
        
        # 更新email字段为可空（如果需要）
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()
        email_column = next((col for col in columns_info if col[1] == 'email'), None)
        
        if email_column and email_column[3] == 1:  # NOT NULL
            print("将email字段设置为可空...")
            # SQLite不支持直接修改列约束，需要重建表
            cursor.execute("""
                CREATE TABLE users_new (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    phone_number TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    refresh_token TEXT
                )
            """)
            
            cursor.execute("""
                INSERT INTO users_new (id, username, email, phone_number, password_hash, refresh_token)
                SELECT id, username, email, phone_number, password_hash, refresh_token FROM users
            """)
            
            cursor.execute("DROP TABLE users")
            cursor.execute("ALTER TABLE users_new RENAME TO users")
            print("表结构更新完成")
        
        conn.commit()
        print("数据库更新成功！")
        
    except Exception as e:
        conn.rollback()
        print(f"数据库更新失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_database() 
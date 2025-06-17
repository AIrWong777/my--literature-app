#!/usr/bin/env python3
"""
简单的测试用户创建脚本
"""

import sys
import os
import sqlite3
from passlib.context import CryptContext
import uuid

# 密码哈希配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_user():
    """创建测试用户"""
    print("🔧 创建测试用户...")
    
    # 数据库路径
    db_path = "literature_system.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查用户是否已存在
        cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser",))
        if cursor.fetchone():
            print("ℹ️  测试用户已存在")
            conn.close()
            return True
        
        # 创建测试用户
        user_id = str(uuid.uuid4())
        username = "testuser"
        email = "test@example.com"
        password = "password123"
        password_hash = pwd_context.hash(password)
        
        cursor.execute("""
            INSERT INTO users (id, username, email, password_hash)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, email, password_hash))
        
        conn.commit()
        conn.close()
        
        print("✅ 测试用户创建成功!")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"   邮箱: {email}")
        print(f"   ID: {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return False

def main():
    """主函数"""
    print("👤 测试用户创建工具")
    print("="*30)
    
    if create_test_user():
        print("\n🎉 测试用户准备完成!")
        print("现在可以使用以下凭据进行API测试:")
        print("  用户名: testuser")
        print("  密码: password123")
    else:
        print("\n❌ 测试用户创建失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
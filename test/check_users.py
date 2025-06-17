#!/usr/bin/env python3
"""
检查数据库中的用户信息
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.user import User

def check_users():
    """检查数据库中的用户"""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 查询所有用户
        users = db.query(User).all()
        
        print(f"数据库中共有 {len(users)} 个用户:")
        print("-" * 50)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"手机号: {user.phone_number}")
            print(f"邮箱: {user.email}")
            print(f"密码哈希: {user.password_hash[:20]}...")
            print("-" * 50)
        
        # 特别检查testuser
        testuser = db.query(User).filter(User.username == "testuser").first()
        if testuser:
            print(f"\n主要测试用户 (testuser):")
            print(f"  ID: {testuser.id}")
            print(f"  用户名: {testuser.username}")
            print(f"  手机号: {testuser.phone_number}")
            print(f"  密码哈希: {testuser.password_hash[:20]}...")
        else:
            print("\n❌ 主要测试用户 (testuser) 不存在")
            
    except Exception as e:
        print(f"检查用户失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users() 
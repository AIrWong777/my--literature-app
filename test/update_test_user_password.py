#!/usr/bin/env python3
"""
更新测试用户密码的脚本
"""

import sqlite3
from passlib.context import CryptContext

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def update_user_password():
    """更新测试用户密码"""
    print("🔐 更新测试用户密码...")
    
    # 生成新的密码哈希
    new_password = "testpass123"
    password_hash = pwd_context.hash(new_password)
    
    print(f"新密码: {new_password}")
    print(f"密码哈希: {password_hash[:50]}...")
    
    try:
        # 连接数据库
        conn = sqlite3.connect("literature_system.db")
        cursor = conn.cursor()
        
        # 更新密码
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (password_hash, "testuser")
        )
        
        if cursor.rowcount > 0:
            print(f"✅ 成功更新 {cursor.rowcount} 个用户的密码")
        else:
            print("❌ 没有找到用户或更新失败")
        
        conn.commit()
        conn.close()
        
        # 验证更新
        print("\n🔍 验证密码更新...")
        conn = sqlite3.connect("literature_system.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, password_hash FROM users WHERE username = ?", ("testuser",))
        result = cursor.fetchone()
        
        if result:
            username, stored_hash = result
            is_valid = pwd_context.verify(new_password, stored_hash)
            print(f"用户: {username}")
            print(f"密码验证: {'✅ 成功' if is_valid else '❌ 失败'}")
        else:
            print("❌ 用户不存在")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 更新密码失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 测试用户密码更新工具")
    print("="*40)
    
    if update_user_password():
        print("\n🎉 密码更新完成!")
    else:
        print("\n❌ 密码更新失败")

if __name__ == "__main__":
    main()
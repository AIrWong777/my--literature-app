#!/usr/bin/env python3
"""
测试密码验证
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.user import User
from app.auth import verify_password, get_password_hash

def test_password():
    """测试密码验证"""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 查找testuser
        testuser = db.query(User).filter(User.username == "testuser").first()
        if not testuser:
            print("❌ testuser不存在")
            return
        
        print(f"用户: {testuser.username}")
        print(f"手机号: {testuser.phone_number}")
        print(f"密码哈希: {testuser.password_hash}")
        
        # 测试密码
        test_passwords = ["testpass123", "testpass", "password123"]
        
        for password in test_passwords:
            is_valid = verify_password(password, testuser.password_hash)
            print(f"密码 '{password}': {'✅ 正确' if is_valid else '❌ 错误'}")
        
        # 如果都不对，重新设置密码
        all_wrong = all(not verify_password(pwd, testuser.password_hash) for pwd in test_passwords)
        if all_wrong:
            print("\n所有测试密码都不正确，重新设置为 'testpass123'")
            new_hash = get_password_hash("testpass123")
            testuser.password_hash = new_hash
            db.commit()
            print("✅ 密码已重新设置")
            
            # 验证新密码
            is_valid = verify_password("testpass123", testuser.password_hash)
            print(f"新密码验证: {'✅ 正确' if is_valid else '❌ 错误'}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_password() 
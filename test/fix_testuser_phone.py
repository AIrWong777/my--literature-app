#!/usr/bin/env python3
"""
修复testuser的手机号，使其与测试脚本一致
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.user import User

def fix_testuser_phone():
    """修复testuser的手机号"""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 查找testuser
        testuser = db.query(User).filter(User.username == "testuser").first()
        if not testuser:
            print("❌ testuser不存在")
            return False
        
        print(f"当前testuser手机号: {testuser.phone_number}")
        
        # 检查13800000001是否被占用
        existing_phone = db.query(User).filter(User.phone_number == "13800000001").first()
        if existing_phone and existing_phone.id != testuser.id:
            print(f"❌ 手机号13800000001已被用户 {existing_phone.username} 占用")
            return False
        
        # 更新手机号
        testuser.phone_number = "13800000001"
        db.commit()
        
        print(f"✅ testuser手机号已更新为: {testuser.phone_number}")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    fix_testuser_phone() 
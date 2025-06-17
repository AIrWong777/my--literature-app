#!/usr/bin/env python3
"""
调试登录问题的脚本
"""

import sys
import traceback
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth import verify_password

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        db = next(get_db())
        users = db.query(User).all()
        print(f"   ✅ 数据库连接成功，找到 {len(users)} 个用户")
        
        for user in users:
            print(f"   - 用户: {user.username} (ID: {user.id[:8]}...)")
        
        db.close()
        return True
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        traceback.print_exc()
        return False

def test_password_verification():
    """测试密码验证"""
    print("\n🔐 测试密码验证...")
    try:
        db = next(get_db())
        user = db.query(User).filter(User.username == "testuser").first()
        
        if not user:
            print("   ❌ 用户不存在")
            return False
        
        print(f"   ✅ 找到用户: {user.username}")
        print(f"   - 密码哈希: {user.password_hash[:20]}...")
        
        # 测试密码验证
        is_valid = verify_password("testpass123", user.password_hash)
        print(f"   - 密码验证结果: {'✅ 正确' if is_valid else '❌ 错误'}")
        
        db.close()
        return is_valid
        
    except Exception as e:
        print(f"   ❌ 密码验证失败: {e}")
        traceback.print_exc()
        return False

def test_jwt_creation():
    """测试JWT创建"""
    print("\n🎫 测试JWT创建...")
    try:
        from jose import jwt
        from datetime import datetime, timedelta
        
        SECRET_KEY = "aicodecode"
        ALGORITHM = "HS256"
        
        # 创建测试token
        data = {"sub": "testuser"}
        expire = datetime.utcnow() + timedelta(minutes=30)
        data.update({"exp": expire})
        
        token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        print(f"   ✅ JWT创建成功: {token[:50]}...")
        
        # 验证token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"   ✅ JWT验证成功: {payload}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JWT处理失败: {e}")
        traceback.print_exc()
        return False

def test_login_logic():
    """测试登录逻辑"""
    print("\n🔑 测试完整登录逻辑...")
    try:
        from fastapi.security import OAuth2PasswordRequestForm
        from datetime import timedelta, datetime
        from jose import jwt
        
        # 模拟登录请求
        db = next(get_db())
        
        # 查找用户
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            print("   ❌ 用户不存在")
            return False
        
        # 验证密码
        if not verify_password("testpass123", user.password_hash):
            print("   ❌ 密码错误")
            return False
        
        # 创建token
        SECRET_KEY = "aicodecode"
        ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {"sub": user.username}
        expire = datetime.utcnow() + access_token_expires
        to_encode.update({"exp": expire})
        access_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        print(f"   ✅ 登录逻辑成功")
        print(f"   - Token: {access_token[:50]}...")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 登录逻辑失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🐛 登录问题调试")
    print("="*40)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("密码验证", test_password_verification),
        ("JWT创建", test_jwt_creation),
        ("登录逻辑", test_login_logic)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n❌ {test_name} 测试失败，停止后续测试")
            break
    
    print(f"\n📊 测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        print("🎉 所有基础功能正常，问题可能在FastAPI路由层")
    else:
        print("⚠️  发现基础功能问题")

if __name__ == "__main__":
    main()
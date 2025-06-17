#!/usr/bin/env python3
"""
最终集成测试 - 验证手机号登录系统是否正常工作
"""

import sys
import os
import requests
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def test_server_health():
    """测试服务器健康状态"""
    print("🔍 测试服务器健康状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            return True
        else:
            print(f"❌ 服务器健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def test_phone_login():
    """测试手机号登录"""
    print("\n📱 测试手机号登录...")
    
    login_data = {
        "phone_number": "13800000001",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ 手机号登录成功")
            print(f"   令牌类型: {token_data.get('token_type')}")
            return access_token
        else:
            print(f"❌ 手机号登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        return None

def test_user_info(token):
    """测试获取用户信息"""
    print("\n👤 测试获取用户信息...")
    
    if not token:
        print("❌ 需要有效的访问令牌")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print("✅ 获取用户信息成功")
            print(f"   用户名: {user_info.get('username')}")
            print(f"   手机号: {user_info.get('phone_number')}")
            return True
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 用户信息请求异常: {e}")
        return False

def test_legacy_login():
    """测试传统用户名登录（兼容性测试）"""
    print("\n🔄 测试传统用户名登录...")
    
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("✅ 传统登录成功 (兼容性正常)")
            return access_token
        else:
            print(f"❌ 传统登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 传统登录请求异常: {e}")
        return None

def test_groups_access(token):
    """测试研究组访问"""
    print("\n📋 测试研究组访问...")
    
    if not token:
        print("❌ 需要有效的访问令牌")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/groups", headers=headers)
        if response.status_code == 200:
            groups_data = response.json()
            groups = groups_data.get("groups", [])
            print(f"✅ 获取研究组成功: {len(groups)} 个组")
            if groups:
                print(f"   第一个组: {groups[0]['name']}")
            return len(groups) > 0
        else:
            print(f"❌ 获取研究组失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 研究组请求异常: {e}")
        return False

def main():
    """主测试流程"""
    print("🚀 开始最终集成测试")
    print("=" * 50)
    
    results = {}
    
    # 1. 测试服务器健康状态
    results["服务器健康检查"] = test_server_health()
    
    if not results["服务器健康检查"]:
        print("\n❌ 服务器不可用，终止测试")
        return
    
    # 2. 测试手机号登录
    phone_token = test_phone_login()
    results["手机号登录"] = phone_token is not None
    
    # 3. 测试用户信息获取
    if phone_token:
        results["用户信息获取"] = test_user_info(phone_token)
        results["研究组访问"] = test_groups_access(phone_token)
    else:
        results["用户信息获取"] = False
        results["研究组访问"] = False
    
    # 4. 测试传统登录兼容性
    legacy_token = test_legacy_login()
    results["传统登录兼容性"] = legacy_token is not None
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！新的手机号登录系统工作正常！")
    else:
        print("⚠️ 部分测试失败，请检查具体问题")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
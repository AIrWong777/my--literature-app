#!/usr/bin/env python3
"""
简单的登录测试脚本
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login():
    """测试登录功能"""
    print("🔐 测试登录功能...")
    
    # 测试数据
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        # 发送登录请求
        response = requests.post(
            f"{BASE_URL}/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功!")
            print(f"Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"Token类型: {result.get('token_type', 'N/A')}")
            return result.get('access_token')
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_protected_endpoint(token):
    """测试受保护的接口"""
    if not token:
        print("⚠️  没有有效token，跳过受保护接口测试")
        return
    
    print("\n🔒 测试受保护接口...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/user/groups", headers=headers)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 受保护接口访问成功!")
            print(f"用户研究组数量: {len(result.get('groups', []))}")
        else:
            print(f"❌ 受保护接口访问失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    """主函数"""
    print("🧪 简单登录测试")
    print("="*30)
    
    # 测试基础连接
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return
    
    # 测试登录
    token = test_login()
    
    # 测试受保护接口
    test_protected_endpoint(token)

if __name__ == "__main__":
    main()
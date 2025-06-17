"""
测试新集成的认证API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """测试用户注册"""
    print("=== 测试用户注册 ===")
    
    data = {
        "username": "testuser001",
        "phone_number": "13800138001",
        "password": "password123",
        "password_confirm": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"注册请求失败: {e}")
        return False

def test_login():
    """测试手机号登录"""
    print("\n=== 测试手机号登录 ===")
    
    data = {
        "phone_number": "13800138001",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if response.status_code == 200 and 'access_token' in result:
            return result
        return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None

def test_get_user_info(access_token):
    """测试获取用户信息"""
    print("\n=== 测试获取用户信息 ===")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return False

def test_health():
    """测试健康检查"""
    print("=== 测试健康检查 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_refresh_token(refresh_token):
    """测试刷新令牌"""
    print("\n=== 测试刷新令牌 ===")
    
    data = {"refresh_token": refresh_token}
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/refresh", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if response.status_code == 200 and 'access_token' in result:
            return result['access_token']
        return None
    except Exception as e:
        print(f"刷新令牌请求失败: {e}")
        return None

def main():
    print("开始测试新集成的认证API...")
    
    # 1. 测试健康检查
    if not test_health():
        print("服务器不可用，停止测试")
        return
    
    # 2. 测试注册
    register_success = test_register()
    
    # 3. 测试登录
    login_result = test_login()
    access_token = login_result.get('access_token') if login_result else None
    refresh_token = login_result.get('refresh_token') if login_result else None
    
    # 4. 测试获取用户信息
    user_info_success = False
    if access_token:
        user_info_success = test_get_user_info(access_token)
    
    # 5. 测试刷新令牌
    refresh_success = False
    if refresh_token:
        new_access_token = test_refresh_token(refresh_token)
        refresh_success = new_access_token is not None
    
    print("\n=== 测试总结 ===")
    print(f"注册: {'✓' if register_success else '✗'}")
    print(f"登录: {'✓' if access_token else '✗'}")
    print(f"获取用户信息: {'✓' if user_info_success else '✗'}")
    print(f"刷新令牌: {'✓' if refresh_success else '✗'}")

if __name__ == "__main__":
    main() 
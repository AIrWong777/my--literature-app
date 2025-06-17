 #!/usr/bin/env python3
"""
课题组管理功能自动化测试脚本
使用此脚本来验证后端API是否正确工作
"""

import requests
import json
import sys

# API基础URL
BASE_URL = "http://127.0.0.1:8000"

def test_login(username="testuser", password="testpass123"):
    """测试用户登录"""
    print("🔐 测试用户登录...")
    
    url = f"{BASE_URL}/login"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, data=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print("✅ 登录成功!")
            print(f"Token: {token[:50]}...")
            return token
        else:
            print("❌ 登录失败!")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败! 请确保应用正在运行 (python run.py)")
        return None
    except Exception as e:
        print(f"❌ 登录错误: {e}")
        return None

def test_create_group(token):
    """测试创建课题组"""
    print("\n📝 测试创建课题组...")
    
    url = f"{BASE_URL}/groups/create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试数据
    params = {
        "name": "AI研究测试组",
        "institution": "测试大学", 
        "description": "这是一个用于测试的课题组",
        "research_area": "人工智能"
    }
    
    try:
        response = requests.post(url, params=params, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            group_id = result.get("group_id")
            invitation_code = result.get("invitation_code")
            print("✅ 创建课题组成功!")
            print(f"课题组ID: {group_id}")
            print(f"邀请码: {invitation_code}")
            return group_id, invitation_code
        else:
            print("❌ 创建课题组失败!")
            return None, None
            
    except Exception as e:
        print(f"❌ 创建课题组错误: {e}")
        return None, None

def test_join_group(token, group_id, invitation_code):
    """测试加入课题组"""
    print("\n🤝 测试加入课题组...")
    
    url = f"{BASE_URL}/groups/join"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "group_id": group_id,
        "invitation_code": invitation_code
    }
    
    try:
        response = requests.post(url, params=params, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 加入课题组成功!")
            return True
        else:
            print("❌ 加入课题组失败!")
            return False
            
    except Exception as e:
        print(f"❌ 加入课题组错误: {e}")
        return False

def test_join_group_duplicate(token, group_id, invitation_code):
    """测试重复加入课题组（应该失败）"""
    print("\n🔄 测试重复加入课题组（预期失败）...")
    
    url = f"{BASE_URL}/groups/join"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "group_id": group_id,
        "invitation_code": invitation_code
    }
    
    try:
        response = requests.post(url, params=params, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 400:
            print("✅ 正确拒绝重复加入!")
            return True
        else:
            print("❌ 应该拒绝重复加入，但没有!")
            return False
            
    except Exception as e:
        print(f"❌ 测试重复加入错误: {e}")
        return False

def test_invalid_group(token):
    """测试加入无效课题组（应该失败）"""
    print("\n❌ 测试加入无效课题组（预期失败）...")
    
    url = f"{BASE_URL}/groups/join"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "group_id": "invalid-group-id",
        "invitation_code": "invalid-code"
    }
    
    try:
        response = requests.post(url, params=params, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 400:
            print("✅ 正确拒绝无效课题组!")
            return True
        else:
            print("❌ 应该拒绝无效课题组，但没有!")
            return False
            
    except Exception as e:
        print(f"❌ 测试无效课题组错误: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始课题组管理功能测试\n")
    print("请确保:")
    print("1. 应用已启动 (python run.py)")
    print("2. 测试用户已创建 (python app/create_test_user.py)")
    print("-" * 50)
    
    # 1. 测试登录
    token = test_login()
    if not token:
        print("\n❌ 无法获取token，停止测试")
        sys.exit(1)
    
    # 2. 测试创建课题组
    group_id, invitation_code = test_create_group(token)
    if not group_id:
        print("\n❌ 无法创建课题组，停止测试")
        sys.exit(1)
    
    # 3. 测试创建者尝试加入自己的课题组（应该失败）
    test_join_group_duplicate(token, group_id, invitation_code)
    
    # 4. 测试无效课题组（应该失败）
    test_invalid_group(token)
    
    print("\n" + "="*50)
    print("🎉 课题组管理功能测试完成!")
    print("如果所有测试都显示 ✅，说明功能实现正确")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试main界面新功能的脚本
包括：文献操作、搜索、退出课题组等功能
"""

import requests
import os
import time

BASE_URL = "http://localhost:8000"

def test_main_features():
    """测试main界面的新功能"""
    
    print("🚀 开始测试main界面新功能...")
    
    # 登录获取token
    print("\n1. 登录系统...")
    login_data = {
        "phone_number": "13800000001",
        "password": "password123"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 登录成功")
        else:
            print("❌ 登录失败，请检查用户是否存在")
            return
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 测试获取私人文献列表
    print("\n2. 测试获取私人文献列表...")
    try:
        response = requests.get(f"{BASE_URL}/literature/private", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取私人文献成功，共 {data['total']} 篇文献")
            if data['literature']:
                print(f"   第一篇文献: {data['literature'][0]['title']}")
        else:
            print(f"❌ 获取私人文献失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取私人文献异常: {e}")
    
    # 测试获取用户课题组
    print("\n3. 测试获取用户课题组...")
    try:
        response = requests.get(f"{BASE_URL}/user/groups", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取课题组成功，共 {data['total']} 个课题组")
            if data['groups']:
                group = data['groups'][0]
                group_id = group['id']
                print(f"   第一个课题组: {group['name']}")
                
                # 测试获取课题组文献
                print("\n4. 测试获取课题组文献...")
                lit_response = requests.get(f"{BASE_URL}/literature/public/{group_id}", headers=headers)
                if lit_response.status_code == 200:
                    lit_data = lit_response.json()
                    print(f"✅ 获取课题组文献成功，共 {lit_data['total']} 篇文献")
                    
                    if lit_data['literature']:
                        literature_id = lit_data['literature'][0]['id']
                        
                        # 测试获取文献详情
                        print("\n5. 测试获取文献详情...")
                        detail_response = requests.get(f"{BASE_URL}/literature/detail/{literature_id}", headers=headers)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            print(f"✅ 获取文献详情成功: {detail_data['title']}")
                        else:
                            print(f"❌ 获取文献详情失败: {detail_response.status_code}")
                else:
                    print(f"❌ 获取课题组文献失败: {lit_response.status_code}")
                
                # 测试获取课题组信息
                print("\n6. 测试获取课题组信息...")
                info_response = requests.get(f"{BASE_URL}/groups/{group_id}/info", headers=headers)
                if info_response.status_code == 200:
                    info_data = info_response.json()
                    print(f"✅ 获取课题组信息成功: {info_data['name']}")
                else:
                    print(f"❌ 获取课题组信息失败: {info_response.status_code}")
                
                # 测试获取课题组成员
                print("\n7. 测试获取课题组成员...")
                members_response = requests.get(f"{BASE_URL}/groups/{group_id}/members", headers=headers)
                if members_response.status_code == 200:
                    members_data = members_response.json()
                    print(f"✅ 获取课题组成员成功，共 {members_data['total']} 名成员")
                else:
                    print(f"❌ 获取课题组成员失败: {members_response.status_code}")
                
            else:
                print("   用户暂无课题组")
        else:
            print(f"❌ 获取课题组失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取课题组异常: {e}")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    test_main_features() 
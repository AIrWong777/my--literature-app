"""
快速诊断脚本 - 检查系统状态和数据
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"

def quick_check():
    print("🔍 快速系统诊断")
    print("=" * 40)
    
    # 1. 检查服务器状态
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print(f"❌ 服务器状态异常: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接服务器: {e}")
        return
    
    # 2. 测试登录
    try:
        response = requests.post(f"{BASE_URL}/login", data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ 用户登录成功")
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return
    
    # 3. 检查用户研究组
    try:
        response = requests.get(f"{BASE_URL}/user/groups", headers=headers)
        print(f"研究组接口状态: {response.status_code}")
        print(f"研究组数据: {response.text}")
        
        if response.status_code == 200:
            groups = response.json()
            print(f"✅ 用户有 {len(groups)} 个研究组")
            
            if len(groups) > 0:
                group = groups[0]
                group_id = group["id"]
                print(f"第一个研究组: {group['name']} (ID: {group_id})")
                
                # 4. 检查文献列表
                response = requests.get(f"{BASE_URL}/literature/public/{group_id}", headers=headers)
                print(f"文献列表接口状态: {response.status_code}")
                print(f"文献数据: {response.text}")
                
                if response.status_code == 200:
                    literature_data = response.json()
                    if "literature" in literature_data:
                        literature_count = len(literature_data["literature"])
                        print(f"✅ 研究组有 {literature_count} 篇文献")
                        
                        if literature_count > 0:
                            lit = literature_data["literature"][0]
                            print(f"第一篇文献: {lit['title']} (ID: {lit['id']})")
                        else:
                            print("⚠️ 研究组中没有文献")
                    else:
                        print(f"❌ 文献数据格式异常: {literature_data}")
                else:
                    print(f"❌ 获取文献列表失败: {response.status_code}")
            else:
                print("⚠️ 用户没有加入任何研究组")
        else:
            print(f"❌ 获取研究组失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查研究组异常: {e}")

if __name__ == "__main__":
    quick_check()
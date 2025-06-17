#!/usr/bin/env python3
"""
文献管理API测试脚本
测试文献上传和列表查看功能
"""

import requests
import json
import sys
import os
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000"

def create_test_pdf():
    """创建一个简单的测试PDF文件"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    test_file_path = "test_document.pdf"
    
    # 创建一个真实的PDF文件
    c = canvas.Canvas(test_file_path, pagesize=letter)
    c.drawString(100, 750, "这是一个测试文档")
    c.drawString(100, 730, "用于测试文献上传功能")
    c.drawString(100, 710, "标题：人工智能研究进展")
    c.drawString(100, 690, "内容：本文介绍了人工智能的最新研究进展...")
    c.save()
    
    return test_file_path

def test_login():
    """测试登录获取token"""
    print("🔐 测试登录...")
    
    url = f"{BASE_URL}/login"
    data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print("✅ 登录成功!")
            return token
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录错误: {e}")
        return None

def test_create_group(token):
    """测试创建研究组"""
    print("\n📝 测试创建研究组...")
    
    url = f"{BASE_URL}/groups/create"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "name": "文献测试组",
        "institution": "测试大学",
        "description": "用于测试文献上传功能的研究组",
        "research_area": "人工智能"
    }
    
    try:
        response = requests.post(url, params=params, headers=headers)
        if response.status_code == 200:
            result = response.json()
            group_id = result.get("group_id")
            print(f"✅ 创建研究组成功! ID: {group_id}")
            return group_id
        else:
            print(f"❌ 创建研究组失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 创建研究组错误: {e}")
        return None

def test_upload_literature(token, group_id):
    """测试文献上传"""
    print("\n📄 测试文献上传...")
    
    # 创建测试文件
    test_file = create_test_pdf()
    
    url = f"{BASE_URL}/literature/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file, f, "application/pdf")}
            data = {
                "group_id": group_id,
                "title": "人工智能研究进展测试文档"
            }
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            literature_id = result.get("literature_id")
            print(f"✅ 文献上传成功!")
            print(f"   文献ID: {literature_id}")
            print(f"   标题: {result.get('title')}")
            print(f"   文件名: {result.get('filename')}")
            print(f"   文件大小: {result.get('file_size')} 字节")
            
            # 清理测试文件
            os.remove(test_file)
            return literature_id
        else:
            print(f"❌ 文献上传失败: {response.text}")
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
            return None
            
    except Exception as e:
        print(f"❌ 文献上传错误: {e}")
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        return None

def test_get_literature_list(token, group_id):
    """测试获取文献列表"""
    print("\n📚 测试获取文献列表...")
    
    url = f"{BASE_URL}/literature/public/{group_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            total = result.get("total", 0)
            literature_list = result.get("literature", [])
            
            print(f"✅ 获取文献列表成功!")
            print(f"   总数: {total}")
            
            for i, lit in enumerate(literature_list, 1):
                print(f"   {i}. {lit.get('title')}")
                print(f"      文件名: {lit.get('filename')}")
                print(f"      上传者: {lit.get('uploader_name')}")
                print(f"      上传时间: {lit.get('upload_time')}")
                print(f"      文件大小: {lit.get('file_size')} 字节")
                print()
            
            return True
        else:
            print(f"❌ 获取文献列表失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取文献列表错误: {e}")
        return False

def test_get_user_groups(token):
    """测试获取用户研究组列表"""
    print("\n🏢 测试获取用户研究组...")
    
    url = f"{BASE_URL}/user/groups"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            total = result.get("total", 0)
            groups = result.get("groups", [])
            
            print(f"✅ 获取用户研究组成功!")
            print(f"   总数: {total}")
            
            for i, group in enumerate(groups, 1):
                print(f"   {i}. {group.get('name')}")
                print(f"      机构: {group.get('institution')}")
                print(f"      研究领域: {group.get('research_area')}")
                print(f"      ID: {group.get('id')}")
                print()
            
            return True
        else:
            print(f"❌ 获取用户研究组失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取用户研究组错误: {e}")
        return False

def test_upload_invalid_file(token, group_id):
    """测试上传无效文件类型"""
    print("\n❌ 测试上传无效文件类型...")
    
    # 创建一个txt文件（不被允许的类型）
    test_file = "test_invalid.txt"
    with open(test_file, "w") as f:
        f.write("这是一个不被允许的文件类型")
    
    url = f"{BASE_URL}/literature/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file, f, "text/plain")}
            data = {"group_id": group_id}
            
            response = requests.post(url, headers=headers, files=files, data=data)
            
        if response.status_code == 400:
            print("✅ 正确拒绝了无效文件类型!")
            print(f"   错误信息: {response.json().get('detail')}")
        else:
            print(f"❌ 应该拒绝无效文件类型，但没有: {response.text}")
        
        # 清理测试文件
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ 测试无效文件类型错误: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """主测试函数"""
    print("🚀 文献管理API功能测试")
    print("="*50)
    print("请确保:")
    print("1. 应用已启动 (python run.py)")
    print("2. 测试用户已创建")
    print("-" * 50)
    
    # 1. 登录获取token
    token = test_login()
    if not token:
        print("\n❌ 无法获取token，停止测试")
        sys.exit(1)
    
    # 2. 创建测试研究组
    group_id = test_create_group(token)
    if not group_id:
        print("\n❌ 无法创建研究组，停止测试")
        sys.exit(1)
    
    # 3. 测试获取用户研究组
    test_get_user_groups(token)
    
    # 4. 测试文献上传
    literature_id = test_upload_literature(token, group_id)
    if not literature_id:
        print("\n⚠️  文献上传失败，但继续其他测试")
    
    # 5. 测试获取文献列表
    test_get_literature_list(token, group_id)
    
    # 6. 测试上传无效文件
    test_upload_invalid_file(token, group_id)
    
    print("\n" + "="*50)
    print("🎉 文献管理API测试完成!")
    print("如果大部分测试显示 ✅，说明API功能基本正常")

if __name__ == "__main__":
    main()
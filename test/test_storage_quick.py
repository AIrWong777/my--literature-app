#!/usr/bin/env python3
"""
快速存储管理功能测试
"""

import requests
import tempfile
import os

BASE_URL = "http://localhost:8000"

def main():
    """主测试函数"""
    print("🚀 快速存储管理功能测试")
    print("="*40)
    
    # 1. 登录
    print("🔐 登录...")
    login_response = requests.post(f"{BASE_URL}/login", data={
        "username": "testuser",
        "password": "testpass123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")
    
    # 2. 获取用户研究组
    print("\n📋 获取研究组...")
    groups_response = requests.get(f"{BASE_URL}/user/groups", headers=headers)
    
    if groups_response.status_code != 200:
        print(f"❌ 获取研究组失败: {groups_response.text}")
        return
    
    groups = groups_response.json()["groups"]
    if not groups:
        print("❌ 用户没有研究组")
        return
    
    group_id = groups[0]["id"]
    print(f"✅ 找到研究组: {groups[0]['name']} ({group_id})")
    
    # 3. 测试文献统计
    print("\n📊 测试文献统计...")
    stats_response = requests.get(f"{BASE_URL}/literature/stats/{group_id}", headers=headers)
    
    if stats_response.status_code == 200:
        stats = stats_response.json()["statistics"]
        print(f"✅ 统计获取成功:")
        print(f"   - 活跃文献: {stats['active_count']}")
        print(f"   - 已删除文献: {stats['deleted_count']}")
        print(f"   - 总大小: {stats['total_size']} 字节")
    else:
        print(f"❌ 统计获取失败: {stats_response.text}")
    
    # 4. 测试存储统计
    print("\n💾 测试存储统计...")
    storage_response = requests.get(f"{BASE_URL}/admin/storage/stats", headers=headers)
    
    if storage_response.status_code == 200:
        result = storage_response.json()
        storage_stats = result["storage_statistics"]
        print(f"✅ 存储统计成功:")
        print(f"   - 总研究组: {storage_stats['total_groups']}")
        print(f"   - 总文件数: {storage_stats['total_files']}")
        print(f"   - 总大小: {storage_stats['total_size']} 字节")
    else:
        print(f"❌ 存储统计失败: {storage_response.text}")
    
    # 5. 测试获取已删除文献
    print("\n🗑️  测试获取已删除文献...")
    deleted_response = requests.get(f"{BASE_URL}/literature/deleted/{group_id}", headers=headers)
    
    if deleted_response.status_code == 200:
        deleted_list = deleted_response.json()["deleted_literature"]
        print(f"✅ 获取成功: 找到 {len(deleted_list)} 个已删除文献")
    else:
        print(f"❌ 获取失败: {deleted_response.text}")
    
    # 6. 测试存储清理
    print("\n🧹 测试存储清理...")
    cleanup_response = requests.post(f"{BASE_URL}/admin/storage/cleanup", headers=headers)
    
    if cleanup_response.status_code == 200:
        result = cleanup_response.json()
        print(f"✅ 清理成功: 清理了 {result['count']} 个空目录")
    else:
        print(f"❌ 清理失败: {cleanup_response.text}")
    
    print("\n🎉 存储管理功能测试完成!")

if __name__ == "__main__":
    main()
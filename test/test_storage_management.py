#!/usr/bin/env python3
"""
存储管理功能测试脚本
测试软删除、恢复、存储统计等功能
"""

import requests
import json
import os
import tempfile
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000"

class StorageManagementTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.group_id = None
        self.literature_id = None
    
    def login(self):
        """登录获取token"""
        print("🔐 用户登录...")
        
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            # 从token中解析用户信息
            import jwt
            payload = jwt.decode(result["access_token"], options={"verify_signature": False})
            self.user_id = payload.get("sub")  # 用户名作为ID
            print(f"   ✅ 登录成功: {self.user_id}")
            return True
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return False
    
    def get_headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_user_groups(self):
        """获取用户研究组"""
        print("\n📋 获取用户研究组...")
        
        response = requests.get(f"{BASE_URL}/user/groups", headers=self.get_headers())
        
        if response.status_code == 200:
            groups = response.json()["groups"]
            if groups:
                self.group_id = groups[0]["id"]
                print(f"   ✅ 找到研究组: {groups[0]['name']} ({self.group_id})")
                return True
            else:
                print("   ❌ 用户没有加入任何研究组")
                return False
        else:
            print(f"   ❌ 获取研究组失败: {response.text}")
            return False
    
    def upload_test_file(self):
        """上传测试文件"""
        print("\n📤 上传测试文件...")
        
        # 创建测试PDF文件
        test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("test_storage.pdf", f, "application/pdf")}
            data = {
                "group_id": self.group_id,
                "title": "存储管理测试文档"
            }
            
            response = requests.post(
                f"{BASE_URL}/literature/upload",
                files=files,
                data=data,
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                result = response.json()
                self.literature_id = result["literature_id"]
                print(f"   ✅ 文件上传成功: {result['title']}")
                return True
            else:
                print(f"   ❌ 文件上传失败: {response.text}")
                return False
                
        finally:
            # 清理临时文件
            if os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except PermissionError:
                    # Windows 系统可能需要稍等一下
                    import time
                    time.sleep(0.1)
                    try:
                os.unlink(tmp_file_path)
                    except:
                        pass  # 如果还是删除不了，就忽略
    
    def test_literature_statistics(self):
        """测试文献统计功能"""
        print("\n📊 测试文献统计...")
        
        response = requests.get(
            f"{BASE_URL}/literature/stats/{self.group_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            stats = response.json()["statistics"]
            print(f"   ✅ 统计获取成功:")
            print(f"      - 活跃文献: {stats['active_count']}")
            print(f"      - 已删除文献: {stats['deleted_count']}")
            print(f"      - 总大小: {stats['total_size']} 字节")
            print(f"      - 文件类型分布: {stats['type_distribution']}")
            return True
        else:
            print(f"   ❌ 获取统计失败: {response.text}")
            return False
    
    def test_soft_delete(self):
        """测试软删除功能"""
        print("\n🗑️  测试软删除...")
        
        data = {"reason": "测试软删除功能"}
        
        response = requests.delete(
            f"{BASE_URL}/literature/{self.literature_id}",
            params=data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            print(f"   ✅ 软删除成功: {response.json()['message']}")
            return True
        else:
            print(f"   ❌ 软删除失败: {response.text}")
            return False
    
    def test_get_deleted_literature(self):
        """测试获取已删除文献列表"""
        print("\n📋 测试获取已删除文献...")
        
        response = requests.get(
            f"{BASE_URL}/literature/deleted/{self.group_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            deleted_list = result["deleted_literature"]
            print(f"   ✅ 获取成功: 找到 {len(deleted_list)} 个已删除文献")
            
            if deleted_list:
                lit = deleted_list[0]
                print(f"      - 标题: {lit['title']}")
                print(f"      - 删除时间: {lit['deleted_at']}")
                print(f"      - 删除原因: {lit['delete_reason']}")
            
            return True
        else:
            print(f"   ❌ 获取失败: {response.text}")
            return False
    
    def test_restore_literature(self):
        """测试恢复文献功能"""
        print("\n🔄 测试恢复文献...")
        
        response = requests.post(
            f"{BASE_URL}/literature/{self.literature_id}/restore",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            print(f"   ✅ 恢复成功: {response.json()['message']}")
            return True
        else:
            print(f"   ❌ 恢复失败: {response.text}")
            return False
    
    def test_storage_statistics(self):
        """测试存储统计功能"""
        print("\n💾 测试存储统计...")
        
        response = requests.get(
            f"{BASE_URL}/admin/storage/stats",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            storage_stats = result["storage_statistics"]
            storage_health = result["storage_health"]
            
            print(f"   ✅ 存储统计获取成功:")
            print(f"      - 总研究组: {storage_stats['total_groups']}")
            print(f"      - 总文件数: {storage_stats['total_files']}")
            print(f"      - 总大小: {storage_stats['total_size']} 字节")
            print(f"      - 存储健康: {'正常' if storage_health['valid'] else '异常'}")
            
            if storage_health['issues']:
                print(f"      - 问题: {storage_health['issues']}")
            
            return True
        else:
            print(f"   ❌ 获取存储统计失败: {response.text}")
            return False
    
    def test_storage_cleanup(self):
        """测试存储清理功能"""
        print("\n🧹 测试存储清理...")
        
        response = requests.post(
            f"{BASE_URL}/admin/storage/cleanup",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 存储清理成功: 清理了 {result['count']} 个空目录")
            return True
        else:
            print(f"   ❌ 存储清理失败: {response.text}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 存储管理功能测试")
        print("="*50)
        
        tests = [
            ("登录", self.login),
            ("获取研究组", self.get_user_groups),
            ("上传测试文件", self.upload_test_file),
            ("文献统计", self.test_literature_statistics),
            ("软删除", self.test_soft_delete),
            ("获取已删除文献", self.test_get_deleted_literature),
            ("恢复文献", self.test_restore_literature),
            ("存储统计", self.test_storage_statistics),
            ("存储清理", self.test_storage_cleanup)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"   ⚠️  {test_name} 测试失败")
            except Exception as e:
                print(f"   ❌ {test_name} 测试异常: {e}")
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有存储管理功能测试通过!")
        else:
            print("⚠️  部分测试失败，请检查系统状态")

def main():
    """主函数"""
    tester = StorageManagementTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
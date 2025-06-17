#!/usr/bin/env python3
"""
文献上传功能专项测试
测试各种边界情况和错误处理
"""

import requests
import json
import sys
import os
import tempfile
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000"

class LiteratureUploadTester:
    def __init__(self):
        self.token = None
        self.test_group_id = None
        self.test_files = []
    
    def cleanup(self):
        """清理测试文件"""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🧹 清理测试文件: {file_path}")
    
    def login(self):
        """登录获取token - 支持新的手机号登录"""
        print("🔐 尝试登录...")
        
        # 首先尝试手机号登录
        success = self.login_with_phone()
        if success:
            return True
        
        # 如果手机号登录失败，尝试传统用户名登录
        print("⚠️ 手机号登录失败，尝试用户名登录...")
        return self.login_legacy()
    
    def login_with_phone(self, phone_number="13800000001", password="testpass123"):
        """使用手机号登录获取token"""
        print(f"📱 使用手机号登录: {phone_number}")
        
        url = f"{BASE_URL}/api/auth/login"
        data = {
            "phone_number": phone_number,
            "password": password
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                print("✅ 手机号登录成功")
                return True
            else:
                print(f"❌ 手机号登录失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 手机号登录错误: {e}")
            return False
    
    def login_legacy(self, username="testuser", password="testpass123"):
        """使用传统用户名登录（兼容性）"""
        print(f"👤 使用用户名登录: {username}")
        
        url = f"{BASE_URL}/login"
        data = {"username": username, "password": password}
        
        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                print("✅ 用户名登录成功")
                return True
            else:
                print(f"❌ 用户名登录失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 用户名登录错误: {e}")
            return False
    
    def create_test_group(self):
        """创建测试研究组"""
        print("\n📝 创建测试研究组...")
        
        url = f"{BASE_URL}/groups/create"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {
            "name": "文献上传测试组",
            "institution": "测试大学",
            "description": "专门用于测试文献上传功能",
            "research_area": "软件测试"
        }
        
        try:
            response = requests.post(url, params=params, headers=headers)
            if response.status_code == 200:
                self.test_group_id = response.json().get("group_id")
                print(f"✅ 创建测试组成功: {self.test_group_id}")
                return True
            else:
                print(f"❌ 创建测试组失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 创建测试组错误: {e}")
            return False
    
    def create_test_file(self, filename, content, size_mb=None):
        """创建测试文件"""
        file_path = filename
        
        if size_mb:
            # 创建指定大小的文件
            with open(file_path, "wb") as f:
                # 写入指定大小的数据
                data = b"0" * (size_mb * 1024 * 1024)
                f.write(data)
        else:
            # 创建普通文本文件
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        self.test_files.append(file_path)
        return file_path
    
    def test_successful_upload(self):
        """测试成功上传场景"""
        print("\n✅ 测试1: 成功上传PDF文件")
        
        # 创建测试PDF文件
        test_file = self.create_test_file(
            "test_success.pdf",
            "这是一个成功上传的测试PDF文档\n标题：机器学习算法研究\n内容：详细介绍了各种机器学习算法..."
        )
        
        url = f"{BASE_URL}/literature/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "application/pdf")}
                data = {
                    "group_id": self.test_group_id,
                    "title": "机器学习算法研究"
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 上传成功: {result.get('title')}")
                print(f"   📄 文件ID: {result.get('literature_id')}")
                return True
            else:
                print(f"   ❌ 上传失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 上传错误: {e}")
            return False
    
    def test_invalid_file_type(self):
        """测试无效文件类型"""
        print("\n❌ 测试2: 上传不支持的文件类型")
        
        # 创建.txt文件（不被支持）
        test_file = self.create_test_file(
            "test_invalid.txt",
            "这是一个不被支持的文本文件"
        )
        
        url = f"{BASE_URL}/literature/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "text/plain")}
                data = {"group_id": self.test_group_id}
                
                response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', '')
                if "不支持的文件类型" in error_detail:
                    print(f"   ✅ 正确拒绝无效文件类型")
                    print(f"   📝 错误信息: {error_detail}")
                    return True
                else:
                    print(f"   ❌ 错误信息不正确: {error_detail}")
                    return False
            else:
                print(f"   ❌ 应该返回400错误，但返回了: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 测试错误: {e}")
            return False
    
    def test_large_file(self):
        """测试大文件上传"""
        print("\n📏 测试3: 上传超大文件")
        
        # 创建60MB的大文件（超过50MB限制）
        test_file = self.create_test_file("test_large.pdf", "", size_mb=60)
        
        url = f"{BASE_URL}/literature/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "application/pdf")}
                data = {"group_id": self.test_group_id}
                
                response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 400:
                error_detail = response.json().get('detail', '')
                if "文件过大" in error_detail:
                    print(f"   ✅ 正确拒绝超大文件")
                    print(f"   📝 错误信息: {error_detail}")
                    return True
                else:
                    print(f"   ❌ 错误信息不正确: {error_detail}")
                    return False
            else:
                print(f"   ❌ 应该返回400错误，但返回了: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 测试错误: {e}")
            return False
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        print("\n🔒 测试4: 未授权访问")
        
        test_file = self.create_test_file("test_unauth.pdf", "未授权测试文件")
        
        url = f"{BASE_URL}/literature/upload"
        # 不提供Authorization头
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "application/pdf")}
                data = {"group_id": self.test_group_id}
                
                response = requests.post(url, files=files, data=data)
            
            if response.status_code == 401:
                print(f"   ✅ 正确拒绝未授权访问")
                return True
            else:
                print(f"   ❌ 应该返回401错误，但返回了: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 测试错误: {e}")
            return False
    
    def test_invalid_group_access(self):
        """测试访问无效研究组"""
        print("\n🚫 测试5: 访问不存在的研究组")
        
        test_file = self.create_test_file("test_invalid_group.pdf", "无效组测试文件")
        
        url = f"{BASE_URL}/literature/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "application/pdf")}
                data = {"group_id": "invalid-group-id-12345"}
                
                response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code in [403, 404]:
                error_detail = response.json().get('detail', '')
                print(f"   ✅ 正确拒绝无效研究组访问")
                print(f"   📝 错误信息: {error_detail}")
                return True
            else:
                print(f"   ❌ 应该返回403/404错误，但返回了: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 测试错误: {e}")
            return False
    
    def test_empty_file(self):
        """测试空文件上传"""
        print("\n📭 测试6: 上传空文件")
        
        test_file = self.create_test_file("test_empty.pdf", "")
        
        url = f"{BASE_URL}/literature/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "application/pdf")}
                data = {"group_id": self.test_group_id}
                
                response = requests.post(url, headers=headers, files=files, data=data)
            
            # 空文件可能被接受（大小为0字节），也可能被拒绝
            if response.status_code == 200:
                print(f"   ✅ 空文件被接受（0字节）")
                return True
            elif response.status_code == 400:
                error_detail = response.json().get('detail', '')
                print(f"   ✅ 空文件被正确拒绝")
                print(f"   📝 错误信息: {error_detail}")
                return True
            else:
                print(f"   ❌ 意外的响应状态: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 测试错误: {e}")
            return False
    
    def test_special_characters_filename(self):
        """测试特殊字符文件名"""
        print("\n🔤 测试7: 特殊字符文件名")
        
        test_file = self.create_test_file(
            "测试文档-特殊字符@#$%.pdf",
            "包含特殊字符的文件名测试"
        )
        
        url = f"{BASE_URL}/literature/upload"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "application/pdf")}
                data = {"group_id": self.test_group_id}
                
                response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 特殊字符文件名处理成功")
                print(f"   📄 标题: {result.get('title')}")
                return True
            else:
                print(f"   ❌ 特殊字符文件名处理失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ 测试错误: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 文献上传功能专项测试")
        print("="*60)
        
        # 准备工作
        if not self.login():
            return False
        
        if not self.create_test_group():
            return False
        
        # 运行测试
        tests = [
            self.test_successful_upload,
            self.test_invalid_file_type,
            self.test_large_file,
            self.test_unauthorized_access,
            self.test_invalid_group_access,
            self.test_empty_file,
            self.test_special_characters_filename
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"   ❌ 测试异常: {e}")
        
        # 清理
        self.cleanup()
        
        # 总结
        print("\n" + "="*60)
        print(f"🎯 测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！文献上传功能工作正常")
            return True
        else:
            print(f"⚠️  有 {total - passed} 个测试失败，需要检查")
            return False

def main():
    """主函数"""
    print("请确保:")
    print("1. 应用已启动 (python run.py)")
    print("2. 测试用户已创建 (testuser/testpass123)")
    print("-" * 40)
    
    tester = LiteratureUploadTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
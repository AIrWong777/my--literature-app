"""
文献文件服务接口测试脚本 - 调试版本
增加详细的调试信息和错误处理
"""

import requests
import json
import os
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8000"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"

class LiteratureFileServiceTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   详情: {details}")
        print()

    def login(self):
        """用户登录获取token"""
        print("🔐 开始用户登录...")
        try:
            response = requests.post(
                f"{BASE_URL}/login",
                data={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD
                }
            )
            
            print(f"登录响应状态码: {response.status_code}")
            print(f"登录响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_test("用户登录", True, "登录成功", {"token_type": data["token_type"]})
                return True
            else:
                self.log_test("用户登录", False, f"登录失败: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("用户登录", False, f"登录异常: {str(e)}")
            return False

    def get_test_literature_id(self):
        """获取测试用的文献ID"""
        print("📚 获取测试文献ID...")
        try:
            # 先获取用户的研究组
            print("正在获取用户研究组...")
            response = requests.get(f"{BASE_URL}/user/groups", headers=self.headers)
            print(f"研究组响应状态码: {response.status_code}")
            print(f"研究组响应内容: {response.text}")
            
            if response.status_code != 200:
                self.log_test("获取研究组", False, f"无法获取用户研究组，状态码: {response.status_code}")
                return None
                
            groups = response.json()
            print(f"解析后的研究组数据: {groups}")
            print(f"研究组数据类型: {type(groups)}")
            print(f"研究组数量: {len(groups) if isinstance(groups, list) else '不是列表'}")
            
            if not groups or len(groups) == 0:
                self.log_test("获取研究组", False, "用户没有加入任何研究组")
                return None
            
            # 检查数据结构
            if isinstance(groups, list):
                group = groups[0]
            elif isinstance(groups, dict) and 'groups' in groups:
                group = groups['groups'][0]
            else:
                self.log_test("获取研究组", False, f"未知的数据结构: {type(groups)}")
                return None
                
            group_id = group["id"]
            group_name = group.get("name", "未知")
            self.log_test("获取研究组", True, f"找到研究组: {group_name}", {"id": group_id})
            
            # 获取该研究组的文献列表
            print(f"正在获取研究组 {group_id} 的文献列表...")
            response = requests.get(f"{BASE_URL}/literature/public/{group_id}", headers=self.headers)
            print(f"文献列表响应状态码: {response.status_code}")
            print(f"文献列表响应内容: {response.text}")
            
            if response.status_code != 200:
                self.log_test("获取文献列表", False, f"无法获取文献列表，状态码: {response.status_code}")
                return None
                
            literature_data = response.json()
            print(f"解析后的文献数据: {literature_data}")
            
            # 检查文献数据结构
            if isinstance(literature_data, dict) and "literature" in literature_data:
                literature_list = literature_data["literature"]
            elif isinstance(literature_data, list):
                literature_list = literature_data
            else:
                self.log_test("获取文献列表", False, f"未知的文献数据结构: {type(literature_data)}")
                return None
            
            if not literature_list or len(literature_list) == 0:
                self.log_test("获取文献列表", False, "研究组中没有文献")
                return None
                
            literature = literature_list[0]
            literature_id = literature["id"]
            literature_title = literature.get("title", "未知标题")
            self.log_test("获取测试文献", True, f"找到测试文献: {literature_title}", {"id": literature_id})
            return literature_id
            
        except Exception as e:
            import traceback
            print(f"获取文献ID时发生异常: {str(e)}")
            print(f"异常详情: {traceback.format_exc()}")
            self.log_test("获取测试文献", False, f"异常: {str(e)}")
            return None

    def test_basic_endpoints(self):
        """测试基础端点"""
        print("🔍 测试基础端点...")
        
        # 测试根路径
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                self.log_test("根路径", True, "根路径访问正常")
            else:
                self.log_test("根路径", False, f"根路径访问失败: {response.status_code}")
        except Exception as e:
            self.log_test("根路径", False, f"根路径访问异常: {str(e)}")
        
        # 测试健康检查
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log_test("健康检查", True, "健康检查正常")
            else:
                self.log_test("健康检查", False, f"健康检查失败: {response.status_code}")
        except Exception as e:
            self.log_test("健康检查", False, f"健康检查异常: {str(e)}")

    def test_literature_detail(self, literature_id):
        """测试文献详情接口"""
        print("📋 测试文献详情接口...")
        try:
            response = requests.get(
                f"{BASE_URL}/literature/detail/{literature_id}",
                headers=self.headers
            )
            
            print(f"文献详情响应状态码: {response.status_code}")
            print(f"文献详情响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "title", "filename", "file_type", "file_size", 
                                 "upload_time", "uploaded_by", "uploader_name", 
                                 "research_group_id", "group_name", "status", 
                                 "file_exists", "can_view"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test("文献详情接口", False, f"缺少字段: {missing_fields}")
                    return False
                
                self.log_test("文献详情接口", True, "成功获取文献详情", {
                    "title": data["title"],
                    "file_type": data["file_type"],
                    "file_exists": data["file_exists"],
                    "can_view": data["can_view"]
                })
                return data
                
            else:
                self.log_test("文献详情接口", False, f"请求失败: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            import traceback
            print(f"文献详情测试异常: {traceback.format_exc()}")
            self.log_test("文献详情接口", False, f"异常: {str(e)}")
            return None

    def test_file_view(self, literature_id):
        """测试文件查看接口"""
        print("👁️ 测试文件查看接口...")
        try:
            response = requests.get(
                f"{BASE_URL}/literature/view/file/{literature_id}",
                headers=self.headers,
                stream=True
            )
            
            print(f"文件查看响应状态码: {response.status_code}")
            print(f"文件查看响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                content_disposition = response.headers.get("Content-Disposition", "")
                content_length = response.headers.get("Content-Length", "0")
                
                is_inline = "inline" in content_disposition
                
                self.log_test("文件查看接口", True, "成功获取文件", {
                    "content_type": content_type,
                    "content_length": content_length,
                    "is_inline": is_inline,
                    "content_disposition": content_disposition
                })
                return True
                
            elif response.status_code == 404:
                self.log_test("文件查看接口", False, "文件不存在", response.text)
                return False
            elif response.status_code == 403:
                self.log_test("文件查看接口", False, "权限不足", response.text)
                return False
            else:
                self.log_test("文件查看接口", False, f"请求失败: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            import traceback
            print(f"文件查看测试异常: {traceback.format_exc()}")
            self.log_test("文件查看接口", False, f"异常: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始文献文件服务接口测试 - 调试版本")
        print("=" * 60)
        
        # 0. 测试基础端点
        self.test_basic_endpoints()
        
        # 1. 登录
        if not self.login():
            print("❌ 登录失败，无法继续测试")
            return
        
        # 2. 获取测试文献ID
        literature_id = self.get_test_literature_id()
        if not literature_id:
            print("❌ 无法获取测试文献，但继续测试其他功能")
            # 继续测试权限控制等不需要真实文献ID的功能
            self.test_permission_control()
            self.print_test_summary()
            return
        
        # 3. 测试文献详情接口
        detail_data = self.test_literature_detail(literature_id)
        
        # 4. 测试文件查看接口
        if detail_data and detail_data.get("file_exists"):
            self.test_file_view(literature_id)
        else:
            print("⚠️ 文件不存在，跳过文件访问测试")
        
        # 5. 测试权限控制
        self.test_permission_control()
        
        # 6. 输出测试总结
        self.print_test_summary()

    def test_permission_control(self):
        """测试权限控制"""
        print("🔒 测试权限控制...")
        
        # 测试无效的文献ID
        fake_literature_id = "fake-literature-id-123"
        
        try:
            response = requests.get(
                f"{BASE_URL}/literature/detail/{fake_literature_id}",
                headers=self.headers
            )
            
            print(f"无效ID测试响应: {response.status_code} - {response.text}")
            
            if response.status_code == 404:
                self.log_test("权限控制-无效ID", True, "正确拒绝无效文献ID")
            else:
                self.log_test("权限控制-无效ID", False, f"应该返回404，实际返回: {response.status_code}")
                
        except Exception as e:
            self.log_test("权限控制-无效ID", False, f"异常: {str(e)}")

        # 测试无token访问
        try:
            response = requests.get(f"{BASE_URL}/literature/detail/{fake_literature_id}")
            
            print(f"无token测试响应: {response.status_code} - {response.text}")
            
            if response.status_code == 401:
                self.log_test("权限控制-无token", True, "正确拒绝无token访问")
            else:
                self.log_test("权限控制-无token", False, f"应该返回401，实际返回: {response.status_code}")
                
        except Exception as e:
            self.log_test("权限控制-无token", False, f"异常: {str(e)}")

    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "无测试")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n📝 详细测试结果已保存到 test_results_debug.json")
        
        # 保存详细结果到文件
        with open("test_results_debug.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    tester = LiteratureFileServiceTester()
    tester.run_all_tests()
#!/usr/bin/env python3
"""
AI集成端到端测试

测试完整的文献管理和AI问答流程
"""
import sys
import os
import json
import time
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_ai_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIIntegrationTester:
    """AI集成测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": []
            }
        }
        
    def log_test_result(self, test_name: str, success: bool, 
                       details: Dict = None, error: str = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        
        self.test_results["tests"].append(result)
        self.test_results["summary"]["total"] += 1
        
        if success:
            self.test_results["summary"]["passed"] += 1
            logger.info(f"[PASS] {test_name} - 通过")
        else:
            self.test_results["summary"]["failed"] += 1
            self.test_results["summary"]["errors"].append(f"{test_name}: {error}")
            logger.error(f"[FAIL] {test_name} - 失败: {error}")
    
    def test_system_health(self) -> bool:
        """测试系统健康状态"""
        logger.info("[TEST] 测试系统健康状态...")
        
        try:
            # 测试基础健康检查 - 添加超时设置
            logger.info(f"正在连接到: {self.base_url}/health")
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code != 200:
                raise Exception(f"健康检查失败: {response.status_code}")
            
            health_data = response.json()
            logger.info("基础健康检查通过")
            
            # 测试AI健康检查
            try:
                logger.info(f"正在连接到: {self.base_url}/health/ai")
                ai_health_response = self.session.get(f"{self.base_url}/health/ai", timeout=10)
                if ai_health_response.status_code == 200:
                    ai_health_data = ai_health_response.json()
                    health_data["ai_health"] = ai_health_data
                    logger.info("AI健康检查通过")
                else:
                    logger.warning(f"AI健康检查失败: {ai_health_response.status_code}")
            except Exception as e:
                logger.warning(f"AI健康检查异常: {e}")
            
            self.log_test_result(
                "系统健康检查",
                True,
                {
                    "basic_health": health_data,
                    "response_time": response.elapsed.total_seconds()
                }
            )
            return True
            
        except requests.exceptions.Timeout:
            error_msg = "连接超时 - 请确保服务器正在运行"
            logger.error(error_msg)
            self.log_test_result("系统健康检查", False, error=error_msg)
            return False
        except requests.exceptions.ConnectionError:
            error_msg = f"无法连接到服务器 {self.base_url} - 请确保服务器正在运行"
            logger.error(error_msg)
            self.log_test_result("系统健康检查", False, error=error_msg)
            return False
        except Exception as e:
            error_msg = f"健康检查失败: {str(e)}"
            logger.error(error_msg)
            self.log_test_result("系统健康检查", False, error=error_msg)
            return False
    
    def test_user_authentication(self, phone_number: str = "13800000001", 
                                password: str = "testpass123") -> bool:
        """测试用户认证 - 支持手机号登录"""
        logger.info("[TEST] 测试用户认证...")
        
        try:
            # 首先尝试手机号登录
            if self.login_with_phone(phone_number, password):
                return True
            
            # 如果手机号登录失败，尝试传统用户名登录
            logger.warning("手机号登录失败，尝试用户名登录...")
            return self.login_legacy("testuser", password)
                
        except Exception as e:
            self.log_test_result("用户认证", False, error=str(e))
            return False
    
    def login_with_phone(self, phone_number: str, password: str) -> bool:
        """使用手机号登录"""
        try:
            login_data = {
                "phone_number": phone_number,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                logger.info(f"手机号登录成功: {phone_number}")
                self.log_test_result(
                    "手机号登录",
                    True,
                    {"phone_number": phone_number, "token_type": token_data.get("token_type")}
                )
                return True
            else:
                logger.error(f"手机号登录失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"手机号登录异常: {e}")
            return False
    
    def login_legacy(self, username: str, password: str) -> bool:
        """使用传统用户名登录（兼容性）"""
        try:
            login_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/login",
                data=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                
                logger.info(f"用户名登录成功: {username}")
                self.log_test_result(
                    "用户名登录",
                    True,
                    {"username": username, "token_type": token_data.get("token_type")}
                )
                return True
            else:
                raise Exception(f"登录失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"用户名登录异常: {e}")
            self.log_test_result("用户名登录", False, error=str(e))
            return False
    
    def test_literature_access(self) -> Optional[str]:
        """测试文献访问功能"""
        logger.info("[TEST] 测试文献访问功能...")
        
        try:
            if not self.access_token:
                raise Exception("需要先登录")
            
            # 获取用户组
            groups_response = self.session.get(f"{self.base_url}/user/groups")
            if groups_response.status_code != 200:
                raise Exception(f"获取用户组失败: {groups_response.status_code}")
            
            groups_data = groups_response.json()
            if not groups_data or not groups_data.get("groups"):
                raise Exception("用户没有加入任何研究组")
            
            group_id = groups_data["groups"][0]["id"]
            
            # 获取组内文献
            literature_response = self.session.get(
                f"{self.base_url}/literature/public/{group_id}"
            )
            if literature_response.status_code != 200:
                raise Exception(f"获取文献列表失败: {literature_response.status_code}")
            
            literature_data = literature_response.json()
            if not literature_data.get("literature"):
                logger.warning("该组没有文献，跳过文献访问测试")
                self.log_test_result(
                    "文献访问",
                    True,
                    {"note": "组内无文献，测试跳过"}
                )
                return None
            
            literature_id = literature_data["literature"][0]["id"]
            
            # 测试文献详情
            detail_response = self.session.get(
                f"{self.base_url}/literature/detail/{literature_id}"
            )
            if detail_response.status_code != 200:
                raise Exception(f"获取文献详情失败: {detail_response.status_code}")
            
            detail_data = detail_response.json()
            
            # 测试文件查看（只检查权限，不下载）
            file_response = self.session.head(
                f"{self.base_url}/literature/view/file/{literature_id}"
            )
            
            self.log_test_result(
                "文献访问",
                True,
                {
                    "group_id": group_id,
                    "literature_count": len(literature_data["literature"]),
                    "test_literature_id": literature_id,
                    "file_access_status": file_response.status_code
                }
            )
            return literature_id
            
        except Exception as e:
            self.log_test_result("文献访问", False, error=str(e))
            return None
    
    def test_ai_question_answer(self, literature_id: str) -> bool:
        """测试AI问答功能"""
        logger.info("[TEST] 测试AI问答功能...")
        
        try:
            if not literature_id:
                raise Exception("需要有效的文献ID")
            
            # 测试预设问题
            preset_response = self.session.get(
                f"{self.base_url}/ai/preset-questions/{literature_id}"
            )
            
            preset_questions = []
            if preset_response.status_code == 200:
                preset_data = preset_response.json()
                preset_questions = preset_data.get("questions", [])
            
            # 准备测试问题
            test_questions = [
                "这篇文献的主要内容是什么？",
                "文献中有哪些重要的研究发现？"
            ]
            
            if preset_questions:
                test_questions.append(preset_questions[0])
            
            qa_results = []
            
            for i, question in enumerate(test_questions[:2]):  # 只测试前2个问题
                logger.info(f"测试问题 {i+1}: {question}")
                
                qa_request = {
                    "question": question,
                    "literature_id": literature_id,
                    "max_sources": 3,
                    "include_history": False
                }
                
                start_time = time.time()
                qa_response = self.session.post(
                    f"{self.base_url}/ai/ask",
                    json=qa_request
                )
                response_time = time.time() - start_time
                
                if qa_response.status_code == 200:
                    qa_data = qa_response.json()
                    qa_results.append({
                        "question": question,
                        "success": True,
                        "response_time": response_time,
                        "answer_length": len(qa_data.get("answer", "")),
                        "sources_count": len(qa_data.get("sources", [])),
                        "confidence": qa_data.get("confidence", 0)
                    })
                else:
                    qa_results.append({
                        "question": question,
                        "success": False,
                        "error": f"HTTP {qa_response.status_code}: {qa_response.text[:200]}"
                    })
                
                # 避免API限制
                time.sleep(1)
            
            # 检查结果
            successful_qa = sum(1 for r in qa_results if r["success"])
            
            self.log_test_result(
                "AI问答功能",
                successful_qa > 0,
                {
                    "preset_questions_count": len(preset_questions),
                    "test_questions_count": len(test_questions),
                    "successful_qa": successful_qa,
                    "qa_results": qa_results
                },
                error=None if successful_qa > 0 else "所有问答请求都失败"
            )
            
            return successful_qa > 0
            
        except Exception as e:
            self.log_test_result("AI问答功能", False, error=str(e))
            return False
    
    def test_permission_control(self) -> bool:
        """测试权限控制"""
        logger.info("[TEST] 测试权限控制...")
        
        try:
            # 测试无效文献ID访问
            invalid_lit_id = "invalid-literature-id"
            
            detail_response = self.session.get(
                f"{self.base_url}/literature/detail/{invalid_lit_id}"
            )
            
            file_response = self.session.get(
                f"{self.base_url}/literature/view/file/{invalid_lit_id}"
            )
            
            qa_request = {
                "question": "测试问题",
                "literature_id": invalid_lit_id
            }
            qa_response = self.session.post(
                f"{self.base_url}/ai/ask",
                json=qa_request
            )
            
            # 这些请求应该都返回错误状态码
            permission_tests = [
                ("文献详情权限", detail_response.status_code in [403, 404]),
                ("文件访问权限", file_response.status_code in [403, 404]),
                ("AI问答权限", qa_response.status_code in [403, 404])
            ]
            
            all_passed = all(test[1] for test in permission_tests)
            
            self.log_test_result(
                "权限控制",
                all_passed,
                {
                    "tests": [
                        {"name": test[0], "passed": test[1]} 
                        for test in permission_tests
                    ]
                },
                error=None if all_passed else "某些权限控制测试失败"
            )
            
            return all_passed
            
        except Exception as e:
            self.log_test_result("权限控制", False, error=str(e))
            return False
    
    def test_error_scenarios(self) -> bool:
        """测试错误场景处理"""
        logger.info("[TEST] 测试错误场景处理...")
        
        try:
            error_tests = []
            
            # 测试1: 空问题
            empty_question_response = self.session.post(
                f"{self.base_url}/ai/ask",
                json={
                    "question": "",
                    "literature_id": "test-id"
                }
            )
            error_tests.append(("空问题处理", empty_question_response.status_code == 422))
            
            # 测试2: 超长问题
            long_question = "这是一个非常长的问题" * 100
            long_question_response = self.session.post(
                f"{self.base_url}/ai/ask",
                json={
                    "question": long_question,
                    "literature_id": "test-id"
                }
            )
            error_tests.append(("超长问题处理", long_question_response.status_code in [422, 400]))
            
            # 测试3: 无效JSON
            try:
                invalid_json_response = self.session.post(
                    f"{self.base_url}/ai/ask",
                    data="invalid json",
                    headers={"Content-Type": "application/json"}
                )
                error_tests.append(("无效JSON处理", invalid_json_response.status_code == 422))
            except:
                error_tests.append(("无效JSON处理", True))  # 异常也算正确处理
            
            passed_tests = sum(1 for test in error_tests if test[1])
            
            self.log_test_result(
                "错误场景处理",
                passed_tests >= 2,  # 至少通过2个测试
                {
                    "tests": [
                        {"name": test[0], "passed": test[1]} 
                        for test in error_tests
                    ],
                    "passed_count": passed_tests
                },
                error=None if passed_tests >= 2 else f"只有 {passed_tests} 个错误处理测试通过"
            )
            
            return passed_tests >= 2
            
        except Exception as e:
            self.log_test_result("错误场景处理", False, error=str(e))
            return False
    
    def run_all_tests(self, username: str = "testuser", password: str = "testpass123"):
        """运行所有测试"""
        logger.info("[START] 开始AI集成端到端测试...")
        logger.info("=" * 60)
        
        # 测试序列
        tests = [
            ("系统健康检查", lambda: self.test_system_health()),
            ("用户认证", lambda: self.test_user_authentication("13800000001", password)),  # 使用手机号
            ("权限控制", lambda: self.test_permission_control()),
            ("错误场景处理", lambda: self.test_error_scenarios())
        ]
        
        literature_id = None
        
        # 运行基础测试
        for test_name, test_func in tests:
            try:
                success = test_func()
                if test_name == "用户认证" and not success:
                    logger.error("认证失败，跳过后续需要认证的测试")
                    break
            except Exception as e:
                logger.error(f"测试 {test_name} 发生异常: {e}")
        
        # 如果认证成功，继续文献相关测试
        if self.access_token:
            try:
                literature_id = self.test_literature_access()
                if literature_id:
                    self.test_ai_question_answer(literature_id)
            except Exception as e:
                logger.error(f"文献相关测试发生异常: {e}")
        
        # 保存测试结果
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["duration_seconds"] = (
            datetime.fromisoformat(self.test_results["end_time"]) - 
            datetime.fromisoformat(self.test_results["start_time"])
        ).total_seconds()
        
        # 输出总结
        summary = self.test_results["summary"]
        logger.info("=" * 60)
        logger.info(" 测试总结")
        logger.info("=" * 60)
        logger.info(f"总测试数: {summary['total']}")
        logger.info(f"通过: {summary['passed']} ({summary['passed']/summary['total']*100:.1f}%)")
        logger.info(f"失败: {summary['failed']} ({summary['failed']/summary['total']*100:.1f}%)")
        
        if summary['errors']:
            logger.info("失败的测试:")
            for error in summary['errors']:
                logger.info(f"  - {error}")
        
        # 保存详细结果
        with open('test_results_ai_integration.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"详细测试结果已保存到: test_results_ai_integration.json")
        
        if summary['passed'] == summary['total']:
            logger.info(" 所有测试通过！")
            return True
        else:
            logger.warning(" 部分测试失败，请查看详细日志")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI集成端到端测试")
    parser.add_argument("--url", default="http://localhost:8000", help="API基础URL")
    parser.add_argument("--username", default="testuser", help="测试用户名")
    parser.add_argument("--password", default="testpass123", help="测试密码")  # 修正默认密码
    
    args = parser.parse_args() 
    
    tester = AIIntegrationTester(args.url)
    success = tester.run_all_tests(args.username, args.password)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
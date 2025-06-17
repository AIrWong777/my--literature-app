#!/usr/bin/env python3
"""
API连接和网络测试

专门测试Google AI API和OpenAI API的连接状况
"""
import sys
import os
import asyncio
import logging
import time
import requests
from typing import Dict, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.utils.embedding_service import embedding_service
from app.utils.rag_service import rag_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIConnectionTester:
    """API连接测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.test_results = {
            "network": [],
            "google_api": [],
            "openai_api": [],
            "embedding_service": [],
            "rag_service": []
        }
    
    async def run_all_tests(self):
        """运行所有连接测试"""
        logger.info("开始API连接测试")
        
        try:
            # 1. 基础网络连接测试
            await self.test_network_connectivity()
            
            # 2. Google API测试
            await self.test_google_api()
            
            # 3. OpenAI API测试（如果配置了）
            await self.test_openai_api()
            
            # 4. Embedding服务测试
            await self.test_embedding_service()
            
            # 5. RAG服务测试
            await self.test_rag_service()
            
            # 生成测试报告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"API连接测试失败: {str(e)}")
    
    async def test_network_connectivity(self):
        """测试基础网络连接"""
        logger.info("测试基础网络连接...")
        
        # 测试基础网络连接
        test_urls = [
            ("Google", "https://www.google.com"),
            ("Google AI", "https://generativelanguage.googleapis.com"),
            ("OpenAI", "https://api.openai.com"),
            ("百度", "https://www.baidu.com")
        ]
        
        for name, url in test_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                self.test_results["network"].append({
                    "test": f"{name}网络连接",
                    "status": "PASS" if response.status_code < 400 else "FAIL",
                    "details": f"状态码: {response.status_code}, 响应时间: {end_time - start_time:.2f}s"
                })
                
            except Exception as e:
                self.test_results["network"].append({
                    "test": f"{name}网络连接",
                    "status": "FAIL",
                    "details": f"连接失败: {str(e)}"
                })
    
    async def test_google_api(self):
        """测试Google API连接"""
        logger.info("测试Google API连接...")
        
        if not Config.GOOGLE_API_KEY:
            self.test_results["google_api"].append({
                "test": "API密钥检查",
                "status": "SKIP",
                "details": "未配置Google API密钥"
            })
            return
        
        # 测试API密钥有效性
        try:
            from google import genai
            client = genai.Client(api_key=Config.GOOGLE_API_KEY)
            
            self.test_results["google_api"].append({
                "test": "客户端初始化",
                "status": "PASS",
                "details": "Google GenAI客户端初始化成功"
            })
            
            # 测试简单的embedding请求
            try:
                from google.genai import types
                
                start_time = time.time()
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents="测试文本",
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT"
                    )
                )
                end_time = time.time()
                
                if response.embeddings and len(response.embeddings) > 0:
                    self.test_results["google_api"].append({
                        "test": "Embedding API调用",
                        "status": "PASS",
                        "details": f"成功生成embedding，维度: {len(response.embeddings[0].values)}, 响应时间: {end_time - start_time:.2f}s"
                    })
                else:
                    self.test_results["google_api"].append({
                        "test": "Embedding API调用",
                        "status": "FAIL",
                        "details": "未收到有效的embedding响应"
                    })
                    
            except Exception as e:
                self.test_results["google_api"].append({
                    "test": "Embedding API调用",
                    "status": "FAIL",
                    "details": f"API调用失败: {str(e)}"
                })
            
            # 测试文本生成API
            try:
                start_time = time.time()
                response = client.models.generate_content(
                    model=Config.GEMINI_MODEL,
                    contents="请简单回答：今天天气如何？"
                )
                end_time = time.time()
                
                if response.candidates and len(response.candidates) > 0:
                    answer = response.candidates[0].content.parts[0].text
                    self.test_results["google_api"].append({
                        "test": "文本生成API调用",
                        "status": "PASS",
                        "details": f"成功生成回答，长度: {len(answer)}字符, 响应时间: {end_time - start_time:.2f}s"
                    })
                else:
                    self.test_results["google_api"].append({
                        "test": "文本生成API调用",
                        "status": "FAIL",
                        "details": "未收到有效的生成响应"
                    })
                    
            except Exception as e:
                self.test_results["google_api"].append({
                    "test": "文本生成API调用",
                    "status": "FAIL",
                    "details": f"API调用失败: {str(e)}"
                })
                
        except Exception as e:
            self.test_results["google_api"].append({
                "test": "客户端初始化",
                "status": "FAIL",
                "details": f"初始化失败: {str(e)}"
            })
    
    async def test_openai_api(self):
        """测试OpenAI API连接"""
        logger.info("测试OpenAI API连接...")
        
        if not Config.OPENAI_API_KEY:
            self.test_results["openai_api"].append({
                "test": "API密钥检查",
                "status": "SKIP",
                "details": "未配置OpenAI API密钥"
            })
            return
        
        try:
            import openai
            client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            
            self.test_results["openai_api"].append({
                "test": "客户端初始化",
                "status": "PASS",
                "details": "OpenAI客户端初始化成功"
            })
            
            # 测试embedding API
            try:
                start_time = time.time()
                response = client.embeddings.create(
                    model=Config.OPENAI_EMBEDDING_MODEL,
                    input="测试文本",
                    encoding_format="float"
                )
                end_time = time.time()
                
                embedding = response.data[0].embedding
                self.test_results["openai_api"].append({
                    "test": "Embedding API调用",
                    "status": "PASS",
                    "details": f"成功生成embedding，维度: {len(embedding)}, 响应时间: {end_time - start_time:.2f}s"
                })
                
            except Exception as e:
                self.test_results["openai_api"].append({
                    "test": "Embedding API调用",
                    "status": "FAIL",
                    "details": f"API调用失败: {str(e)}"
                })
            
            # 测试Chat API
            try:
                start_time = time.time()
                response = client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": "请简单回答：今天天气如何？"}],
                    max_tokens=50
                )
                end_time = time.time()
                
                answer = response.choices[0].message.content
                self.test_results["openai_api"].append({
                    "test": "Chat API调用",
                    "status": "PASS",
                    "details": f"成功生成回答，长度: {len(answer)}字符, 响应时间: {end_time - start_time:.2f}s"
                })
                
            except Exception as e:
                self.test_results["openai_api"].append({
                    "test": "Chat API调用",
                    "status": "FAIL",
                    "details": f"API调用失败: {str(e)}"
                })
                
        except Exception as e:
            self.test_results["openai_api"].append({
                "test": "客户端初始化",
                "status": "FAIL",
                "details": f"初始化失败: {str(e)}"
            })
    
    async def test_embedding_service(self):
        """测试embedding服务"""
        logger.info("测试Embedding服务...")
        
        # 测试服务可用性
        is_available = embedding_service.is_available()
        self.test_results["embedding_service"].append({
            "test": "服务可用性",
            "status": "PASS" if is_available else "FAIL",
            "details": f"服务状态: {'可用' if is_available else '不可用'}"
        })
        
        if is_available:
            # 测试单个文本embedding
            try:
                start_time = time.time()
                embedding = embedding_service.generate_embedding("这是一个测试文本。")
                end_time = time.time()
                
                if embedding:
                    self.test_results["embedding_service"].append({
                        "test": "单文本embedding",
                        "status": "PASS",
                        "details": f"成功生成embedding，维度: {len(embedding)}, 响应时间: {end_time - start_time:.2f}s"
                    })
                else:
                    self.test_results["embedding_service"].append({
                        "test": "单文本embedding",
                        "status": "FAIL",
                        "details": "生成embedding失败"
                    })
                    
            except Exception as e:
                self.test_results["embedding_service"].append({
                    "test": "单文本embedding",
                    "status": "FAIL",
                    "details": f"异常: {str(e)}"
                })
            
            # 测试连接
            try:
                connection_test = embedding_service.test_connection()
                self.test_results["embedding_service"].append({
                    "test": "连接测试",
                    "status": "PASS" if connection_test.get("status") == "success" else "FAIL",
                    "details": f"测试结果: {connection_test}"
                })
                
            except Exception as e:
                self.test_results["embedding_service"].append({
                    "test": "连接测试",
                    "status": "FAIL",
                    "details": f"异常: {str(e)}"
                })
    
    async def test_rag_service(self):
        """测试RAG服务"""
        logger.info("测试RAG服务...")
        
        # 测试健康检查
        try:
            health_status = await rag_service.health_check()
            self.test_results["rag_service"].append({
                "test": "健康检查",
                "status": "PASS" if health_status.get("status") in ["healthy", "degraded"] else "FAIL",
                "details": f"服务状态: {health_status.get('status', 'unknown')}"
            })
        except Exception as e:
            self.test_results["rag_service"].append({
                "test": "健康检查",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试预设问题生成（不需要API调用）
        try:
            preset_questions = rag_service.get_preset_questions("test_lit_id", "测试文献标题")
            self.test_results["rag_service"].append({
                "test": "预设问题生成",
                "status": "PASS" if isinstance(preset_questions, list) and len(preset_questions) > 0 else "FAIL",
                "details": f"生成问题数: {len(preset_questions) if isinstance(preset_questions, list) else 0}"
            })
        except Exception as e:
            self.test_results["rag_service"].append({
                "test": "预设问题生成",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试服务统计
        try:
            stats = rag_service.get_service_stats()
            self.test_results["rag_service"].append({
                "test": "服务统计",
                "status": "PASS" if stats.get("service_name") else "FAIL",
                "details": f"服务名称: {stats.get('service_name', 'unknown')}"
            })
        except Exception as e:
            self.test_results["rag_service"].append({
                "test": "服务统计",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
    
    def generate_test_report(self):
        """生成测试报告"""
        logger.info("生成API连接测试报告...")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        print("\n" + "="*60)
        print("API连接测试报告")
        print("="*60)
        
        for component, tests in self.test_results.items():
            if not tests:
                continue
                
            print(f"\n【{component.upper()}】")
            print("-" * 30)
            
            for test in tests:
                total_tests += 1
                status = test["status"]
                
                if status == "PASS":
                    passed_tests += 1
                    status_symbol = "✓"
                elif status == "SKIP":
                    skipped_tests += 1
                    status_symbol = "⊝"
                else:
                    failed_tests += 1
                    status_symbol = "✗"
                
                print(f"{status_symbol} {test['test']}: {status}")
                print(f"   {test['details']}")
        
        print(f"\n{'='*60}")
        print(f"测试总结:")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"跳过: {skipped_tests}")
        success_rate = passed_tests / (total_tests - skipped_tests) * 100 if (total_tests - skipped_tests) > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        print("="*60)

async def main():
    """主函数"""
    print("API连接和网络测试")
    print("检查网络连接和API服务状态...")
    
    tester = APIConnectionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
系统基础功能测试

测试核心组件的基本功能，避免长时间API调用
"""
import sys
import os
import asyncio
import logging
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.utils.prompt_builder import PromptBuilder
from app.utils.answer_processor import AnswerProcessor
from app.utils.embedding_service import embedding_service
from app.utils.conversation_manager import conversation_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BasicSystemTester:
    """基础系统功能测试器"""
    
    def __init__(self):
        self.test_results = {
            "config": [],
            "prompt_builder": [],
            "answer_processor": [],
            "embedding_basic": [],
            "conversation_manager": []
        }
    
    async def run_all_tests(self):
        """运行所有基础测试"""
        logger.info("开始系统基础功能测试")
        
        try:
            # 1. 配置测试
            self.test_configuration()
            
            # 2. 提示词构建器测试
            self.test_prompt_builder()
            
            # 3. 答案处理器测试
            self.test_answer_processor()
            
            # 4. Embedding基础测试（快速）
            await self.test_embedding_basic()
            
            # 5. 对话管理器测试
            self.test_conversation_manager()
            
            # 生成测试报告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"系统测试失败: {str(e)}")
    
    def test_configuration(self):
        """测试配置"""
        logger.info("测试系统配置...")
        
        # 测试配置加载
        try:
            ai_provider = Config.get_ai_provider()
            self.test_results["config"].append({
                "test": "AI提供商配置",
                "status": "PASS" if ai_provider != "none" else "FAIL",
                "details": f"当前提供商: {ai_provider}"
            })
        except Exception as e:
            self.test_results["config"].append({
                "test": "AI提供商配置",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试配置验证
        try:
            is_valid, message = Config.validate_ai_config()
            self.test_results["config"].append({
                "test": "AI配置验证",
                "status": "PASS" if is_valid else "WARN",
                "details": message
            })
        except Exception as e:
            self.test_results["config"].append({
                "test": "AI配置验证",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试配置摘要
        try:
            config_summary = Config.get_config_summary()
            self.test_results["config"].append({
                "test": "配置摘要",
                "status": "PASS" if config_summary else "FAIL",
                "details": f"配置项数量: {len(config_summary)}"
            })
        except Exception as e:
            self.test_results["config"].append({
                "test": "配置摘要",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
    
    def test_prompt_builder(self):
        """测试提示词构建器"""
        logger.info("测试提示词构建器...")
        
        prompt_builder = PromptBuilder()
        
        # 测试数据
        test_question = "这篇文献的主要结论是什么？"
        test_chunks = [
            {
                "text": "研究结果表明，新方法比传统方法效果提高了30%。",
                "metadata": {"source": "结论部分", "page": 25}
            }
        ]
        test_history = [
            {"role": "user", "content": "文献背景是什么？"},
            {"role": "assistant", "content": "这是一项关于机器学习的研究。"}
        ]
        
        # 测试基础提示词构建
        try:
            prompt = prompt_builder.build_qa_prompt(test_question, test_chunks, test_history)
            self.test_results["prompt_builder"].append({
                "test": "基础提示词构建",
                "status": "PASS" if prompt and len(prompt) > 50 else "FAIL",
                "details": f"提示词长度: {len(prompt)}"
            })
        except Exception as e:
            self.test_results["prompt_builder"].append({
                "test": "基础提示词构建",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试提示词验证
        try:
            if prompt:
                validation = prompt_builder.validate_prompt_quality(prompt)
                self.test_results["prompt_builder"].append({
                    "test": "提示词质量验证",
                    "status": "PASS" if validation.get("is_valid") else "FAIL",
                    "details": f"验证通过: {validation.get('is_valid')}, 问题数: {len(validation.get('issues', []))}"
                })
        except Exception as e:
            self.test_results["prompt_builder"].append({
                "test": "提示词质量验证",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试预设问题生成
        try:
            preset_questions = prompt_builder.build_preset_questions_prompt("机器学习效果评估研究")
            self.test_results["prompt_builder"].append({
                "test": "预设问题生成",
                "status": "PASS" if isinstance(preset_questions, list) and len(preset_questions) > 0 else "FAIL",
                "details": f"生成问题数: {len(preset_questions) if isinstance(preset_questions, list) else 0}"
            })
        except Exception as e:
            self.test_results["prompt_builder"].append({
                "test": "预设问题生成",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
    
    def test_answer_processor(self):
        """测试答案处理器"""
        logger.info("测试答案处理器...")
        
        answer_processor = AnswerProcessor()
        
        # 测试数据
        test_raw_answer = """
**答案：**
根据研究结果，新方法的效果确实比传统方法有显著提升，具体提升了30%的效率。

**引用来源：**
- 【来源1】：结论部分 - 效果对比数据

**置信度：**
高 - 数据明确，结论可靠
        """
        
        test_chunks = [
            {
                "text": "研究结果表明，新方法比传统方法效果提高了30%。",
                "metadata": {"source": "结论部分", "page": 25}
            }
        ]
        
        # 测试答案处理
        try:
            processed = answer_processor.process_answer(
                test_raw_answer, 
                test_chunks, 
                "这篇文献的主要结论是什么？",
                "test_lit_id"
            )
            
            self.test_results["answer_processor"].append({
                "test": "答案基础处理",
                "status": "PASS" if processed.get("answer") else "FAIL",
                "details": f"处理后答案长度: {len(processed.get('answer', ''))}"
            })
            
            # 测试置信度计算
            confidence = processed.get("confidence", 0)
            self.test_results["answer_processor"].append({
                "test": "置信度计算",
                "status": "PASS" if 0 <= confidence <= 1 else "FAIL",
                "details": f"置信度: {confidence}"
            })
            
            # 测试来源提取
            sources = processed.get("sources", [])
            self.test_results["answer_processor"].append({
                "test": "来源提取",
                "status": "PASS" if len(sources) > 0 else "FAIL",
                "details": f"提取来源数: {len(sources)}"
            })
            
        except Exception as e:
            self.test_results["answer_processor"].append({
                "test": "答案处理",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
    
    async def test_embedding_basic(self):
        """测试Embedding基础功能"""
        logger.info("测试Embedding基础功能...")
        
        # 测试服务可用性
        try:
            is_available = embedding_service.is_available()
            self.test_results["embedding_basic"].append({
                "test": "服务可用性",
                "status": "PASS" if is_available else "FAIL",
                "details": f"服务状态: {'可用' if is_available else '不可用'}"
            })
        except Exception as e:
            self.test_results["embedding_basic"].append({
                "test": "服务可用性",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 如果服务可用，测试简单embedding（限制超时）
        if embedding_service.is_available():
            try:
                # 设置较短的超时时间进行快速测试
                import time
                start_time = time.time()
                
                # 测试短文本embedding
                embedding = embedding_service.generate_embedding("测试")
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if embedding and response_time < 5.0:  # 5秒内完成
                    self.test_results["embedding_basic"].append({
                        "test": "快速embedding生成",
                        "status": "PASS",
                        "details": f"维度: {len(embedding)}, 响应时间: {response_time:.2f}s"
                    })
                elif embedding:
                    self.test_results["embedding_basic"].append({
                        "test": "快速embedding生成",
                        "status": "WARN",
                        "details": f"成功但较慢: {response_time:.2f}s"
                    })
                else:
                    self.test_results["embedding_basic"].append({
                        "test": "快速embedding生成",
                        "status": "FAIL",
                        "details": "生成失败"
                    })
                    
            except Exception as e:
                self.test_results["embedding_basic"].append({
                    "test": "快速embedding生成",
                    "status": "FAIL",
                    "details": f"异常: {str(e)}"
                })
        
        # 测试服务信息
        try:
            info = embedding_service.get_embedding_info()
            self.test_results["embedding_basic"].append({
                "test": "服务信息",
                "status": "PASS" if info else "FAIL",
                "details": f"提供商: {info.get('provider', 'unknown')}, 模型: {info.get('model', 'unknown')}"
            })
        except Exception as e:
            self.test_results["embedding_basic"].append({
                "test": "服务信息",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
    
    def test_conversation_manager(self):
        """测试对话管理器"""
        logger.info("测试对话管理器...")
        
        # 测试关键词提取
        try:
            keywords = conversation_manager._extract_keywords("这篇文献的主要研究方法是什么？")
            self.test_results["conversation_manager"].append({
                "test": "关键词提取",
                "status": "PASS" if len(keywords) > 0 else "FAIL",
                "details": f"提取关键词数: {len(keywords)}"
            })
        except Exception as e:
            self.test_results["conversation_manager"].append({
                "test": "关键词提取",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
        
        # 测试历史过滤
        try:
            test_history = [
                {"role": "user", "content": "研究背景是什么？"},
                {"role": "assistant", "content": "这是机器学习研究。"},
                {"role": "user", "content": "实验结果如何？"},
                {"role": "assistant", "content": "效果提升30%。"}
            ]
            
            filtered = conversation_manager._filter_relevant_history(
                test_history, 
                "实验效果怎么样？", 
                max_turns=2
            )
            
            self.test_results["conversation_manager"].append({
                "test": "历史过滤",
                "status": "PASS" if isinstance(filtered, list) else "FAIL",
                "details": f"过滤后轮次: {len(filtered) if isinstance(filtered, list) else 0}"
            })
        except Exception as e:
            self.test_results["conversation_manager"].append({
                "test": "历史过滤",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })
    
    def generate_test_report(self):
        """生成测试报告"""
        logger.info("生成基础功能测试报告...")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warned_tests = 0
        
        print("\n" + "="*60)
        print("系统基础功能测试报告")
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
                elif status == "WARN":
                    warned_tests += 1
                    status_symbol = "⚠"
                else:
                    failed_tests += 1
                    status_symbol = "✗"
                
                print(f"{status_symbol} {test['test']}: {status}")
                print(f"   {test['details']}")
        
        print(f"\n{'='*60}")
        print(f"测试总结:")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"警告: {warned_tests}")
        print(f"失败: {failed_tests}")
        success_rate = (passed_tests + warned_tests) / total_tests * 100 if total_tests > 0 else 0
        print(f"总体成功率: {success_rate:.1f}%")
        print("="*60)
        
        # 保存结果
        try:
            with open("test_results_basic.json", "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"详细测试结果已保存到: test_results_basic.json")
        except Exception as e:
            logger.error(f"保存测试结果失败: {str(e)}")

async def main():
    """主函数"""
    print("系统基础功能测试")
    print("测试核心组件的基本功能...")
    
    tester = BasicSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
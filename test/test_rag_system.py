#!/usr/bin/env python3
"""
RAG问答系统综合测试

测试RAG系统的各个组件和完整流程
"""
import sys
import os
import asyncio
import logging
from typing import Dict, List
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.utils.prompt_builder import PromptBuilder
from app.utils.answer_processor import AnswerProcessor
from app.utils.rag_service import rag_service
from app.utils.conversation_manager import conversation_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGSystemTester:
    """RAG系统测试类"""
    
    def __init__(self):
        """初始化测试器"""
        self.test_results = {
            "prompt_builder": [],
            "answer_processor": [],
            "rag_service": [],
            "conversation_manager": [],
            "integration": []
        }
        
        self.prompt_builder = PromptBuilder()
        self.answer_processor = AnswerProcessor()
        
        # 测试数据
        self.test_question = "这篇文献的主要研究方法是什么？"
        self.test_context_chunks = [
            {
                "chunk_id": "test_chunk_1",
                "text": "本研究采用了定量分析的方法，通过问卷调查收集了500名参与者的数据。我们使用了SPSS软件进行统计分析，包括描述性统计、相关分析和回归分析。",
                "similarity": 0.85,
                "metadata": {
                    "source": "第3章 研究方法",
                    "page": 15,
                    "chunk_index": 5
                }
            },
            {
                "chunk_id": "test_chunk_2", 
                "text": "研究采用混合方法设计，结合定量和定性分析。定量部分包括结构化问卷，定性部分包括深度访谈。数据分析使用了多元统计方法。",
                "similarity": 0.82,
                "metadata": {
                    "source": "第2章 文献综述",
                    "page": 8,
                    "chunk_index": 3
                }
            }
        ]
        
        self.test_conversation_history = [
            {
                "role": "user",
                "content": "这篇文献的研究背景是什么？",
                "timestamp": "2024-01-01T10:00:00"
            },
            {
                "role": "assistant",
                "content": "根据文献内容，研究背景主要涉及当前领域的理论空白和实践需求。",
                "timestamp": "2024-01-01T10:00:30",
                "confidence": 0.75
            }
        ]

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始RAG系统综合测试")
        
        try:
            # 1. 测试提示词构建器
            await self.test_prompt_builder()
            
            # 2. 测试答案处理器
            await self.test_answer_processor()
            
            # 3. 测试RAG服务
            await self.test_rag_service()
            
            # 4. 测试对话管理器
            await self.test_conversation_manager()
            
            # 5. 集成测试
            await self.test_integration()
            
            # 生成测试报告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"测试执行失败: {str(e)}")

    async def test_prompt_builder(self):
        """测试提示词构建器"""
        logger.info("测试提示词构建器...")
        
        try:
            # 测试基础问答提示词构建
            prompt = self.prompt_builder.build_qa_prompt(
                self.test_question,
                self.test_context_chunks,
                self.test_conversation_history
            )
            
            self.test_results["prompt_builder"].append({
                "test": "基础问答提示词构建",
                "status": "PASS" if prompt and len(prompt) > 100 else "FAIL",
                "details": f"生成提示词长度: {len(prompt)}"
            })
            
            # 测试提示词质量验证
            validation = self.prompt_builder.validate_prompt_quality(prompt)
            
            self.test_results["prompt_builder"].append({
                "test": "提示词质量验证",
                "status": "PASS" if validation["is_valid"] else "FAIL",
                "details": f"验证结果: {validation}"
            })
            
            # 测试预设问题生成
            preset_questions = self.prompt_builder.build_preset_questions_prompt("机器学习在医疗诊断中的应用研究")
            
            self.test_results["prompt_builder"].append({
                "test": "预设问题生成",
                "status": "PASS" if isinstance(preset_questions, list) and len(preset_questions) > 0 else "FAIL",
                "details": f"生成问题数量: {len(preset_questions) if isinstance(preset_questions, list) else 0}"
            })
            
            # 测试Token估算
            tokens = self.prompt_builder._estimate_tokens(prompt)
            
            self.test_results["prompt_builder"].append({
                "test": "Token估算",
                "status": "PASS" if tokens > 0 else "FAIL",
                "details": f"估算Token数: {tokens}"
            })
            
            logger.info("提示词构建器测试完成")
            
        except Exception as e:
            logger.error(f"提示词构建器测试失败: {str(e)}")
            self.test_results["prompt_builder"].append({
                "test": "全部测试",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })

    async def test_answer_processor(self):
        """测试答案处理器"""
        logger.info("测试答案处理器...")
        
        try:
            # 模拟AI回答
            raw_answer = """
**答案：**
根据提供的文献内容，这篇研究主要采用了混合方法设计，具体包括：

1. **定量分析方法**：通过结构化问卷调查收集了500名参与者的数据，使用SPSS软件进行统计分析，包括描述性统计、相关分析和回归分析。

2. **定性分析方法**：结合深度访谈的方式收集定性数据，以获得更深入的见解。

3. **多元统计方法**：在数据分析阶段使用了多元统计技术来处理复杂的数据关系。

**引用来源：**
- 【来源1】：第3章 研究方法 - 定量分析方法描述
- 【来源2】：第2章 文献综述 - 混合方法设计说明

**置信度：**
高 - 文献中明确描述了研究方法，信息完整且详细
            """
            
            # 测试答案处理
            processed_answer = self.answer_processor.process_answer(
                raw_answer,
                self.test_context_chunks,
                self.test_question,
                "test_literature_id"
            )
            
            self.test_results["answer_processor"].append({
                "test": "答案基础处理",
                "status": "PASS" if processed_answer.get("answer") else "FAIL",
                "details": f"处理后答案长度: {len(processed_answer.get('answer', ''))}"
            })
            
            # 测试引用来源提取
            sources = processed_answer.get("sources", [])
            
            self.test_results["answer_processor"].append({
                "test": "引用来源提取",
                "status": "PASS" if len(sources) > 0 else "FAIL",
                "details": f"提取到 {len(sources)} 个引用来源"
            })
            
            # 测试置信度计算
            confidence = processed_answer.get("confidence", 0)
            
            self.test_results["answer_processor"].append({
                "test": "置信度计算",
                "status": "PASS" if 0 <= confidence <= 1 else "FAIL",
                "details": f"置信度: {confidence}"
            })
            
            # 测试质量评分
            quality_score = processed_answer.get("quality_score", {})
            
            self.test_results["answer_processor"].append({
                "test": "质量评分计算",
                "status": "PASS" if isinstance(quality_score, dict) and len(quality_score) > 0 else "FAIL",
                "details": f"质量评分维度数: {len(quality_score)}"
            })
            
            logger.info("答案处理器测试完成")
            
        except Exception as e:
            logger.error(f"答案处理器测试失败: {str(e)}")
            self.test_results["answer_processor"].append({
                "test": "全部测试",
                "status": "FAIL", 
                "details": f"异常: {str(e)}"
            })

    async def test_rag_service(self):
        """测试RAG服务"""
        logger.info("测试RAG服务...")
        
        try:
            # 测试健康检查
            health_status = await rag_service.health_check()
            
            self.test_results["rag_service"].append({
                "test": "健康检查",
                "status": "PASS" if health_status.get("status") == "healthy" else "DEGRADED",
                "details": f"服务状态: {health_status.get('status', 'unknown')}"
            })
            
            # 测试服务统计
            stats = rag_service.get_service_stats()
            
            self.test_results["rag_service"].append({
                "test": "服务统计",
                "status": "PASS" if stats.get("service_name") else "FAIL",
                "details": f"服务名称: {stats.get('service_name', 'unknown')}"
            })
            
            # 测试预设问题生成
            preset_questions = rag_service.get_preset_questions("test_lit_id", "测试文献标题")
            
            self.test_results["rag_service"].append({
                "test": "预设问题生成",
                "status": "PASS" if isinstance(preset_questions, list) and len(preset_questions) > 0 else "FAIL",
                "details": f"生成问题数: {len(preset_questions) if isinstance(preset_questions, list) else 0}"
            })
            
            logger.info("RAG服务测试完成")
            
        except Exception as e:
            logger.error(f"RAG服务测试失败: {str(e)}")
            self.test_results["rag_service"].append({
                "test": "全部测试",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })

    async def test_conversation_manager(self):
        """测试对话管理器"""
        logger.info("测试对话管理器...")
        
        try:
            # 测试关键词提取
            keywords = conversation_manager._extract_keywords(self.test_question)
            
            self.test_results["conversation_manager"].append({
                "test": "关键词提取",
                "status": "PASS" if len(keywords) > 0 else "FAIL",
                "details": f"提取关键词: {keywords}"
            })
            
            # 测试历史过滤
            relevant_history = conversation_manager._filter_relevant_history(
                self.test_conversation_history,
                self.test_question,
                3
            )
            
            self.test_results["conversation_manager"].append({
                "test": "相关历史过滤",
                "status": "PASS" if isinstance(relevant_history, list) else "FAIL",
                "details": f"过滤后历史长度: {len(relevant_history) if isinstance(relevant_history, list) else 0}"
            })
            
            logger.info("对话管理器测试完成")
            
        except Exception as e:
            logger.error(f"对话管理器测试失败: {str(e)}")
            self.test_results["conversation_manager"].append({
                "test": "全部测试",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })

    async def test_integration(self):
        """集成测试"""
        logger.info("开始集成测试...")
        
        try:
            # 测试完整的提示词到答案的流程
            # 1. 构建提示词
            prompt = self.prompt_builder.build_qa_prompt(
                self.test_question,
                self.test_context_chunks,
                self.test_conversation_history
            )
            
            # 2. 模拟AI响应
            mock_ai_response = """
**答案：**
这篇文献主要采用了混合研究方法，结合了定量和定性两种分析方式。

**引用来源：**
- 【来源1】：第3章描述了定量分析方法
- 【来源2】：第2章说明了混合方法设计

**置信度：**
高 - 文献中有明确的方法描述
            """
            
            # 3. 处理答案
            processed_answer = self.answer_processor.process_answer(
                mock_ai_response,
                self.test_context_chunks,
                self.test_question,
                "test_literature_id"
            )
            
            # 验证集成结果
            integration_success = (
                prompt and len(prompt) > 0 and
                processed_answer.get("answer") and
                processed_answer.get("confidence", 0) > 0 and
                len(processed_answer.get("sources", [])) > 0
            )
            
            self.test_results["integration"].append({
                "test": "完整RAG流程",
                "status": "PASS" if integration_success else "FAIL",
                "details": {
                    "prompt_length": len(prompt),
                    "answer_length": len(processed_answer.get("answer", "")),
                    "confidence": processed_answer.get("confidence", 0),
                    "sources_count": len(processed_answer.get("sources", []))
                }
            })
            
            logger.info("集成测试完成")
            
        except Exception as e:
            logger.error(f"集成测试失败: {str(e)}")
            self.test_results["integration"].append({
                "test": "完整RAG流程",
                "status": "FAIL",
                "details": f"异常: {str(e)}"
            })

    def generate_test_report(self):
        """生成测试报告"""
        logger.info("生成测试报告...")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        print("\n" + "="*60)
        print("RAG问答系统测试报告")
        print("="*60)
        
        for component, tests in self.test_results.items():
            print(f"\n【{component.upper()}】")
            print("-" * 30)
            
            for test in tests:
                total_tests += 1
                status = test["status"]
                if status == "PASS":
                    passed_tests += 1
                    status_symbol = "✓"
                else:
                    failed_tests += 1
                    status_symbol = "✗"
                
                print(f"{status_symbol} {test['test']}: {status}")
                if isinstance(test["details"], dict):
                    for key, value in test["details"].items():
                        print(f"   {key}: {value}")
                else:
                    print(f"   {test['details']}")
        
        print(f"\n{'='*60}")
        print(f"测试总结:")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "0%")
        print("="*60)
        
        # 保存详细结果到文件
        try:
            with open("test_results_rag.json", "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"详细测试结果已保存到: test_results_rag.json")
        except Exception as e:
            logger.error(f"保存测试结果失败: {str(e)}")

async def main():
    """主函数"""
    print("RAG问答系统综合测试")
    print("测试环境检查...")
    
    # 检查配置
    try:
        if not Config.GOOGLE_API_KEY:
            print("⚠️  警告: 未配置Google AI API密钥，某些测试可能失败")
        else:
            print("✓ Google AI API密钥已配置")
        
        print(f"✓ 最大上下文Token数: {Config.RAG_MAX_CONTEXT_TOKENS}")
        print(f"✓ 检索数量: {Config.RAG_TOP_K_RETRIEVAL}")
        
    except Exception as e:
        print(f"✗ 配置检查失败: {str(e)}")
    
    # 运行测试
    tester = RAGSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
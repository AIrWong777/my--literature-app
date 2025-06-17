#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI回答质量测试脚本
用于验证修复后的AI回答质量
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.rag_service import RAGService
from app.utils.vector_store import VectorStore
from app.utils.prompt_builder import PromptBuilder
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ai_quality():
    """测试AI回答质量"""
    
    # 初始化服务
    rag_service = RAGService()
    
    # 测试问题列表
    test_questions = [
        "文献中使用了哪些研究方法？",
        "实验的主要结论是什么？",
        "作者采用了什么样的实验设计？",
        "研究中提到了哪些关键技术？",
        "文献的研究背景是什么？"
    ]
    
    # 需要指定一个实际的文献ID和组ID进行测试
    literature_id = "cd398a81-238d-4463-87e6-edcbe33a0dbe"  # 从日志中获取
    group_id = "private"  # 使用private组ID，这是从日志中看到的实际组ID
    
    logger.info("开始AI质量测试...")
    
    for i, question in enumerate(test_questions, 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"测试 {i}/5: {question}")
        logger.info(f"{'='*50}")
        
        try:
            # 处理问题
            result = await rag_service.process_question(
                question=question,
                literature_id=literature_id,
                group_id=group_id,
                top_k=5
            )
            
            # 分析结果质量
            if result and result.get("answer"):
                answer = result["answer"]
                
                # 质量指标
                answer_length = len(answer)
                has_sources = "来源" in answer
                has_confidence = "置信度" in answer
                
                # 检查是否包含乱码
                garbage_count = answer.count("[fOMN-_Ã")
                
                logger.info(f"回答长度: {answer_length}")
                logger.info(f"包含来源信息: {has_sources}")
                logger.info(f"包含置信度: {has_confidence}")
                logger.info(f"乱码数量: {garbage_count}")
                
                # 显示回答内容（截取前200字符）
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                logger.info(f"回答预览:\n{preview}")
                
                # 质量评估
                quality_score = 0
                if answer_length > 50:
                    quality_score += 1
                if has_sources:
                    quality_score += 1
                if has_confidence:
                    quality_score += 1
                if garbage_count == 0:
                    quality_score += 1
                if "抱歉" not in answer and "无法" not in answer:
                    quality_score += 1
                
                logger.info(f"质量评分: {quality_score}/5")
                
            else:
                logger.error("未获得有效回答")
                
        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
        
        # 添加延迟避免频繁请求
        await asyncio.sleep(2)
    
    logger.info("\n测试完成!")

def test_text_cleaning():
    """测试文本清理功能"""
    logger.info("测试文本清理功能...")
    
    prompt_builder = PromptBuilder()
    
    # 测试乱码文本
    garbage_text = "[fOMN-_Ã[fOMºe(ÏvÑmK^sSð  743202358  20250512这是一段包含乱码的文本"
    cleaned = prompt_builder._clean_text(garbage_text)
    
    logger.info(f"原文: {garbage_text}")
    logger.info(f"清理后: {cleaned}")
    logger.info(f"清理效果: {'✓' if '[fOMN' not in cleaned else '✗'}")

if __name__ == "__main__":
    # 测试文本清理
    test_text_cleaning()
    
    # 测试AI质量（需要确保服务运行）
    print("\n是否要测试AI回答质量？(需要确保服务正在运行) [y/N]: ", end="")
    if input().lower() == 'y':
        asyncio.run(test_ai_quality()) 
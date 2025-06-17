#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高层次问题测试脚本
测试AI对论文主要论点、创新点等高层次问题的回答质量
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.rag_service import RAGService
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_high_level_questions():
    """测试高层次问题回答质量"""
    
    # 初始化服务
    rag_service = RAGService()
    
    # 高层次测试问题
    high_level_questions = [
        "这篇文献的主要论点是什么？",
        "这项研究有什么创新点和贡献？", 
        "文献的研究背景是什么？",
        "作者提出了什么新的理论或方法？",
        "这项研究解决了什么问题？",
        "研究的主要发现和结论是什么？",
        "这项工作的理论意义和实际应用价值是什么？"
    ]
    
    # 使用实际的文献ID
    literature_id = "9d6b6860-22da-481e-be6c-482be2327e6b"  # 从日志中获取
    group_id = "private"
    
    logger.info("开始高层次问题测试...")
    logger.info(f"文献ID: {literature_id}")
    logger.info(f"测试问题数量: {len(high_level_questions)}")
    
    results = []
    
    for i, question in enumerate(high_level_questions, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"测试 {i}/{len(high_level_questions)}: {question}")
        logger.info(f"{'='*60}")
        
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
                
                # 检查是否是无效回答
                is_invalid_response = any(phrase in answer for phrase in [
                    "抱歉", "无法回答", "无法确定", "我无法", "根据提供的文献内容，我无法"
                ])
                
                # 检查是否包含实质性内容
                has_substantial_content = any(keyword in answer for keyword in [
                    "研究", "方法", "结果", "发现", "分析", "实验", "理论", "模型",
                    "创新", "贡献", "意义", "目的", "背景", "问题", "解决"
                ])
                
                logger.info(f"回答长度: {answer_length}")
                logger.info(f"包含来源信息: {has_sources}")
                logger.info(f"包含置信度: {has_confidence}")
                logger.info(f"是无效回答: {is_invalid_response}")
                logger.info(f"包含实质性内容: {has_substantial_content}")
                
                # 显示回答内容
                preview = answer[:300] + "..." if len(answer) > 300 else answer
                logger.info(f"回答预览:\n{preview}")
                
                # 质量评分
                quality_score = 0
                if answer_length > 50:
                    quality_score += 1
                if has_sources:
                    quality_score += 1
                if has_confidence:
                    quality_score += 1
                if not is_invalid_response:
                    quality_score += 1
                if has_substantial_content:
                    quality_score += 1
                
                logger.info(f"质量评分: {quality_score}/5")
                
                # 记录结果
                results.append({
                    "question": question,
                    "answer_length": answer_length,
                    "has_sources": has_sources,
                    "has_confidence": has_confidence,
                    "is_invalid": is_invalid_response,
                    "has_content": has_substantial_content,
                    "quality_score": quality_score,
                    "answer_preview": preview
                })
                
            else:
                logger.error("未获得有效回答")
                results.append({
                    "question": question,
                    "quality_score": 0,
                    "error": "未获得回答"
                })
                
        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
            results.append({
                "question": question,
                "quality_score": 0,
                "error": str(e)
            })
        
        # 添加延迟避免频繁请求
        await asyncio.sleep(3)
    
    # 汇总结果
    logger.info(f"\n{'='*60}")
    logger.info("测试结果汇总")
    logger.info(f"{'='*60}")
    
    total_score = sum(r.get("quality_score", 0) for r in results)
    max_score = len(results) * 5
    average_score = total_score / len(results) if results else 0
    
    logger.info(f"总分: {total_score}/{max_score}")
    logger.info(f"平均分: {average_score:.2f}/5")
    
    # 统计各项指标
    valid_answers = sum(1 for r in results if not r.get("is_invalid", True))
    with_sources = sum(1 for r in results if r.get("has_sources", False))
    with_confidence = sum(1 for r in results if r.get("has_confidence", False))
    with_content = sum(1 for r in results if r.get("has_content", False))
    
    logger.info(f"有效回答率: {valid_answers}/{len(results)} ({valid_answers/len(results)*100:.1f}%)")
    logger.info(f"包含来源率: {with_sources}/{len(results)} ({with_sources/len(results)*100:.1f}%)")
    logger.info(f"包含置信度率: {with_confidence}/{len(results)} ({with_confidence/len(results)*100:.1f}%)")
    logger.info(f"包含实质内容率: {with_content}/{len(results)} ({with_content/len(results)*100:.1f}%)")
    
    logger.info("\n测试完成!")

if __name__ == "__main__":
    asyncio.run(test_high_level_questions()) 
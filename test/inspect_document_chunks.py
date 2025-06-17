#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档块检查脚本
用于分析特定文献的所有文档块，查看内容质量和类型分布
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.vector_store import VectorStore
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_literature_chunks():
    """检查特定文献的所有文档块"""
    
    # 初始化向量存储
    vector_store = VectorStore()
    
    # 文献信息
    literature_id = "9d6b6860-22da-481e-be6c-482be2327e6b"
    group_id = "private"
    
    logger.info(f"检查文献 {literature_id} 的所有文档块...")
    
    try:
        # 获取集合
        collection = vector_store.get_or_create_collection(group_id)
        
        if not collection:
            logger.error("无法获取或创建集合")
            return
        
        # 查询所有属于该文献的文档块
        results = collection.get(
            where={"literature_id": literature_id},
            include=["documents", "metadatas"]
        )
        
        if not results["documents"]:
            logger.error("未找到该文献的任何文档块")
            return
        
        total_chunks = len(results["documents"])
        logger.info(f"总共找到 {total_chunks} 个文档块")
        
        # 分析每个文档块
        for i, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
            chunk_id = metadata.get("chunk_index", i)
            
            print(f"\n{'='*80}")
            print(f"文档块 {i+1}/{total_chunks} (ID: {chunk_id})")
            print(f"{'='*80}")
            
            # 基本信息
            print(f"长度: {len(doc)} 字符")
            print(f"元数据: {metadata}")
            
            # 内容预览
            preview = doc[:500] + "..." if len(doc) > 500 else doc
            print(f"\n内容预览:\n{preview}")
            
            # 内容分析
            print(f"\n内容分析:")
            
            # 检查是否包含学术关键词
            academic_keywords = [
                'abstract', 'introduction', 'method', 'result', 'conclusion', 'discussion',
                '摘要', '引言', '方法', '结果', '结论', '讨论', 'research', 'study', 'analysis'
            ]
            
            found_keywords = [kw for kw in academic_keywords if kw.lower() in doc.lower()]
            print(f"包含的学术关键词: {found_keywords}")
            
            # 检查是否可能是重要章节
            is_important = any(kw in found_keywords for kw in [
                'abstract', 'introduction', 'conclusion', '摘要', '引言', '结论'
            ])
            print(f"可能是重要章节: {is_important}")
            
            # 检查内容质量
            has_meaningful_content = len([s for s in doc.split('.') if len(s.strip()) > 20]) >= 2
            print(f"包含有意义的句子: {has_meaningful_content}")
            
            # 检查是否主要是数据/图表描述
            data_indicators = ['figure', 'table', 'graph', 'chart', '图', '表', 'rs', 'chromosome']
            is_likely_data = sum(1 for indicator in data_indicators if indicator.lower() in doc.lower()) >= 2
            print(f"可能是数据/图表描述: {is_likely_data}")
            
            # 检查版权信息
            copyright_indicators = ['creative commons', 'license', 'copyright', 'permission', '版权', '许可']
            is_copyright = any(indicator.lower() in doc.lower() for indicator in copyright_indicators)
            print(f"是版权信息: {is_copyright}")
            
            # 综合质量评分
            quality_score = 0
            if found_keywords:
                quality_score += 1
            if is_important:
                quality_score += 2
            if has_meaningful_content:
                quality_score += 1
            if not is_likely_data:
                quality_score += 1
            if not is_copyright:
                quality_score += 1
            
            print(f"质量评分: {quality_score}/6")
            
            # 分类建议
            if is_copyright:
                category = "版权信息"
            elif is_likely_data:
                category = "数据/图表"
            elif is_important:
                category = "重要章节"
            elif has_meaningful_content and found_keywords:
                category = "一般内容"
            else:
                category = "低质量内容"
            
            print(f"内容分类: {category}")
            
        # 总结统计
        print(f"\n{'='*80}")
        print("总结统计")
        print(f"{'='*80}")
        
        # 统计各类内容数量
        important_count = 0
        data_count = 0
        copyright_count = 0
        general_count = 0
        low_quality_count = 0
        
        for i, doc in enumerate(results["documents"]):
            academic_keywords = [
                'abstract', 'introduction', 'method', 'result', 'conclusion', 'discussion',
                '摘要', '引言', '方法', '结果', '结论', '讨论'
            ]
            
            found_keywords = [kw for kw in academic_keywords if kw.lower() in doc.lower()]
            is_important = any(kw in found_keywords for kw in [
                'abstract', 'introduction', 'conclusion', '摘要', '引言', '结论'
            ])
            
            data_indicators = ['figure', 'table', 'graph', 'chart', '图', '表', 'rs', 'chromosome']
            is_likely_data = sum(1 for indicator in data_indicators if indicator.lower() in doc.lower()) >= 2
            
            copyright_indicators = ['creative commons', 'license', 'copyright', 'permission', '版权', '许可']
            is_copyright = any(indicator.lower() in doc.lower() for indicator in copyright_indicators)
            
            has_meaningful_content = len([s for s in doc.split('.') if len(s.strip()) > 20]) >= 2
            
            if is_copyright:
                copyright_count += 1
            elif is_likely_data:
                data_count += 1
            elif is_important:
                important_count += 1
            elif has_meaningful_content and found_keywords:
                general_count += 1
            else:
                low_quality_count += 1
        
        print(f"重要章节 (摘要/引言/结论): {important_count}")
        print(f"一般学术内容: {general_count}")
        print(f"数据/图表描述: {data_count}")
        print(f"版权信息: {copyright_count}")
        print(f"低质量内容: {low_quality_count}")
        
        # 建议
        print(f"\n建议:")
        if important_count == 0:
            print("⚠️  警告: 该文献缺少重要章节（摘要、引言、结论）的文档块")
            print("这可能是文档处理时的分块策略导致的，需要重新处理该文献")
        
        if data_count > total_chunks * 0.5:
            print("⚠️  警告: 超过50%的文档块是数据/图表描述，缺少叙述性内容")
        
        if low_quality_count > total_chunks * 0.3:
            print("⚠️  警告: 超过30%的文档块质量较低，需要改进文档处理流程")
            
    except Exception as e:
        logger.error(f"检查文档块时出错: {str(e)}")

if __name__ == "__main__":
    inspect_literature_chunks() 
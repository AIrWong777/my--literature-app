#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的文档处理流程
从PDF提取到文档块生成
"""

import os
import sys
import logging

# 设置路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.document_processor import DocumentProcessor
from app.utils.text_extractor import extract_pdf_text_enhanced

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('document_processing_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_document_processing():
    """测试文档处理流程"""
    
    # 测试文件
    test_file = "uploads/private_5d5cd027-2e0f-4961-aaa0-f673b43e3a0c/s41467-023-40566-6.pdf"
    
    if not os.path.exists(test_file):
        logger.error(f"测试文件不存在: {test_file}")
        return
    
    logger.info(f"测试文件: {test_file}")
    
    # 1. 测试文本提取
    logger.info("="*80)
    logger.info("第一步：PDF文本提取")
    
    extraction_result = extract_pdf_text_enhanced(test_file)
    
    logger.info(f"提取方法: {extraction_result['extraction_method']}")
    logger.info(f"提取成功: {extraction_result['extraction_success']}")
    logger.info(f"文本长度: {len(extraction_result['text'])} 字符")
    logger.info(f"文本块数量: {len(extraction_result['text_blocks'])}")
    
    if extraction_result['text']:
        text = extraction_result['text']
        
        # 显示文本开头
        logger.info(f"文本开头 (前500字符):")
        logger.info(text[:500])
        
        # 2. 测试文档处理器
        logger.info("="*80)
        logger.info("第二步：文档处理器分块")
        
        processor = DocumentProcessor()
        
        # 调用文档处理器
        chunks = processor.process_text(text, test_file)
        
        logger.info(f"生成的文档块数量: {len(chunks)}")
        
        # 分析文档块质量
        high_quality_chunks = []
        medium_quality_chunks = []
        low_quality_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '')
            
            # 简单的质量评估
            academic_keywords = [
                'abstract', 'introduction', 'method', 'result', 'conclusion',
                'figure', 'table', 'reference', 'experiment', 'analysis',
                'discussion', 'author', 'doi', 'journal', 'cardiovascular'
            ]
            
            keyword_count = sum(1 for keyword in academic_keywords if keyword.lower() in content.lower())
            length = len(content)
            
            if keyword_count >= 3 and length > 200:
                quality = "高"
                high_quality_chunks.append((i, chunk))
            elif keyword_count >= 1 and length > 100:
                quality = "中"
                medium_quality_chunks.append((i, chunk))
            else:
                quality = "低"
                low_quality_chunks.append((i, chunk))
            
            logger.info(f"块 {i+1}: 长度={length}, 关键词={keyword_count}, 质量={quality}")
            if i < 10:  # 只显示前10个块的内容预览
                preview = content[:100].replace('\n', ' ')
                logger.info(f"  内容预览: {preview}...")
        
        logger.info("="*80)
        logger.info("文档块质量统计:")
        logger.info(f"高质量块: {len(high_quality_chunks)}")
        logger.info(f"中等质量块: {len(medium_quality_chunks)}")
        logger.info(f"低质量块: {len(low_quality_chunks)}")
        
        # 显示一些高质量块的内容
        if high_quality_chunks:
            logger.info("\n高质量块示例:")
            for i, (idx, chunk) in enumerate(high_quality_chunks[:3]):
                content = chunk.get('content', '')
                logger.info(f"高质量块 {idx+1}:")
                logger.info(f"  内容: {content[:300]}...")
        
        # 检查是否包含重要章节
        abstract_found = False
        intro_found = False
        method_found = False
        result_found = False
        conclusion_found = False
        
        for chunk in chunks:
            content = chunk.get('content', '').lower()
            if 'abstract' in content and len(content) > 100:
                abstract_found = True
            if 'introduction' in content and len(content) > 100:
                intro_found = True
            if 'method' in content and len(content) > 100:
                method_found = True
            if 'result' in content and len(content) > 100:
                result_found = True
            if 'conclusion' in content and len(content) > 100:
                conclusion_found = True
        
        logger.info("="*80)
        logger.info("重要章节检测:")
        logger.info(f"摘要 (Abstract): {'✅' if abstract_found else '❌'}")
        logger.info(f"引言 (Introduction): {'✅' if intro_found else '❌'}")
        logger.info(f"方法 (Method): {'✅' if method_found else '❌'}")
        logger.info(f"结果 (Result): {'✅' if result_found else '❌'}")
        logger.info(f"结论 (Conclusion): {'✅' if conclusion_found else '❌'}")
        
    else:
        logger.error("文本提取失败，无法继续测试")

if __name__ == "__main__":
    test_document_processing() 
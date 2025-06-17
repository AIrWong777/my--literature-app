#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实学术论文PDF的文本提取
"""

import os
import sys
import logging
from pathlib import Path

# 设置路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.text_extractor import (
    extract_pdf_text, 
    extract_pdf_text_with_pymupdf,
    extract_pdf_text_enhanced
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('real_pdf_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_specific_pdf(pdf_path):
    """测试特定PDF文件的文本提取"""
    
    logger.info(f"\n{'='*80}")
    logger.info(f"测试PDF文件: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        logger.error(f"文件不存在: {pdf_path}")
        return
    
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    logger.info(f"文件大小: {file_size:.2f} MB")
    
    try:
        # 测试增强提取
        logger.info("使用增强PDF提取...")
        enhanced_result = extract_pdf_text_enhanced(pdf_path)
        
        logger.info(f"页数: {enhanced_result['page_count']}")
        logger.info(f"提取方法: {enhanced_result['extraction_method']}")
        logger.info(f"提取成功: {enhanced_result['extraction_success']}")
        logger.info(f"文本长度: {len(enhanced_result['text'])} 字符")
        logger.info(f"文本块数量: {len(enhanced_result['text_blocks'])}")
        logger.info(f"包含图像: {enhanced_result['has_images']}")
        
        if enhanced_result['text']:
            text = enhanced_result['text']
            
            # 显示文本预览
            preview = text[:1000].replace('\n', ' ')
            logger.info(f"文本预览 (前1000字符): {preview}...")
            
            # 检查是否包含学术关键词
            academic_keywords = [
                'abstract', 'introduction', 'method', 'result', 'conclusion',
                'figure', 'table', 'reference', 'experiment', 'analysis',
                'discussion', 'author', 'doi', 'journal', 'volume',
                '摘要', '引言', '方法', '结果', '结论', '图', '表', '参考文献'
            ]
            
            found_keywords = []
            text_lower = text.lower()
            for keyword in academic_keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
            
            logger.info(f"发现的学术关键词: {found_keywords}")
            
            # 统计文本结构
            lines = text.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            logger.info(f"总行数: {len(lines)}")
            logger.info(f"非空行数: {len(non_empty_lines)}")
            
            # 检查段落
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            logger.info(f"段落数量: {len(paragraphs)}")
            
            # 检查是否有标题结构
            potential_titles = []
            for line in non_empty_lines[:20]:  # 检查前20行
                if len(line) < 100 and line.isupper() or (line[0].isupper() and len(line.split()) < 10):
                    potential_titles.append(line)
            
            if potential_titles:
                logger.info(f"可能的标题/章节: {potential_titles[:5]}")  # 只显示前5个
            
            # 检查引用格式
            citation_patterns = ['[1]', '(1)', 'et al.', 'DOI:', 'doi:', 'arXiv:']
            found_citations = []
            for pattern in citation_patterns:
                if pattern in text:
                    found_citations.append(pattern)
            
            if found_citations:
                logger.info(f"发现的引用格式: {found_citations}")
            
            # 检查数学公式或特殊符号
            math_symbols = ['α', 'β', 'γ', 'δ', 'θ', 'λ', 'μ', 'σ', '±', '∈', '≤', '≥', '∑', '∫']
            found_math = []
            for symbol in math_symbols:
                if symbol in text:
                    found_math.append(symbol)
            
            if found_math:
                logger.info(f"发现的数学符号: {found_math}")
            
            # 检查文本质量
            if len(text) > 5000:
                logger.info("✅ 文本长度充足，适合进行问答")
            else:
                logger.warning("⚠️ 文本较短，可能影响问答质量")
            
            if len(found_keywords) >= 3:
                logger.info("✅ 包含丰富的学术关键词")
            else:
                logger.warning("⚠️ 学术关键词较少")
                
        else:
            logger.warning("❌ 未提取到任何文本")
    
    except Exception as e:
        logger.error(f"测试PDF文件时出错: {e}")

def main():
    """主函数"""
    logger.info("开始测试真实学术论文PDF文件")
    
    # 测试特定的PDF文件
    pdf_files = [
        "uploads/private_5d5cd027-2e0f-4961-aaa0-f673b43e3a0c/s41467-023-40566-6.pdf",
        "uploads/private_5d5cd027-2e0f-4961-aaa0-f673b43e3a0c/test1.pdf",
        "uploads/private_5d5cd027-2e0f-4961-aaa0-f673b43e3a0c/20250512122228.pdf"
    ]
    
    for pdf_file in pdf_files:
        test_specific_pdf(pdf_file)
    
    logger.info("\n" + "="*80)
    logger.info("真实PDF测试完成")

if __name__ == "__main__":
    main() 
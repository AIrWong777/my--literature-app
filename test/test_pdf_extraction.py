#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文本提取测试脚本
测试PyMuPDF和PyPDF2的文本提取能力
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
        logging.FileHandler('pdf_extraction_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_pdf_extraction():
    """测试PDF文本提取功能"""
    
    # 查找uploads目录中的PDF文件
    uploads_dir = Path("uploads")
    if not uploads_dir.exists():
        logger.error("uploads目录不存在")
        return
    
    pdf_files = []
    for folder in uploads_dir.iterdir():
        if folder.is_dir():
            for file in folder.glob("*.pdf"):
                pdf_files.append(file)
    
    if not pdf_files:
        logger.error("未找到PDF文件")
        return
    
    logger.info(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 测试前几个PDF文件
    for i, pdf_file in enumerate(pdf_files[:3]):  # 只测试前3个文件
        logger.info(f"\n{'='*60}")
        logger.info(f"测试文件 {i+1}: {pdf_file}")
        
        try:
            # 测试增强提取
            logger.info("使用增强提取...")
            enhanced_result = extract_pdf_text_enhanced(str(pdf_file))
            
            logger.info(f"页数: {enhanced_result['page_count']}")
            logger.info(f"提取方法: {enhanced_result['extraction_method']}")
            logger.info(f"提取成功: {enhanced_result['extraction_success']}")
            logger.info(f"文本长度: {len(enhanced_result['text'])} 字符")
            logger.info(f"文本块数量: {len(enhanced_result['text_blocks'])}")
            logger.info(f"包含图像: {enhanced_result['has_images']}")
            
            if enhanced_result['text']:
                # 显示文本预览
                preview = enhanced_result['text'][:500].replace('\n', ' ')
                logger.info(f"文本预览: {preview}...")
                
                # 检查是否包含学术关键词
                academic_keywords = [
                    'abstract', 'introduction', 'method', 'result', 'conclusion',
                    'figure', 'table', 'reference', 'experiment', 'analysis',
                    '摘要', '引言', '方法', '结果', '结论', '图', '表', '参考文献'
                ]
                
                found_keywords = []
                text_lower = enhanced_result['text'].lower()
                for keyword in academic_keywords:
                    if keyword in text_lower:
                        found_keywords.append(keyword)
                
                logger.info(f"发现的学术关键词: {found_keywords}")
                
                # 分析文档结构
                lines = enhanced_result['text'].split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                logger.info(f"非空行数: {len(non_empty_lines)}")
                
                # 检查是否有段落分隔
                paragraphs = enhanced_result['text'].split('\n\n')
                logger.info(f"段落数量: {len(paragraphs)}")
                
            else:
                logger.warning("未提取到任何文本")
                
        except Exception as e:
            logger.error(f"测试文件 {pdf_file} 时出错: {e}")
    
    logger.info(f"\n{'='*60}")
    logger.info("PDF提取测试完成")

def compare_extraction_methods():
    """比较不同提取方法的效果"""
    
    uploads_dir = Path("uploads")
    pdf_files = []
    for folder in uploads_dir.iterdir():
        if folder.is_dir():
            for file in folder.glob("*.pdf"):
                pdf_files.append(file)
                break  # 只取第一个PDF文件
        if pdf_files:
            break
    
    if not pdf_files:
        logger.error("未找到PDF文件进行比较")
        return
    
    test_file = pdf_files[0]
    logger.info(f"比较提取方法，测试文件: {test_file}")
    
    # 方法1: PyMuPDF
    logger.info("\n--- PyMuPDF提取 ---")
    try:
        text1 = extract_pdf_text_with_pymupdf(str(test_file))
        if text1:
            logger.info(f"PyMuPDF提取长度: {len(text1)} 字符")
            logger.info(f"PyMuPDF预览: {text1[:200]}...")
        else:
            logger.info("PyMuPDF提取失败")
    except Exception as e:
        logger.error(f"PyMuPDF提取错误: {e}")
    
    # 方法2: 标准方法（会尝试PyMuPDF然后回退到PyPDF2）
    logger.info("\n--- 标准提取方法 ---")
    try:
        text2 = extract_pdf_text(str(test_file))
        if text2:
            logger.info(f"标准方法提取长度: {len(text2)} 字符")
            logger.info(f"标准方法预览: {text2[:200]}...")
        else:
            logger.info("标准方法提取失败")
    except Exception as e:
        logger.error(f"标准方法提取错误: {e}")
    
    # 比较结果
    if 'text1' in locals() and 'text2' in locals() and text1 and text2:
        if len(text1) > len(text2):
            logger.info(f"PyMuPDF提取了更多文本 (+{len(text1) - len(text2)} 字符)")
        elif len(text2) > len(text1):
            logger.info(f"标准方法提取了更多文本 (+{len(text2) - len(text1)} 字符)")
        else:
            logger.info("两种方法提取的文本长度相同")

if __name__ == "__main__":
    logger.info("开始PDF文本提取测试")
    
    # 首先安装PyMuPDF（如果需要的话）
    try:
        import fitz
        logger.info("PyMuPDF已安装")
    except ImportError:
        logger.warning("PyMuPDF未安装，将使用PyPDF2")
    
    test_pdf_extraction()
    compare_extraction_methods() 
#!/usr/bin/env python3
"""
测试文件处理工具函数
验证文件上传相关功能是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import config
from app.utils.file_handler import (
    validate_file_type, 
    generate_file_path,
    get_file_info
)
from app.utils.text_extractor import (
    extract_title_from_filename,
    extract_title_from_text,
    is_text_extractable
)

def test_config():
    """测试配置功能"""
    print("🔧 测试配置功能...")
    
    print("测试文件类型验证...")
    try:
        # 测试文件类型验证
        print(f"测试 PDF: {config.is_allowed_file_type('test.pdf')}")
        assert config.is_allowed_file_type("test.pdf") == True
        print(f"测试 DOCX: {config.is_allowed_file_type('test.docx')}")
        assert config.is_allowed_file_type("test.docx") == True
        print(f"测试 HTML: {config.is_allowed_file_type('test.html')}")
        assert config.is_allowed_file_type("test.html") == True
        print(f"测试 TXT: {config.is_allowed_file_type('test.txt')}")
        assert config.is_allowed_file_type("test.txt") == True
        print(f"测试 EXE: {config.is_allowed_file_type('test.exe')}")
        assert config.is_allowed_file_type("test.exe") == False
        print("✅ 文件类型验证正常")
    except AssertionError as e:
        print(f"❌ 文件类型验证失败: {e}")
        raise
    
    print("\n测试文件大小验证...")
    try:
        # 测试文件大小验证
        print(f"测试 1KB: {config.is_file_size_valid(1024)}")
        assert config.is_file_size_valid(1024) == True  # 1KB
        print(f"测试 50MB: {config.is_file_size_valid(50 * 1024 * 1024)}")
        assert config.is_file_size_valid(50 * 1024 * 1024) == True  # 50MB
        print(f"测试 100MB: {config.is_file_size_valid(100 * 1024 * 1024)}")
        assert config.is_file_size_valid(100 * 1024 * 1024) == False  # 100MB
        print("✅ 文件大小验证正常")
    except AssertionError as e:
        print(f"❌ 文件大小验证失败: {e}")
        raise
    
    print("\n测试目录创建...")
    try:
        # 测试目录创建
        test_group_id = "test-group-123"
        upload_dir = config.ensure_upload_dir_exists(test_group_id)
        print(f"创建目录: {upload_dir}")
        assert os.path.exists(upload_dir)
        print(f"✅ 目录创建正常: {upload_dir}")
    except AssertionError as e:
        print(f"❌ 目录创建失败: {e}")
        raise
    except Exception as e:
        print(f"❌ 目录创建出错: {e}")
        raise

def test_file_handler():
    """测试文件处理函数"""
    print("\n📁 测试文件处理函数...")
    
    # 测试文件类型验证
    print("测试文件类型验证...")
    print(f"测试 PDF: {validate_file_type('document.pdf')}")
    assert validate_file_type("document.pdf") == True
    print(f"测试 EXE: {validate_file_type('document.exe')}")
    assert validate_file_type("document.exe") == False
    print("✅ 文件类型验证函数正常")
    
    # 测试路径生成
    print("\n测试路径生成...")
    test_group_id = "test-group-456"
    test_filename = "research_paper.pdf"
    full_path = generate_file_path(test_group_id, test_filename)
    
    print(f"生成路径: {full_path}")
    assert test_group_id in str(full_path)
    assert str(full_path).endswith(".pdf")
    print("✅ 路径生成正常")
    print(f"   完整路径: {full_path}")

def test_text_extractor():
    """测试文本提取函数"""
    print("\n📝 测试文本提取函数...")
    
    # 测试从文件名提取标题
    print("测试从文件名提取标题...")
    title1 = extract_title_from_filename("research_paper.pdf")
    assert title1 == "research paper"  # 注意：函数会将下划线替换为空格
    print(f"✅ 文件名标题提取: '{title1}'")
    
    # 测试从文本提取标题
    print("\n测试从文本提取标题...")
    test_text = "第1章 人工智能研究概述\n\n本文介绍了人工智能的发展历程..."
    title2 = extract_title_from_text(test_text)
    assert "人工智能研究概述" in title2
    print(f"✅ 文本标题提取: '{title2}'")
    
    # 测试长文本标题截断
    print("\n测试长文本标题截断...")
    long_text = "这是一个非常非常非常非常非常非常非常非常非常非常长的标题，应该被截断"
    title3 = extract_title_from_text(long_text, max_length=20)
    assert len(title3) <= 20
    print(f"✅ 长标题截断: '{title3}'")
    
    # 测试文件类型支持检查
    print("\n测试文件类型支持检查...")
    print(f"测试 PDF: {is_text_extractable('test.pdf')}")
    assert is_text_extractable("test.pdf") == True
    print(f"测试 DOCX: {is_text_extractable('test.docx')}")
    assert is_text_extractable("test.docx") == True
    print(f"测试 HTML: {is_text_extractable('test.html')}")
    assert is_text_extractable("test.html") == True
    print(f"测试 EXE: {is_text_extractable('test.exe')}")
    assert is_text_extractable("test.exe") == False
    print("✅ 文件类型支持检查正常")

def test_directory_structure():
    """测试目录结构"""
    print("\n📂 测试目录结构...")
    
    # 检查uploads目录是否创建
    uploads_dir = Path("./uploads")
    if uploads_dir.exists():
        print(f"✅ uploads目录存在: {uploads_dir.absolute()}")
        
        # 列出子目录
        subdirs = [d for d in uploads_dir.iterdir() if d.is_dir()]
        if subdirs:
            print("📁 发现的研究组目录:")
            for subdir in subdirs:
                print(f"   - {subdir.name}")
        else:
            print("ℹ️  暂无研究组目录")
    else:
        print("ℹ️  uploads目录尚未创建")

def main():
    """主测试函数"""
    print("🧪 文件处理工具函数测试")
    print("="*50)
    
    try:
        test_config()
        test_file_handler()
        test_text_extractor()
        test_directory_structure()
        
        print("\n" + "="*50)
        print("🎉 所有测试通过！文件处理工具函数正常工作")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
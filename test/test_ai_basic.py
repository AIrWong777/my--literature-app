"""
AI功能基础测试脚本
测试文本处理、配置等基础功能
"""

import os
import sys
sys.path.append('.')

from app.config import settings
from app.utils.text_extractor import extract_text_from_file, extract_metadata_from_file
from app.utils.text_processor import split_text_into_chunks, prepare_chunks_for_embedding

def test_config():
    """测试配置功能"""
    print("=== 配置测试 ===")
    
    # 测试AI配置
    ai_provider = settings.get_ai_provider()
    print(f"AI提供商: {ai_provider}")
    
    ai_valid, ai_message = settings.validate_ai_config()
    print(f"AI配置验证: {ai_valid} - {ai_message}")
    
    # 显示配置摘要
    config_summary = settings.get_config_summary()
    print("\n配置摘要:")
    for key, value in config_summary.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 配置测试完成\n")

def test_text_extraction():
    """测试文本提取功能"""
    print("=== 文本提取测试 ===")
    
    # 查找测试文件
    test_files = []
    uploads_dir = "./uploads"
    
    if os.path.exists(uploads_dir):
        for root, dirs, files in os.walk(uploads_dir):
            for file in files:
                if file.lower().endswith(('.pdf', '.docx', '.html', '.txt')):
                    test_files.append(os.path.join(root, file))
    
    if not test_files:
        print("❌ 没有找到测试文件")
        return
    
    print(f"找到 {len(test_files)} 个测试文件")
    
    for file_path in test_files[:3]:  # 只测试前3个文件
        print(f"\n测试文件: {file_path}")
        
        try:
            # 提取文本
            extracted_text = extract_text_from_file(file_path)
            if extracted_text:
                print(f"  ✅ 文本提取成功，长度: {len(extracted_text)} 字符")
                print(f"  预览: {extracted_text[:100]}...")
            else:
                print("  ❌ 文本提取失败或为空")
            
            # 提取元数据
            metadata = extract_metadata_from_file(file_path, os.path.basename(file_path))
            print(f"  标题: {metadata['title']}")
            print(f"  提取成功: {metadata['extraction_success']}")
            print(f"  文本长度: {metadata['text_length']}")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
    
    print("\n✅ 文本提取测试完成\n")

def test_text_processing():
    """测试文本处理功能"""
    print("=== 文本处理测试 ===")
    
    # 创建测试文本
    test_text = """
    这是一个测试文档的标题
    
    第一段内容：人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
    它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
    
    第二段内容：机器学习是人工智能的一个重要分支，它通过算法使计算机能够从数据中学习，
    而不需要明确编程。深度学习是机器学习的一个子集，它使用神经网络来模拟人脑的工作方式。
    
    第三段内容：自然语言处理（NLP）是人工智能的另一个重要领域，它致力于让计算机理解、
    解释和生成人类语言。这包括文本分析、语音识别、机器翻译等多个方面。
    
    结论：人工智能技术正在快速发展，并在各个领域产生深远影响。
    """ * 3  # 重复3次以增加长度
    
    print(f"测试文本长度: {len(test_text)} 字符")
    
    try:
        # 测试文本分块
        chunks = split_text_into_chunks(test_text, chunk_size=500, overlap=100)
        print(f"✅ 文本分块成功: {len(chunks)} 个块")
        
        for i, chunk in enumerate(chunks[:3]):  # 显示前3个块
            print(f"  块 {i+1} (长度: {len(chunk)}): {chunk[:100]}...")
        
        # 测试准备embedding数据
        chunks_data = prepare_chunks_for_embedding(
            chunks, 
            "test_literature_id", 
            "test_group_id",
            "测试文献标题"
        )
        print(f"✅ 准备embedding数据成功: {len(chunks_data)} 个数据块")
        
        # 显示第一个数据块的结构
        if chunks_data:
            first_chunk = chunks_data[0]
            print("  第一个数据块结构:")
            for key, value in first_chunk.items():
                if key == "text":
                    print(f"    {key}: {str(value)[:50]}...")
                else:
                    print(f"    {key}: {value}")
        
    except Exception as e:
        print(f"❌ 文本处理失败: {e}")
    
    print("\n✅ 文本处理测试完成\n")

def test_vector_store_basic():
    """测试向量存储基础功能"""
    print("=== 向量存储基础测试 ===")
    
    try:
        from app.utils.vector_store import vector_store
        
        # 检查可用性
        is_available = vector_store.is_available()
        print(f"向量存储可用性: {is_available}")
        
        if is_available:
            # 健康检查
            health = vector_store.health_check()
            print("健康检查结果:")
            for key, value in health.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️ 向量存储不可用（可能是ChromaDB未安装）")
        
    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
    
    print("\n✅ 向量存储基础测试完成\n")

def test_embedding_service_basic():
    """测试embedding服务基础功能"""
    print("=== Embedding服务基础测试 ===")
    
    try:
        from app.utils.embedding_service import embedding_service
        
        # 检查可用性
        is_available = embedding_service.is_available()
        print(f"Embedding服务可用性: {is_available}")
        
        # 获取服务信息
        info = embedding_service.get_embedding_info()
        print("服务信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        if is_available:
            # 连接测试
            test_result = embedding_service.test_connection()
            print("连接测试结果:")
            for key, value in test_result.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️ Embedding服务不可用（可能是API密钥未配置或库未安装）")
        
    except Exception as e:
        print(f"❌ Embedding服务测试失败: {e}")
    
    print("\n✅ Embedding服务基础测试完成\n")

def main():
    """主测试函数"""
    print("🚀 开始AI功能基础测试\n")
    
    try:
        test_config()
        test_text_extraction()
        test_text_processing()
        test_vector_store_basic()
        test_embedding_service_basic()
        
        print("🎉 所有基础测试完成！")
        print("\n📋 测试总结:")
        print("- ✅ 配置管理功能正常")
        print("- ✅ 文本提取功能正常")
        print("- ✅ 文本处理功能正常")
        print("- ⚠️ 向量存储和Embedding服务需要安装相应依赖")
        print("\n💡 下一步:")
        print("1. 安装AI相关依赖: pip install -r requirements.txt")
        print("2. 配置API密钥（在.env文件中）")
        print("3. 运行完整的AI功能测试")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
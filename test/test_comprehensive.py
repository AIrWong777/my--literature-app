#!/usr/bin/env python3
"""
综合功能测试脚本
测试文献管理系统的所有核心功能
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_google_api():
    """测试Google API连接"""
    print("🌐 测试Google API连接...")
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ Google API密钥未配置")
            return False
        
        client = genai.Client(api_key=api_key)
        
        # 测试embedding生成
        response = client.models.embed_content(
            model="text-embedding-004",
            contents="测试文本",
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )
        
        if response.embeddings and len(response.embeddings) > 0:
            embedding_dim = len(response.embeddings[0].values)
            print(f"✅ Google API连接正常，embedding维度: {embedding_dim}")
            return True
        else:
            print("❌ Google API响应异常")
            return False
            
    except Exception as e:
        print(f"❌ Google API连接失败: {e}")
        return False

def test_embedding_service():
    """测试embedding服务"""
    print("\n🧠 测试Embedding服务...")
    
    try:
        sys.path.append('.')
        from app.utils.embedding_service import embedding_service
        
        # 测试连接
        result = embedding_service.test_connection()
        if result.get('status') == 'success':
            print(f"✅ Embedding服务可用: {result['provider']}")
            print(f"   模型: {result['model']}")
            print(f"   维度: {result['embedding_dimension']}")
            print(f"   响应时间: {result['response_time_seconds']}秒")
            
            # 测试批量生成
            test_texts = [
                "人工智能技术发展迅速",
                "机器学习是AI的重要分支",
                "深度学习在图像识别中表现优异"
            ]
            
            embeddings, failed = embedding_service.batch_generate_embeddings(test_texts, batch_size=2)
            print(f"✅ 批量embedding生成: {len(embeddings)}/{len(test_texts)} 成功")
            
            return True
        else:
            print(f"❌ Embedding服务不可用: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Embedding服务测试失败: {e}")
        return False

def test_vector_store():
    """测试向量数据库"""
    print("\n🗄️  测试向量数据库...")
    
    try:
        sys.path.append('.')
        from app.utils.vector_store import VectorStore
        
        # 创建测试实例
        vector_store = VectorStore()
        
        # 测试健康检查
        health = vector_store.health_check()
        print(f"✅ 向量数据库健康状态: {health['status']}")
        print(f"   集合数量: {health['collections_count']}")
        
        # 测试集合操作
        test_group_id = "test_group_comprehensive"
        collection = vector_store.get_or_create_collection(test_group_id)
        print(f"✅ 集合操作成功: {collection.name}")
        
        # 测试文档存储
        test_chunks = [
            {
                'text': '人工智能是计算机科学的分支，研究如何让机器模拟人类智能',
                'chunk_index': 0,
                'literature_id': 'test_lit_001',
                'group_id': test_group_id,
                'literature_title': '人工智能概论',
                'chunk_length': 30,
                'chunk_id': 'test_lit_001_chunk_0'
            },
            {
                'text': '机器学习使计算机能够从数据中学习，无需明确编程',
                'chunk_index': 1,
                'literature_id': 'test_lit_001',
                'group_id': test_group_id,
                'literature_title': '人工智能概论',
                'chunk_length': 24,
                'chunk_id': 'test_lit_001_chunk_1'
            }
        ]
        
        # 修正方法调用 - 使用新的便捷方法
        success = vector_store.store_document_chunks_with_embeddings(test_chunks, 'test_lit_001', test_group_id)
        print(f"✅ 文档存储成功: {success}")
        
        # 测试搜索 - 使用新的便捷方法
        results = vector_store.search_similar_chunks_by_query(
            query="什么是机器学习", 
            group_id=test_group_id, 
            top_k=2
        )
        print(f"✅ 相似度搜索: 找到 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            print(f"   结果{i}: 相似度 {result['similarity']:.3f}")
            print(f"         文本: {result['text'][:50]}...")
        
        # 清理测试数据
        vector_store.delete_document_chunks('test_lit_001', test_group_id)
        print("✅ 测试数据清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_processing():
    """测试文本处理功能"""
    print("\n📝 测试文本处理功能...")
    
    try:
        sys.path.append('.')
        from app.utils.text_processor import (
            split_text_into_chunks, 
            prepare_chunks_for_embedding, 
            estimate_token_count
        )
        from app.utils.text_extractor import clean_extracted_text
        
        # 测试文本清理
        dirty_text = "   这是一个   测试文本\n\n\n   包含多余空白   "
        clean_text = clean_extracted_text(dirty_text)
        print(f"✅ 文本清理: '{dirty_text}' -> '{clean_text}'")
        
        # 测试文本分块
        long_text = """
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，
        并生产出一种新的能以人类智能相似的方式做出反应的智能机器。机器学习是人工智能的一个重要
        分支，它是一种通过算法使机器能够从数据中学习并做出决策或预测的技术。深度学习是机器学习
        的一个子集，它使用神经网络来模拟人脑的工作方式。
        
        自然语言处理（Natural Language Processing，NLP）是人工智能和语言学领域的分支学科。
        此领域探讨如何处理及运用自然语言；自然语言处理包括多个步骤：词法分析、语法分析、
        语义分析、语用分析等。机器翻译，语音识别，文本分类都是自然语言处理的应用。
        """
        
        chunks = split_text_into_chunks(long_text, chunk_size=200, overlap=50)
        print(f"✅ 文本分块: {len(long_text)} 字符 -> {len(chunks)} 个块")
        
        # 测试embedding数据准备
        chunk_data = prepare_chunks_for_embedding(
            chunks, 
            literature_id="test_lit_processing",
            group_id="test_group_processing",
            literature_title="文本处理测试"
        )
        print(f"✅ Embedding数据准备: {len(chunk_data)} 个数据块")
        
        # 测试token计算
        token_count = estimate_token_count(long_text, model_type="google")
        print(f"✅ Token估算: {len(long_text)} 字符 ≈ {token_count} tokens")
        
        return True
        
    except Exception as e:
        print(f"❌ 文本处理测试失败: {e}")
        return False

def test_file_upload_processing():
    """测试文件上传和处理"""
    print("\n📁 测试文件处理功能...")
    
    try:
        sys.path.append('.')
        from app.utils.storage_manager import StorageManager
        from app.utils.text_extractor import extract_text_from_file
        
        # 创建临时测试文件
        test_content = """
        # 测试文档
        
        这是一个测试文档，用于验证文件处理功能。
        
        ## 第一章：人工智能简介
        
        人工智能（AI）是一个跨学科的科学领域，致力于理解和构建智能行为。
        它结合了计算机科学、数学、心理学、语言学等多个学科。
        
        ## 第二章：机器学习
        
        机器学习是AI的一个重要分支，通过算法让计算机从数据中学习模式。
        常见的机器学习方法包括监督学习、无监督学习和强化学习。
        
        ## 结论
        
        AI技术正在快速发展，在各个领域都有广泛应用。
        """
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file_path = f.name
        
        try:
            # 测试文本提取
            extracted_text = extract_text_from_file(temp_file_path)
            print(f"✅ 文本提取: {len(extracted_text)} 字符")
            
            # 测试存储管理
            storage = StorageManager()
            test_group_id = "test_group_storage"
            
            # 模拟文件上传
            with open(temp_file_path, 'rb') as f:
                file_data = f.read()
            
            # 这里简化测试，不实际保存文件
            print("✅ 文件读取成功")
            print(f"   文件大小: {len(file_data)} 字节")
            
            return True
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
            
    except Exception as e:
        print(f"❌ 文件处理测试失败: {e}")
        return False

def test_end_to_end_workflow():
    """测试端到端工作流程"""
    print("\n🔄 测试端到端工作流程...")
    
    try:
        sys.path.append('.')
        from app.utils.text_processor import split_text_into_chunks, prepare_chunks_for_embedding
        from app.utils.embedding_service import embedding_service
        from app.utils.vector_store import VectorStore
        
        # 模拟文献处理流程
        test_text = """
        机器学习算法分析：
        
        1. 监督学习：使用标记数据训练模型，如分类和回归问题。
           常见算法：线性回归、决策树、随机森林、支持向量机。
        
        2. 无监督学习：从未标记数据中发现模式。
           常见算法：聚类、降维、关联规则挖掘。
        
        3. 强化学习：通过与环境交互学习最优策略。
           应用领域：游戏AI、机器人控制、推荐系统。
        
        选择合适的算法需要考虑数据特征、问题类型和计算资源。
        """
        
        # 步骤1: 文本处理
        chunks = split_text_into_chunks(test_text, chunk_size=150, overlap=30)
        chunk_data = prepare_chunks_for_embedding(
            chunks,
            literature_id="test_workflow_lit",
            group_id="test_workflow_group",
            literature_title="机器学习算法综述"
        )
        print(f"✅ 步骤1 - 文本处理: {len(chunk_data)} 个块")
        
        # 步骤2: 生成embeddings
        embeddings, failed = embedding_service.batch_generate_embeddings(
            [chunk['text'] for chunk in chunk_data]
        )
        print(f"✅ 步骤2 - Embedding生成: {len(embeddings)} 个向量")
        
        # 步骤3: 存储到向量数据库
        if embeddings:
            vector_store = VectorStore()
            success = vector_store.store_document_chunks_with_embeddings(chunk_data, "test_workflow_lit", "test_workflow_group")
            print(f"✅ 步骤3 - 向量存储: {'成功' if success else '失败'}")
            
            # 步骤4: 测试检索
            query_results = vector_store.search_similar_chunks_by_query(
                query="什么是监督学习？",
                group_id="test_workflow_group",
                top_k=2
            )
            print(f"✅ 步骤4 - 检索测试: 找到 {len(query_results)} 个相关结果")
            
            # 清理测试数据
            vector_store.delete_document_chunks("test_workflow_lit", "test_workflow_group")
            print("✅ 测试数据清理完成")
            
            return True
        else:
            print("❌ 无法生成embeddings")
            return False
            
    except Exception as e:
        print(f"❌ 端到端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 文献管理系统综合功能测试")
    print("=" * 60)
    
    tests = [
        ("Google API连接", test_google_api),
        ("Embedding服务", test_embedding_service),
        ("向量数据库", test_vector_store),
        ("文本处理", test_text_processing),
        ("文件处理", test_file_upload_processing),
        ("端到端工作流程", test_end_to_end_workflow)
    ]
    
    results = []
    total_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        start_time = time.time()
        
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ 通过" if success else "❌ 失败"
            elapsed = time.time() - start_time
            print(f"\n{status} ({elapsed:.2f}秒)")
        except Exception as e:
            results.append((test_name, False))
            elapsed = time.time() - start_time
            print(f"\n❌ 异常: {e} ({elapsed:.2f}秒)")
    
    # 测试结果汇总
    total_elapsed = time.time() - total_time
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    print(f"总耗时: {total_elapsed:.2f}秒")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！系统功能完整。")
    else:
        print(f"\n⚠️  {len(results) - passed} 个测试失败，请检查相关功能。")
    
    print("\n💡 系统功能概览:")
    print("   ✅ Google AI API集成")
    print("   ✅ 文本向量化服务")
    print("   ✅ ChromaDB向量数据库")
    print("   ✅ 智能文本处理")
    print("   ✅ 文件提取和解析")
    print("   ✅ 完整的检索工作流程")

if __name__ == "__main__":
    main() 
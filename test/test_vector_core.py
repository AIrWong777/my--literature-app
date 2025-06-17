#!/usr/bin/env python3
"""
向量数据库核心功能测试脚本
测试ChromaDB、Google embedding、向量存储等核心功能
不依赖API服务器
"""

import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.vector_store import VectorStore
from app.utils.embedding_service import EmbeddingService
from app.utils.text_processor import split_text_into_chunks, prepare_chunks_for_embedding
from app.config import settings

def test_configuration():
    """测试配置信息"""
    print("⚙️  测试配置信息...")
    
    print(f"   AI提供商: {settings.get_ai_provider()}")
    print(f"   向量数据库路径: {settings.VECTOR_DB_PATH}")
    print(f"   集合前缀: {settings.VECTOR_DB_COLLECTION_PREFIX}")
    
    ai_valid, ai_message = settings.validate_ai_config()
    print(f"   AI配置: {'✅' if ai_valid else '❌'} {ai_message}")
    
    return ai_valid

def test_vector_store():
    """测试向量存储"""
    print("\n🗄️  测试向量存储...")
    
    vector_store = VectorStore()
    
    # 测试初始化
    if vector_store.is_available():
        print("   ✅ ChromaDB客户端初始化成功")
    else:
        print("   ❌ ChromaDB客户端初始化失败")
        return False
    
    # 测试健康检查
    try:
        health = vector_store.health_check()
        print(f"   健康状态: {health}")
        if health.get("status") != "healthy":
            print("   ❌ 向量存储健康检查失败")
            return False
    except Exception as e:
        print(f"   ❌ 健康检查异常: {e}")
        return False
    
    return True

def test_embedding_service():
    """测试embedding服务"""
    print("\n🧠 测试embedding服务...")
    
    embedding_service = EmbeddingService()
    
    # 检查服务是否可用
    if not embedding_service.is_available():
        print("   ❌ Embedding服务不可用")
        return False
    
    print(f"   提供商: {embedding_service.provider}")
    
    # 测试连接
    try:
        connection_test = embedding_service.test_connection()
        print(f"   连接测试: {connection_test}")
        if not connection_test.get("success", False):
            print(f"   ❌ 连接测试失败: {connection_test.get('error', '未知错误')}")
            return False
    except Exception as e:
        print(f"   ❌ 连接测试异常: {e}")
        return False
    
    # 测试单个文本embedding
    test_text = "这是一个测试文本，用于验证embedding生成功能。"
    print(f"   测试文本: {test_text}")
    
    try:
        embedding = embedding_service.generate_embedding(test_text)
        if embedding:
            print(f"   ✅ 单个embedding生成成功，维度: {len(embedding)}")
            print(f"   前5个值: {[f'{x:.4f}' for x in embedding[:5]]}")
        else:
            print("   ❌ 单个embedding生成失败")
            return False
    except Exception as e:
        print(f"   ❌ 单个embedding生成异常: {e}")
        return False
    
    # 测试批量embedding
    test_texts = [
        "人工智能是计算机科学的一个分支。",
        "机器学习是人工智能的重要组成部分。",
        "深度学习使用多层神经网络。",
        "自然语言处理处理人类语言。"
    ]
    
    print(f"   测试批量embedding: {len(test_texts)} 个文本")
    
    try:
        embeddings, failed_texts = embedding_service.batch_generate_embeddings(
            test_texts, batch_size=2, delay_between_batches=0.5
        )
        
        if embeddings:
            print(f"   ✅ 批量embedding生成成功: {len(embeddings)}/{len(test_texts)}")
            if failed_texts:
                print(f"   ⚠️  失败文本数: {len(failed_texts)}")
        else:
            print("   ❌ 批量embedding生成失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 批量embedding生成异常: {e}")
        return False
    
    return True

def test_collection_management():
    """测试集合管理"""
    print("\n📚 测试集合管理...")
    
    vector_store = VectorStore()
    test_group_id = "test_group_123"
    
    # 测试创建集合
    print(f"   为测试组 {test_group_id} 创建集合...")
    success = vector_store.create_collection_for_group(test_group_id)
    if success:
        print("   ✅ 集合创建成功")
    else:
        print("   ❌ 集合创建失败")
        return False
    
    # 测试获取集合
    print("   获取集合...")
    collection = vector_store.get_or_create_collection(test_group_id)
    if collection:
        print(f"   ✅ 集合获取成功: {collection.name}")
    else:
        print("   ❌ 集合获取失败")
        return False
    
    # 测试集合统计
    try:
        stats = vector_store.get_collection_stats(test_group_id)
        print(f"   集合统计: {stats}")
    except Exception as e:
        print(f"   ⚠️  集合统计获取失败: {e}")
    
    return True

def test_document_storage_and_retrieval():
    """测试文档存储和检索"""
    print("\n📄 测试文档存储和检索...")
    
    vector_store = VectorStore()
    embedding_service = EmbeddingService()
    test_group_id = "test_group_123"
    
    # 准备测试文档
    test_document = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

    机器学习是人工智能的一个重要分支，它是一种通过算法使机器能够从数据中学习并做出决策或预测的技术。机器学习的核心思想是让计算机通过大量数据的训练，自动发现数据中的模式和规律。

    深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。深度学习在图像识别、语音识别、自然语言处理等领域取得了突破性进展。

    自然语言处理（Natural Language Processing，NLP）是人工智能和语言学领域的分支学科。此领域探讨如何处理及运用自然语言。
    """
    
    literature_id = f"test_lit_{int(time.time())}"
    print(f"   测试文献ID: {literature_id}")
    
    # 1. 文本分块
    print("   步骤1: 文本分块...")
    chunks = split_text_into_chunks(test_document, chunk_size=300, overlap=50)
    print(f"   ✅ 分块完成: {len(chunks)} 个块")
    
    for i, chunk in enumerate(chunks):
        print(f"      块 {i+1}: {len(chunk)} 字符")
    
    # 2. 准备chunks数据
    print("   步骤2: 准备chunks数据...")
    chunks_data = prepare_chunks_for_embedding(
        chunks, literature_id, test_group_id, "人工智能技术概述"
    )
    print(f"   ✅ 数据准备完成: {len(chunks_data)} 个数据块")
    
    # 3. 生成embeddings
    print("   步骤3: 生成embeddings...")
    embeddings, failed_texts = embedding_service.batch_generate_embeddings(
        [chunk["text"] for chunk in chunks_data],
        batch_size=2,
        delay_between_batches=1.0
    )
    
    if not embeddings:
        print("   ❌ Embedding生成失败")
        return False
    
    print(f"   ✅ Embedding生成完成: {len(embeddings)} 个向量")
    print(f"   向量维度: {len(embeddings[0]) if embeddings else 0}")
    
    # 4. 存储到向量数据库
    print("   步骤4: 存储到向量数据库...")
    success = vector_store.store_document_chunks(
        chunks_data, embeddings, literature_id, test_group_id
    )
    
    if not success:
        print("   ❌ 向量存储失败")
        return False
    
    print("   ✅ 向量存储成功")
    
    # 5. 测试相似度搜索
    print("   步骤5: 测试相似度搜索...")
    
    # 生成查询embedding
    query_text = "什么是机器学习？"
    print(f"   查询文本: {query_text}")
    
    query_embedding = embedding_service.generate_embedding(query_text)
    if not query_embedding:
        print("   ❌ 查询embedding生成失败")
        return False
    
    # 执行搜索
    search_results = vector_store.search_similar_chunks(
        query_embedding, test_group_id, literature_id, top_k=3
    )
    
    if search_results:
        print(f"   ✅ 搜索成功: 找到 {len(search_results)} 个相关结果")
        for i, result in enumerate(search_results):
            similarity = result.get('similarity', result.get('distance', 0))
            print(f"      结果 {i+1}: 相似度 {similarity:.3f}")
            print(f"         文本预览: {result.get('text', '')[:100]}...")
    else:
        print("   ❌ 搜索失败或无结果")
        return False
    
    # 6. 测试删除文档
    print("   步骤6: 测试删除文档...")
    delete_success = vector_store.delete_document_chunks(literature_id, test_group_id)
    if delete_success:
        print("   ✅ 文档删除成功")
    else:
        print("   ❌ 文档删除失败")
        return False
    
    return True

def test_performance():
    """测试性能"""
    print("\n⚡ 测试性能...")
    
    embedding_service = EmbeddingService()
    
    # 测试embedding生成性能
    test_texts = [f"这是第{i}个测试文本，用于性能测试。包含一些中文内容和数字{i}。" for i in range(5)]
    
    print(f"   测试 {len(test_texts)} 个文本的embedding生成...")
    start_time = time.time()
    
    embeddings, failed = embedding_service.batch_generate_embeddings(
        test_texts, batch_size=3, delay_between_batches=0.5
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    if embeddings:
        print(f"   ✅ 性能测试完成:")
        print(f"      总时间: {duration:.2f} 秒")
        print(f"      平均每个: {duration/len(test_texts):.2f} 秒")
        print(f"      成功率: {len(embeddings)/len(test_texts)*100:.1f}%")
    else:
        print("   ❌ 性能测试失败")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🧪 向量数据库核心功能测试")
    print("="*50)
    
    tests = [
        ("配置信息", test_configuration),
        ("向量存储初始化", test_vector_store),
        ("Embedding服务", test_embedding_service),
        ("集合管理", test_collection_management),
        ("文档存储和检索", test_document_storage_and_retrieval),
        ("性能测试", test_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有向量数据库核心功能测试通过!")
        print("\n📋 功能实现总结:")
        print("   ✅ ChromaDB集成和初始化")
        print("   ✅ Google AI Studio embedding服务")
        print("   ✅ 向量集合管理")
        print("   ✅ 文档块存储和检索")
        print("   ✅ 相似度搜索")
        print("   ✅ 批量处理和性能优化")
    else:
        print("⚠️  部分测试失败，请检查实现")
        print("\n💡 可能的问题:")
        print("   - 检查.env文件中的GOOGLE_API_KEY是否正确配置")
        print("   - 确保网络连接正常，可以访问Google AI服务")
        print("   - 检查ChromaDB是否正确安装")

if __name__ == "__main__":
    main() 
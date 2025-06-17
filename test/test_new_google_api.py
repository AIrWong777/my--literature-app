#!/usr/bin/env python3
"""
新Google GenAI SDK测试脚本
验证新的google-genai库的功能
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_new_google_genai():
    """测试新的Google GenAI SDK"""
    print("🧪 测试新的Google GenAI SDK...")
    
    # 检查API密钥
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY环境变量未设置")
        return False
    
    print(f"✅ API密钥: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        from google import genai
        print("✅ google.genai库导入成功")
    except ImportError as e:
        print(f"❌ google.genai库导入失败: {e}")
        print("请运行: pip install -q -U google-genai")
        return False
    
    try:
        # 创建客户端
        client = genai.Client(api_key=api_key)
        print("✅ Google GenAI客户端创建成功")
        
        # 测试文本生成
        print("\n📝 测试文本生成...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Say hello in Chinese"
        )
        print(f"✅ 文本生成成功: {response.candidates[0].content.parts[0].text}")
        
        # 测试embedding生成
        print("\n🔢 测试embedding生成...")
        from google.genai import types
        
        embed_response = client.models.embed_content(
            model="text-embedding-004",
            contents="这是一个测试文本",
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )
        
        if embed_response.embeddings and len(embed_response.embeddings) > 0:
            embedding = embed_response.embeddings[0].values
            print(f"✅ Embedding生成成功，维度: {len(embedding)}")
            print(f"前5个值: {embedding[:5]}")
        else:
            print("❌ 未获取到embedding响应")
            return False
        
        # 测试查询embedding
        print("\n🔍 测试查询embedding...")
        query_response = client.models.embed_content(
            model="text-embedding-004",
            contents="搜索查询文本",
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY"
            )
        )
        
        if query_response.embeddings and len(query_response.embeddings) > 0:
            query_embedding = query_response.embeddings[0].values
            print(f"✅ 查询embedding生成成功，维度: {len(query_embedding)}")
        else:
            print("❌ 未获取到查询embedding响应")
            return False
        
        print("\n🎉 所有测试通过！新SDK工作正常。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_service():
    """测试我们的embedding服务"""
    print("\n🔧 测试我们的embedding服务...")
    
    try:
        sys.path.append('.')
        from app.utils.embedding_service import embedding_service
        
        # 测试连接
        result = embedding_service.test_connection()
        print(f"连接测试结果: {result}")
        
        if result.get('status') == 'success':
            print("✅ Embedding服务连接成功")
            
            # 测试embedding生成
            test_text = "这是一个测试文本，用于验证embedding生成功能。"
            embedding = embedding_service.generate_embedding(test_text)
            
            if embedding:
                print(f"✅ Embedding生成成功，维度: {len(embedding)}")
                
                # 测试查询embedding
                query = "测试查询"
                query_embedding = embedding_service.generate_query_embedding(query)
                
                if query_embedding:
                    print(f"✅ 查询embedding生成成功，维度: {len(query_embedding)}")
                    return True
                else:
                    print("❌ 查询embedding生成失败")
            else:
                print("❌ Embedding生成失败")
        else:
            print(f"❌ Embedding服务连接失败: {result.get('error')}")
        
        return False
        
    except Exception as e:
        print(f"❌ Embedding服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始Google GenAI SDK测试\n")
    
    # 测试新SDK
    sdk_success = test_new_google_genai()
    
    # 测试我们的服务
    service_success = test_embedding_service()
    
    print(f"\n📊 测试结果总结:")
    print(f"新SDK测试: {'✅ 通过' if sdk_success else '❌ 失败'}")
    print(f"服务测试: {'✅ 通过' if service_success else '❌ 失败'}")
    
    if sdk_success and service_success:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1) 
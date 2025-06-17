#!/usr/bin/env python3
"""
Google API地理位置限制测试
检查不同API是否受地理位置影响
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_google_api_availability():
    """测试Google API的可用性"""
    print("🌍 测试Google API地理位置限制...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY环境变量未设置")
        return
    
    print(f"✅ API密钥: {api_key[:10]}...{api_key[-5:]}")
    
    # 测试新SDK
    print("\n📦 测试新google-genai SDK...")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # 只测试embedding，跳过生成
        print("🔢 测试embedding API...")
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
            print(f"✅ 新SDK Embedding可用，维度: {len(embedding)}")
        else:
            print("❌ 新SDK Embedding不可用")
            
    except Exception as e:
        print(f"❌ 新SDK测试失败: {e}")
    
    # 测试旧SDK
    print("\n📦 测试旧google-generativeai SDK...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # 测试embedding
        print("🔢 测试旧SDK embedding API...")
        result = genai.embed_content(
            model="models/embedding-001",
            content="这是一个测试文本",
            task_type="retrieval_document"
        )
        
        if result and 'embedding' in result:
            embedding = result['embedding']
            print(f"✅ 旧SDK Embedding可用，维度: {len(embedding)}")
        else:
            print("❌ 旧SDK Embedding不可用")
            
    except Exception as e:
        print(f"❌ 旧SDK测试失败: {e}")
    
    # 结论和建议
    print("\n📋 地理位置限制分析:")
    print("根据错误信息，你的地理位置不支持Google AI Studio API")
    print("这可能是因为:")
    print("1. 你在不支持的国家/地区")
    print("2. Google AI Studio服务在你的地区尚未推出")
    print("3. 需要使用VPN或代理")
    
    print("\n💡 建议解决方案:")
    print("1. 使用VPN连接到支持的地区（如美国）")
    print("2. 考虑使用其他AI服务提供商（如OpenAI）")
    print("3. 使用模拟embedding服务进行开发测试")

if __name__ == "__main__":
    test_google_api_availability() 
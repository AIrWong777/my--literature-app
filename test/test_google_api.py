#!/usr/bin/env python3
"""
Google AI API测试脚本
验证Google Generative AI API的embedding功能
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_google_api():
    """测试Google AI API"""
    print("🧪 测试Google AI API...")
    
    # 检查API密钥
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY环境变量未设置")
        return False
    
    print(f"✅ API密钥已配置: {api_key[:10]}...")
    
    try:
        import google.generativeai as genai
        print("✅ google.generativeai库导入成功")
    except ImportError as e:
        print(f"❌ google.generativeai库导入失败: {e}")
        return False
    
    try:
        # 配置API密钥
        genai.configure(api_key=api_key)
        print("✅ API密钥配置成功")
        
        # 测试文本生成（验证API连接）
        print("\n📝 测试文本生成...")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, how are you?")
        print(f"✅ 文本生成成功: {response.text[:50]}...")
        
    except Exception as e:
        print(f"❌ 文本生成测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False
    
    try:
        # 测试embedding生成
        print("\n🧠 测试embedding生成...")
        
        test_text = "这是一个测试文本，用于验证embedding功能。"
        print(f"测试文本: {test_text}")
        
        # 尝试不同的模型名称
        model_names = [
            "models/embedding-001",
            "models/text-embedding-004",
            "embedding-001",
            "text-embedding-004"
        ]
        
        for model_name in model_names:
            try:
                print(f"\n尝试模型: {model_name}")
                result = genai.embed_content(
                    model=model_name,
                    content=test_text,
                    task_type="retrieval_document"
                )
                
                embedding = result['embedding']
                print(f"✅ 模型 {model_name} 成功!")
                print(f"   向量维度: {len(embedding)}")
                print(f"   前5个值: {[f'{x:.4f}' for x in embedding[:5]]}")
                return True
                
            except Exception as e:
                print(f"❌ 模型 {model_name} 失败: {e}")
                continue
        
        print("❌ 所有embedding模型都失败了")
        return False
        
    except Exception as e:
        print(f"❌ embedding测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

def test_available_models():
    """测试可用的模型列表"""
    print("\n📋 获取可用模型列表...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        
        models = genai.list_models()
        
        print("可用模型:")
        embedding_models = []
        for model in models:
            print(f"  - {model.name}")
            if 'embed' in model.name.lower():
                embedding_models.append(model.name)
        
        print(f"\nEmbedding相关模型:")
        for model in embedding_models:
            print(f"  - {model}")
            
        return embedding_models
        
    except Exception as e:
        print(f"❌ 获取模型列表失败: {e}")
        return []

if __name__ == "__main__":
    print("🚀 Google AI API 测试")
    print("="*50)
    
    # 测试API基本功能
    if test_google_api():
        print("\n🎉 Google AI API测试成功!")
    else:
        print("\n💡 尝试获取可用模型列表...")
        test_available_models()
        print("\n❌ Google AI API测试失败")
        print("\n🔧 可能的解决方案:")
        print("1. 检查GOOGLE_API_KEY是否正确")
        print("2. 确保网络连接正常")
        print("3. 检查API配额是否用完")
        print("4. 尝试使用不同的模型名称") 
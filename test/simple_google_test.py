#!/usr/bin/env python3
"""
简单的Google API测试
使用现有的google-generativeai库
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_simple_google_api():
    """简单测试Google API"""
    print("🧪 简单Google API测试...")
    
    # 检查API密钥
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY环境变量未设置")
        return False
    
    print(f"✅ API密钥: {api_key[:10]}...")
    
    try:
        import google.generativeai as genai
        print("✅ 库导入成功")
        
        # 配置API密钥
        genai.configure(api_key=api_key)
        
        # 先测试简单的文本生成
        print("\n📝 测试文本生成...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello in Chinese")
        print(f"✅ 文本生成成功: {response.text}")
        
        # 测试embedding - 最简单的调用
        print("\n🧠 测试embedding...")
        
        result = genai.embed_content(
            model="models/embedding-001",
            content="Hello world"
        )
        
        print(f"✅ Embedding成功!")
        print(f"维度: {len(result['embedding'])}")
        print(f"前3个值: {result['embedding'][:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        
        # 打印更详细的错误信息
        import traceback
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    test_simple_google_api() 
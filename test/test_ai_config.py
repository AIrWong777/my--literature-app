"""
AI配置测试脚本
验证Google Gemini和其他AI服务的配置
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_google_ai_basic():
    """测试Google AI基础连接"""
    print("🔍 测试Google AI基础连接...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY未设置")
            print("💡 请在.env文件中设置: GOOGLE_API_KEY=your-api-key")
            return False
        
        genai.configure(api_key=api_key)
        
        # 测试基础模型调用
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Hello, 请用中文回复")
        
        print(f"✅ Google AI连接成功")
        print(f"📝 测试响应: {response.text[:100]}...")
        return True
        
    except ImportError:
        print("❌ google-generativeai包未安装")
        print("💡 请运行: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Google AI连接失败: {e}")
        return False

def test_langchain_integration():
    """测试Langchain集成"""
    print("\n🔗 测试Langchain集成...")
    
    try:
        from app.utils.ai_config import get_ai_manager
        
        # 获取AI管理器
        ai_manager = get_ai_manager()
        
        # 测试连接
        success, message = ai_manager.test_connection()
        
        if success:
            print(f"✅ {message}")
            
            # 获取提供商信息
            provider_info = ai_manager.get_provider_info()
            print(f"🤖 AI提供商: {provider_info['provider']}")
            print(f"📊 LLM模型: {provider_info['llm_model']}")
            print(f"🔢 Embedding模型: {provider_info['embedding_model']}")
            print(f"💰 费用: {provider_info['cost']}")
            
            # 测试LLM
            try:
                llm = ai_manager.get_llm_client()
                response = llm.invoke("请用中文简单介绍一下人工智能")
                print(f"📝 LLM测试响应: {response.content[:100]}...")
            except Exception as e:
                print(f"⚠️ LLM测试失败: {e}")
            
            # 测试Embedding
            try:
                embedding_client = ai_manager.get_embedding_client()
                embeddings = embedding_client.embed_query("人工智能测试")
                print(f"🔢 Embedding测试: 向量维度 {len(embeddings)}")
            except Exception as e:
                print(f"⚠️ Embedding测试失败: {e}")
            
            return True
        else:
            print(f"❌ {message}")
            return False
            
    except ImportError as e:
        print(f"❌ 依赖包导入失败: {e}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Langchain集成测试失败: {e}")
        return False

def test_config_validation():
    """测试配置验证"""
    print("\n⚙️ 测试配置验证...")
    
    try:
        from app.config import settings
        
        # 验证AI配置
        is_valid, message = settings.validate_ai_config()
        
        if is_valid:
            print(f"✅ {message}")
            print(f"📊 当前AI提供商: {settings.get_ai_provider()}")
            
            if settings.get_ai_provider() == "google":
                print(f"🤖 LLM模型: {settings.GEMINI_MODEL}")
                print(f"🔢 Embedding模型: {settings.GEMINI_EMBEDDING_MODEL}")
            elif settings.get_ai_provider() == "openai":
                print(f"🤖 LLM模型: {settings.OPENAI_MODEL}")
                print(f"🔢 Embedding模型: {settings.OPENAI_EMBEDDING_MODEL}")
            
            # 显示其他配置
            print(f"📏 文本分块大小: {settings.CHUNK_SIZE}")
            print(f"🔄 分块重叠: {settings.CHUNK_OVERLAP}")
            print(f"📚 最大检索文档数: {settings.MAX_RETRIEVAL_DOCS}")
            print(f"💾 向量数据库路径: {settings.VECTOR_DB_PATH}")
            
            return True
        else:
            print(f"❌ {message}")
            return False
            
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def test_environment_setup():
    """测试环境设置"""
    print("\n🌍 测试环境设置...")
    
    # 检查.env文件
    if not os.path.exists(".env"):
        print("⚠️ .env文件不存在")
        print("💡 请复制.env.example为.env并配置API密钥")
        return False
    
    # 检查必要的环境变量
    required_vars = ["SECRET_KEY"]
    optional_vars = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]
    
    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"❌ 缺少必需的环境变量: {missing_required}")
        return False
    
    # 检查AI API密钥
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if not has_google and not has_openai:
        print("❌ 未配置任何AI API密钥")
        print("💡 请至少配置GOOGLE_API_KEY或OPENAI_API_KEY")
        return False
    
    print("✅ 环境变量配置正常")
    if has_google:
        print("🟢 Google API密钥已配置")
    if has_openai:
        print("🟢 OpenAI API密钥已配置")
    
    return True

def main():
    """主测试函数"""
    print("🚀 AI配置测试开始")
    print("=" * 50)
    
    # 运行测试
    tests = [
        ("环境设置检查", test_environment_setup),
        ("配置验证", test_config_validation),
        ("Google AI基础连接", test_google_ai_basic),
        ("Langchain集成", test_langchain_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！AI配置正常")
        print("\n📋 下一步:")
        print("1. 开始实现文本处理功能")
        print("2. 创建向量数据库")
        print("3. 实现RAG问答功能")
    else:
        print("⚠️ 部分测试失败，请检查配置")
        print("\n🔧 解决方案:")
        print("1. 检查.env文件是否存在并正确配置")
        print("2. 确保API密钥有效")
        print("3. 运行: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 
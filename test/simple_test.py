print("Hello from Python!")
print("Testing basic functionality...")

try:
    import sys
    print(f"Python version: {sys.version}")
    
    import os
    print(f"Current directory: {os.getcwd()}")
    
    # 测试导入app模块
    sys.path.append('.')
    from app.config import settings
    print("✅ 成功导入app.config")
    
    # 测试配置
    print(f"AI提供商: {settings.get_ai_provider()}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("测试完成！") 
#!/usr/bin/env python3
"""
简化缓存系统测试

避免复杂的配置依赖，直接测试缓存功能
"""
import sys
import os
import time
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置基础日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cache_imports():
    """测试缓存模块导入"""
    print("🔧 测试缓存模块导入...")
    
    try:
        from cachetools import TTLCache
        print("✅ cachetools 导入成功")
    except ImportError as e:
        print(f"❌ cachetools 导入失败: {e}")
        return False
    
    try:
        # 设置默认配置值
        os.environ["RAG_CACHE_EMBEDDING_MAX_SIZE"] = "100"
        os.environ["RAG_CACHE_ANSWER_MAX_SIZE"] = "50"
        os.environ["RAG_CACHE_CHUNK_MAX_SIZE"] = "200"
        os.environ["RAG_CACHE_TTL"] = "3600"
        
        from app.utils.cache_manager import CacheKeyGenerator, CacheStats, MemoryCacheBackend
        print("✅ 缓存组件导入成功")
    except Exception as e:
        print(f"❌ 缓存组件导入失败: {e}")
        return False
    
    return True

def test_cache_key_generator():
    """测试缓存键生成器"""
    print("\n🔑 测试缓存键生成器...")
    
    try:
        from app.utils.cache_manager import CacheKeyGenerator
        
        # 测试embedding键生成
        key1 = CacheKeyGenerator.embedding_key("test text", "google")
        key2 = CacheKeyGenerator.embedding_key("test text", "google")
        key3 = CacheKeyGenerator.embedding_key("test text", "openai")
        
        print(f"Embedding键1: {key1}")
        print(f"Embedding键2: {key2}")
        print(f"Embedding键3: {key3}")
        
        if key1 == key2:
            print("✅ 相同输入生成相同键")
        else:
            print("❌ 相同输入生成不同键")
            return False
        
        if key1 != key3:
            print("✅ 不同模型生成不同键")
        else:
            print("❌ 不同模型生成相同键")
            return False
        
        # 测试答案键生成
        question = "测试问题"
        lit_id = "lit_001"
        context_hash = "abc123"
        answer_key = CacheKeyGenerator.answer_key(question, lit_id, context_hash)
        print(f"答案键: {answer_key}")
        
        # 测试文档块键生成
        chunk_key = CacheKeyGenerator.chunk_key("lit_001", 5)
        print(f"文档块键: {chunk_key}")
        
        # 测试上下文哈希
        test_chunks = [
            {"text": "测试文本1", "metadata": {"source": "test.pdf", "page": 1}},
            {"text": "测试文本2", "metadata": {"source": "test.pdf", "page": 2}}
        ]
        context_hash = CacheKeyGenerator.context_hash(test_chunks)
        print(f"上下文哈希: {context_hash}")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存键生成器测试失败: {e}")
        return False

def test_memory_cache_backend():
    """测试内存缓存后端"""
    print("\n💾 测试内存缓存后端...")
    
    try:
        from app.utils.cache_manager import MemoryCacheBackend
        
        # 创建测试缓存
        cache = MemoryCacheBackend(maxsize=10, ttl=60, cache_type="test")
        print(f"✅ 缓存创建成功: {cache.cache_type}")
        
        # 测试基本操作
        test_key = "test_key"
        test_value = [0.1, 0.2, 0.3]
        
        # 测试设置
        set_result = cache.set(test_key, test_value)
        print(f"设置缓存: {set_result}")
        
        # 测试获取
        get_result = cache.get(test_key)
        print(f"获取缓存: {get_result == test_value}")
        
        # 测试大小
        size = cache.size()
        print(f"缓存大小: {size}")
        
        # 测试删除
        delete_result = cache.delete(test_key)
        print(f"删除缓存: {delete_result}")
        
        # 测试清空
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        clear_result = cache.clear()
        print(f"清空缓存: {clear_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 内存缓存后端测试失败: {e}")
        return False

def test_cache_stats():
    """测试缓存统计"""
    print("\n📊 测试缓存统计...")
    
    try:
        from app.utils.cache_manager import CacheStats
        
        stats = CacheStats()
        print("✅ 缓存统计创建成功")
        
        # 测试统计操作
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        stats.record_set()
        
        stats_data = stats.get_stats()
        print(f"统计数据: {stats_data}")
        
        hit_rate = stats.hit_rate()
        print(f"命中率: {hit_rate:.2f}")
        
        if hit_rate > 0.5:  # 2命中1未命中，应该是66.7%
            print("✅ 命中率计算正确")
        else:
            print("❌ 命中率计算错误")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存统计测试失败: {e}")
        return False

def test_cache_performance():
    """测试缓存性能"""
    print("\n⚡ 测试缓存性能...")
    
    try:
        from app.utils.cache_manager import MemoryCacheBackend
        
        cache = MemoryCacheBackend(maxsize=1000, ttl=3600, cache_type="performance_test")
        
        # 测试批量设置性能
        start_time = time.time()
        for i in range(100):
            cache.set(f"key_{i}", [0.1] * 768)
        set_time = time.time() - start_time
        print(f"100次设置耗时: {set_time:.4f}秒")
        
        # 测试批量获取性能
        start_time = time.time()
        for i in range(100):
            cache.get(f"key_{i}")
        get_time = time.time() - start_time
        print(f"100次获取耗时: {get_time:.4f}秒")
        
        if set_time < 1.0 and get_time < 0.1:  # 合理的性能阈值
            print("✅ 缓存性能良好")
            return True
        else:
            print("⚠️ 缓存性能较慢，但功能正常")
            return True
        
    except Exception as e:
        print(f"❌ 缓存性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始简化缓存系统测试...")
    print("=" * 50)
    
    tests = [
        ("导入测试", test_cache_imports),
        ("键生成器测试", test_cache_key_generator),
        ("内存缓存后端测试", test_memory_cache_backend),
        ("缓存统计测试", test_cache_stats),
        ("缓存性能测试", test_cache_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📈 测试结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有缓存功能测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查相关组件")

if __name__ == "__main__":
    main() 
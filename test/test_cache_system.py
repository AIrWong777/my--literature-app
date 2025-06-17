#!/usr/bin/env python3
"""
缓存系统测试

测试缓存管理器的功能和性能
"""
import sys
import os
import asyncio
import logging
import time
import json
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.utils.cache_manager import cache_manager, CacheKeyGenerator
from app.utils.embedding_service import embedding_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CacheSystemTester:
    """缓存系统测试器"""
    
    def __init__(self):
        self.test_results = {
            "cache_manager": [],
            "embedding_cache": [],
            "answer_cache": [],
            "chunk_cache": [],
            "performance": [],
            "integration": []
        }
        
    async def run_all_tests(self):
        """运行所有缓存测试"""
        print("🚀 开始缓存系统测试...")
        print("=" * 60)
        
        start_time = time.time()
        
        # 1. 缓存管理器基础测试
        await self.test_cache_manager_basic()
        
        # 2. Embedding缓存测试
        await self.test_embedding_cache()
        
        # 3. 答案缓存测试
        await self.test_answer_cache()
        
        # 4. 文档块缓存测试
        await self.test_chunk_cache()
        
        # 5. 性能测试
        await self.test_cache_performance()
        
        # 6. 集成测试
        await self.test_cache_integration()
        
        # 7. 生成测试报告
        total_time = time.time() - start_time
        self.generate_test_report(total_time)
    
    async def test_cache_manager_basic(self):
        """测试缓存管理器基础功能"""
        print("📋 测试缓存管理器基础功能...")
        
        # 测试统计功能
        try:
            stats = cache_manager.get_stats()
            self.test_results["cache_manager"].append({
                "test": "获取统计信息",
                "status": "PASS",
                "details": f"统计数据包含 {len(stats)} 个字段"
            })
        except Exception as e:
            self.test_results["cache_manager"].append({
                "test": "获取统计信息",
                "status": "FAIL",
                "details": str(e)
            })
        
        # 测试健康检查
        try:
            health = cache_manager.health_check()
            self.test_results["cache_manager"].append({
                "test": "健康检查",
                "status": "PASS",
                "details": f"健康状态: {health['status']}"
            })
        except Exception as e:
            self.test_results["cache_manager"].append({
                "test": "健康检查",
                "status": "FAIL",
                "details": str(e)
            })
        
        # 测试清空功能
        try:
            cache_manager.clear_all()
            self.test_results["cache_manager"].append({
                "test": "清空所有缓存",
                "status": "PASS",
                "details": "缓存清空成功"
            })
        except Exception as e:
            self.test_results["cache_manager"].append({
                "test": "清空所有缓存",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_embedding_cache(self):
        """测试Embedding缓存功能"""
        print("🔤 测试Embedding缓存...")
        
        test_texts = [
            "这是一个测试文本",
            "缓存测试用例",
            "Embedding向量化测试"
        ]
        
        for i, text in enumerate(test_texts):
            try:
                # 首次获取（应该缓存未命中）
                cached = cache_manager.get_embedding(text)
                if cached is None:
                    miss_status = "PASS"
                else:
                    miss_status = "FAIL"
                
                # 设置缓存
                test_embedding = [0.1] * 768  # 模拟embedding向量
                set_success = cache_manager.set_embedding(text, test_embedding)
                
                # 再次获取（应该缓存命中）
                cached_embedding = cache_manager.get_embedding(text)
                if cached_embedding and len(cached_embedding) == 768:
                    hit_status = "PASS"
                else:
                    hit_status = "FAIL"
                
                self.test_results["embedding_cache"].append({
                    "test": f"Embedding缓存测试 {i+1}",
                    "status": "PASS" if miss_status == "PASS" and set_success and hit_status == "PASS" else "FAIL",
                    "details": f"缓存未命中: {miss_status}, 设置: {set_success}, 缓存命中: {hit_status}"
                })
                
            except Exception as e:
                self.test_results["embedding_cache"].append({
                    "test": f"Embedding缓存测试 {i+1}",
                    "status": "FAIL",
                    "details": str(e)
                })
    
    async def test_answer_cache(self):
        """测试答案缓存功能"""
        print("💬 测试答案缓存...")
        
        test_question = "这篇文献的主要观点是什么？"
        test_literature_id = "test_lit_001"
        test_context = [
            {"text": "这是一个测试文档块", "metadata": {"source": "test.pdf", "page": 1}},
            {"text": "另一个测试文档块", "metadata": {"source": "test.pdf", "page": 2}}
        ]
        test_answer = {
            "answer": "这是一个测试答案",
            "confidence": 0.8,
            "metadata": {
                "model": "test",
                "tokens": 100
            }
        }
        
        try:
            # 首次获取（应该缓存未命中）
            cached = cache_manager.get_answer(test_question, test_literature_id, test_context)
            miss_status = "PASS" if cached is None else "FAIL"
            
            # 设置缓存
            set_success = cache_manager.set_answer(test_question, test_literature_id, test_context, test_answer)
            
            # 再次获取（应该缓存命中）
            cached_answer = cache_manager.get_answer(test_question, test_literature_id, test_context)
            hit_status = "PASS" if cached_answer and cached_answer.get("answer") == test_answer["answer"] else "FAIL"
            
            self.test_results["answer_cache"].append({
                "test": "答案缓存基础测试",
                "status": "PASS" if miss_status == "PASS" and set_success and hit_status == "PASS" else "FAIL",
                "details": f"缓存未命中: {miss_status}, 设置: {set_success}, 缓存命中: {hit_status}"
            })
            
            # 测试上下文哈希
            context_hash = CacheKeyGenerator.context_hash(test_context)
            hash_test = "PASS" if len(context_hash) == 16 else "FAIL"
            
            self.test_results["answer_cache"].append({
                "test": "上下文哈希生成",
                "status": hash_test,
                "details": f"哈希长度: {len(context_hash)}, 值: {context_hash}"
            })
            
        except Exception as e:
            self.test_results["answer_cache"].append({
                "test": "答案缓存测试",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_chunk_cache(self):
        """测试文档块缓存功能"""
        print("📄 测试文档块缓存...")
        
        test_literature_id = "test_lit_002"
        test_chunks = [
            (0, {"text": "第一个文档块", "metadata": {"page": 1}}),
            (1, {"text": "第二个文档块", "metadata": {"page": 1}}),
            (2, {"text": "第三个文档块", "metadata": {"page": 2}})
        ]
        
        try:
            # 首次获取（应该缓存未命中）
            cached = cache_manager.get_chunks(test_literature_id, [0, 1, 2])
            miss_status = "PASS" if cached is None else "FAIL"
            
            # 设置缓存
            set_success = cache_manager.set_chunks(test_literature_id, test_chunks)
            
            # 再次获取（应该缓存命中）
            cached_chunks = cache_manager.get_chunks(test_literature_id, [0, 1, 2])
            hit_status = "PASS" if cached_chunks and len(cached_chunks) == 3 else "FAIL"
            
            self.test_results["chunk_cache"].append({
                "test": "文档块缓存基础测试",
                "status": "PASS" if miss_status == "PASS" and set_success and hit_status == "PASS" else "FAIL",
                "details": f"缓存未命中: {miss_status}, 设置: {set_success}, 缓存命中: {hit_status}"
            })
            
        except Exception as e:
            self.test_results["chunk_cache"].append({
                "test": "文档块缓存测试",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_cache_performance(self):
        """测试缓存性能"""
        print("⚡ 测试缓存性能...")
        
        # 测试Embedding缓存性能
        test_text = "性能测试用的文本"
        
        try:
            # 清理可能存在的缓存
            cache_manager.embedding_cache.clear()
            
            # 测试设置性能
            set_times = []
            for i in range(10):
                start_time = time.time()
                cache_manager.set_embedding(f"{test_text}_{i}", [0.1] * 768)
                set_times.append(time.time() - start_time)
            
            avg_set_time = sum(set_times) / len(set_times)
            
            # 测试获取性能
            get_times = []
            for i in range(10):
                start_time = time.time()
                cache_manager.get_embedding(f"{test_text}_{i}")
                get_times.append(time.time() - start_time)
            
            avg_get_time = sum(get_times) / len(get_times)
            
            # 性能评估
            performance_ok = avg_set_time < 0.001 and avg_get_time < 0.001  # 1ms以内
            
            self.test_results["performance"].append({
                "test": "Embedding缓存性能",
                "status": "PASS" if performance_ok else "FAIL",
                "details": f"平均设置时间: {avg_set_time*1000:.2f}ms, 平均获取时间: {avg_get_time*1000:.2f}ms"
            })
            
        except Exception as e:
            self.test_results["performance"].append({
                "test": "Embedding缓存性能",
                "status": "FAIL",
                "details": str(e)
            })
        
        # 测试内存使用
        try:
            # 填充缓存
            for i in range(100):
                cache_manager.set_embedding(f"test_text_{i}", [0.1] * 768)
            
            stats = cache_manager.get_stats()
            memory_items = stats.get("total_memory_items", 0)
            
            self.test_results["performance"].append({
                "test": "内存使用测试",
                "status": "PASS" if memory_items >= 100 else "FAIL",
                "details": f"缓存项数量: {memory_items}"
            })
            
        except Exception as e:
            self.test_results["performance"].append({
                "test": "内存使用测试",
                "status": "FAIL",
                "details": str(e)
            })
    
    async def test_cache_integration(self):
        """测试缓存集成功能"""
        print("🔗 测试缓存集成...")
        
        # 测试与embedding_service的集成
        if embedding_service.is_available():
            try:
                test_text = "集成测试文本"
                
                # 清理可能存在的缓存
                cache_manager.embedding_cache.clear()
                
                # 第一次调用（应该生成新的embedding并缓存）
                start_time = time.time()
                embedding1 = embedding_service.generate_embedding(test_text)
                first_call_time = time.time() - start_time
                
                # 第二次调用（应该从缓存获取）
                start_time = time.time()
                embedding2 = embedding_service.generate_embedding(test_text)
                second_call_time = time.time() - start_time
                
                # 验证结果
                if embedding1 and embedding2 and embedding1 == embedding2:
                    improvement = ((first_call_time - second_call_time) / first_call_time) * 100 if first_call_time > 0 else 0
                    
                    self.test_results["integration"].append({
                        "test": "Embedding服务集成",
                        "status": "PASS",
                        "details": f"性能提升: {improvement:.1f}%, 首次: {first_call_time*1000:.1f}ms, 缓存: {second_call_time*1000:.1f}ms"
                    })
                else:
                    self.test_results["integration"].append({
                        "test": "Embedding服务集成",
                        "status": "FAIL",
                        "details": "embedding结果不一致或生成失败"
                    })
                
            except Exception as e:
                self.test_results["integration"].append({
                    "test": "Embedding服务集成",
                    "status": "FAIL",
                    "details": str(e)
                })
        else:
            self.test_results["integration"].append({
                "test": "Embedding服务集成",
                "status": "SKIP",
                "details": "Embedding服务不可用"
            })
        
        # 测试缓存键生成器
        try:
            # 测试embedding键生成
            key1 = CacheKeyGenerator.embedding_key("test text", "google")
            key2 = CacheKeyGenerator.embedding_key("test text", "google")
            key3 = CacheKeyGenerator.embedding_key("test text", "openai")
            
            key_consistency = key1 == key2
            key_uniqueness = key1 != key3
            
            self.test_results["integration"].append({
                "test": "缓存键生成器",
                "status": "PASS" if key_consistency and key_uniqueness else "FAIL",
                "details": f"一致性: {key_consistency}, 唯一性: {key_uniqueness}"
            })
            
        except Exception as e:
            self.test_results["integration"].append({
                "test": "缓存键生成器",
                "status": "FAIL",
                "details": str(e)
            })
    
    def generate_test_report(self, total_time: float):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 缓存系统测试报告")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for category, tests in self.test_results.items():
            if not tests:
                continue
                
            print(f"\n{category.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            for test in tests:
                status = test["status"]
                total_tests += 1
                
                if status == "PASS":
                    passed_tests += 1
                    status_icon = "✅"
                elif status == "FAIL":
                    failed_tests += 1
                    status_icon = "❌"
                else:  # SKIP
                    skipped_tests += 1
                    status_icon = "⏭️"
                
                print(f"  {status_icon} {test['test']}: {status}")
                if test.get("details"):
                    print(f"     详情: {test['details']}")
        
        # 总结
        print("\n" + "=" * 60)
        print("📈 测试总结")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"失败: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        if skipped_tests > 0:
            print(f"跳过: {skipped_tests} ({skipped_tests/total_tests*100:.1f}%)")
        print(f"总耗时: {total_time:.2f}秒")
        
        # 性能总结
        if cache_manager.stats.get_stats()["total_operations"] > 0:
            stats = cache_manager.stats.get_stats()
            print(f"\n缓存统计:")
            print(f"  命中率: {stats['hit_rate']*100:.1f}%")
            print(f"  总操作数: {stats['total_operations']}")
            print(f"  命中次数: {stats['hits']}")
            print(f"  未命中次数: {stats['misses']}")
        
        # 保存测试结果到文件
        try:
            with open("test_results_cache.json", "w", encoding="utf-8") as f:
                json.dump({
                    "summary": {
                        "total_tests": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "skipped": skipped_tests,
                        "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                        "total_time": total_time
                    },
                    "details": self.test_results,
                    "cache_stats": cache_manager.stats.get_stats()
                }, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 测试结果已保存到 test_results_cache.json")
        except Exception as e:
            print(f"\n⚠️ 保存测试结果失败: {e}")

async def main():
    """主测试函数"""
    tester = CacheSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
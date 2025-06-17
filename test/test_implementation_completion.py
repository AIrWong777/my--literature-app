#!/usr/bin/env python3
"""
第4-5天后端开发计划实现完成度测试

验证所有计划功能是否已实现
"""
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImplementationChecker:
    """实现完成度检查器"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "categories": {},
            "summary": {
                "total_features": 0,
                "implemented": 0,
                "completion_rate": 0.0
            }
        }
    
    def check_file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        return os.path.exists(file_path)
    
    def check_function_exists(self, module_path: str, function_name: str) -> bool:
        """检查函数是否存在"""
        try:
            module = __import__(module_path, fromlist=[function_name])
            return hasattr(module, function_name)
        except:
            return False
    
    def check_api_endpoint(self, endpoint_pattern: str) -> bool:
        """检查API端点是否定义（简单的文本搜索）"""
        files_to_check = ['app/main.py', 'app/routers/ai_chat.py']
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if endpoint_pattern in content:
                            return True
                except:
                    continue
        return False
    
    def check_stage1_literature_file_service(self) -> Dict:
        """检查阶段1：文献文件服务接口"""
        stage_results = {
            "name": "文献文件服务接口",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "文件查看接口",
                "check": lambda: self.check_api_endpoint("/literature/view/file/"),
                "implemented": False
            },
            {
                "name": "文献详情接口", 
                "check": lambda: self.check_api_endpoint("/literature/detail/"),
                "implemented": False
            },
            {
                "name": "权限验证工具",
                "check": lambda: self.check_file_exists("app/utils/auth_helper.py"),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def check_stage2_ai_dependencies(self) -> Dict:
        """检查阶段2：AI依赖配置 & 环境准备"""
        stage_results = {
            "name": "AI依赖配置 & 环境准备",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "requirements.txt AI依赖",
                "check": lambda: self._check_requirements_ai_deps(),
                "implemented": False
            },
            {
                "name": "AI配置管理",
                "check": lambda: self.check_file_exists("app/utils/ai_config.py"),
                "implemented": False
            },
            {
                "name": "配置文件更新",
                "check": lambda: self._check_config_ai_settings(),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def check_stage3_text_processing(self) -> Dict:
        """检查阶段3：文本处理 & 分块功能"""
        stage_results = {
            "name": "文本处理 & 分块功能",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "文本提取功能",
                "check": lambda: self.check_file_exists("app/utils/text_extractor.py"),
                "implemented": False
            },
            {
                "name": "文本分块处理",
                "check": lambda: self.check_file_exists("app/utils/text_processor.py"),
                "implemented": False
            },
            {
                "name": "异步文本处理",
                "check": lambda: self.check_file_exists("app/utils/async_processor.py"),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def check_stage4_vector_database(self) -> Dict:
        """检查阶段4：向量数据库基础"""
        stage_results = {
            "name": "向量数据库基础",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "向量存储",
                "check": lambda: self.check_file_exists("app/utils/vector_store.py"),
                "implemented": False
            },
            {
                "name": "Embedding生成服务",
                "check": lambda: self.check_file_exists("app/utils/embedding_service.py"),
                "implemented": False
            },
            {
                "name": "简化向量存储",
                "check": lambda: self.check_file_exists("app/utils/simple_vector_store.py"),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def check_stage5_rag_qa(self) -> Dict:
        """检查阶段5：RAG问答核心功能"""
        stage_results = {
            "name": "RAG问答核心功能",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "问答接口",
                "check": lambda: self.check_api_endpoint("/ai/ask"),
                "implemented": False
            },
            {
                "name": "RAG服务",
                "check": lambda: self.check_file_exists("app/utils/rag_service.py"),
                "implemented": False
            },
            {
                "name": "对话历史管理",
                "check": lambda: self.check_file_exists("app/utils/conversation_manager.py"),
                "implemented": False
            },
            {
                "name": "AI聊天路由",
                "check": lambda: self.check_file_exists("app/routers/ai_chat.py"),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def check_stage6_ai_optimization(self) -> Dict:
        """检查阶段6：AI接口优化 & 错误处理"""
        stage_results = {
            "name": "AI接口优化 & 错误处理",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "预设问题功能",
                "check": lambda: self.check_api_endpoint("/ai/preset-questions/"),
                "implemented": False
            },
            {
                "name": "错误处理器",
                "check": lambda: self.check_file_exists("app/utils/error_handler.py"),
                "implemented": False
            },
            {
                "name": "缓存系统",
                "check": lambda: self.check_file_exists("app/utils/cache_manager.py"),
                "implemented": False
            },
            {
                "name": "答案处理器",
                "check": lambda: self.check_file_exists("app/utils/answer_processor.py"),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def check_stage7_integration_testing(self) -> Dict:
        """检查阶段7：集成测试 & 验证"""
        stage_results = {
            "name": "集成测试 & 验证",
            "features": [],
            "completion": 0
        }
        
        features = [
            {
                "name": "端到端测试",
                "check": lambda: self.check_file_exists("test_ai_integration.py"),
                "implemented": False
            },
            {
                "name": "数据库更新脚本",
                "check": lambda: self.check_file_exists("update_existing_literature.py"),
                "implemented": False
            },
            {
                "name": "AI健康检查接口",
                "check": lambda: self.check_api_endpoint("/health/ai"),
                "implemented": False
            }
        ]
        
        for feature in features:
            feature["implemented"] = feature["check"]()
            stage_results["features"].append({
                "name": feature["name"],
                "implemented": feature["implemented"]
            })
        
        implemented_count = sum(1 for f in features if f["implemented"])
        stage_results["completion"] = implemented_count / len(features)
        
        return stage_results
    
    def _check_requirements_ai_deps(self) -> bool:
        """检查requirements.txt中的AI依赖"""
        if not os.path.exists("requirements.txt"):
            return False
        
        try:
            with open("requirements.txt", 'r', encoding='utf-8') as f:
                content = f.read()
                ai_deps = ['openai', 'langchain', 'tiktoken', 'chromadb', 'sentence-transformers']
                return all(dep in content for dep in ai_deps)
        except:
            return False
    
    def _check_config_ai_settings(self) -> bool:
        """检查配置文件中的AI相关设置"""
        if not os.path.exists("app/config.py"):
            return False
        
        try:
            with open("app/config.py", 'r', encoding='utf-8') as f:
                content = f.read()
                ai_configs = ['OPENAI_API_KEY', 'EMBEDDING_MODEL', 'CHUNK_SIZE']
                return any(config in content for config in ai_configs)
        except:
            return False
    
    def run_complete_check(self) -> Dict:
        """运行完整的实现检查"""
        logger.info("🔍 开始检查第4-5天后端开发计划实现完成度...")
        
        stages = [
            ("stage1", self.check_stage1_literature_file_service),
            ("stage2", self.check_stage2_ai_dependencies),
            ("stage3", self.check_stage3_text_processing),
            ("stage4", self.check_stage4_vector_database),
            ("stage5", self.check_stage5_rag_qa),
            ("stage6", self.check_stage6_ai_optimization),
            ("stage7", self.check_stage7_integration_testing)
        ]
        
        total_features = 0
        total_implemented = 0
        
        for stage_id, stage_checker in stages:
            stage_result = stage_checker()
            self.results["categories"][stage_id] = stage_result
            
            stage_features = len(stage_result["features"])
            stage_implemented = sum(1 for f in stage_result["features"] if f["implemented"])
            
            total_features += stage_features
            total_implemented += stage_implemented
            
            logger.info(f"✅ {stage_result['name']}: {stage_implemented}/{stage_features} "
                       f"({stage_result['completion']*100:.1f}%)")
        
        # 计算总体完成度
        self.results["summary"]["total_features"] = total_features
        self.results["summary"]["implemented"] = total_implemented
        self.results["summary"]["completion_rate"] = total_implemented / total_features if total_features > 0 else 0
        
        # 输出总结
        logger.info("=" * 60)
        logger.info("📊 实现完成度总结")
        logger.info("=" * 60)
        logger.info(f"总功能数: {total_features}")
        logger.info(f"已实现: {total_implemented}")
        logger.info(f"完成率: {self.results['summary']['completion_rate']*100:.1f}%")
        
        # 详细报告
        logger.info("\n📋 详细报告:")
        for stage_id, stage_data in self.results["categories"].items():
            logger.info(f"\n{stage_data['name']} ({stage_data['completion']*100:.1f}%):")
            for feature in stage_data["features"]:
                status = "✅" if feature["implemented"] else "❌"
                logger.info(f"  {status} {feature['name']}")
        
        # 保存结果
        with open('implementation_check_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n详细结果已保存到: implementation_check_results.json")
        
        return self.results

def main():
    """主函数"""
    checker = ImplementationChecker()
    results = checker.run_complete_check()
    
    # 根据完成度返回相应的退出码
    completion_rate = results["summary"]["completion_rate"]
    if completion_rate >= 0.9:
        print("\n🎉 实现度优秀！")
        sys.exit(0)
    elif completion_rate >= 0.7:
        print("\n👍 实现度良好！")
        sys.exit(0)
    else:
        print("\n⚠️ 还有部分功能需要实现")
        sys.exit(1)

if __name__ == "__main__":
    main() 
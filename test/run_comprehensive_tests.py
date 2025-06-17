#!/usr/bin/env python3
"""
综合测试运行脚本
支持新的手机号登录系统，全面测试系统功能
"""

import sys
import os
import asyncio
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试模块
from test.create_test_user import create_test_user, create_additional_test_users
from test.test_literature_upload import LiteratureUploadTester
from test.test_ai_integration import AIIntegrationTester

def check_server_running(base_url="http://localhost:8000"):
    """检查服务器是否运行"""
    import requests
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_server_check():
    """检查并提示服务器状态"""
    print("🔍 检查服务器状态...")
    
    if check_server_running():
        print("✅ 服务器正在运行")
        return True
    else:
        print("❌ 服务器未运行")
        print("请先启动服务器:")
        print("  python -m uvicorn app.main:app --reload --port 8000")
        return False

def setup_test_data():
    """设置测试数据"""
    print("\n📋 设置测试数据...")
    
    try:
        # 创建主要测试用户
        main_user_id = create_test_user()
        if not main_user_id:
            print("❌ 创建主要测试用户失败")
            return False
        
        # 创建额外测试用户
        additional_users = create_additional_test_users()
        
        print("✅ 测试数据设置完成")
        print(f"   主要测试用户: testuser (手机号: 13800000001)")
        print(f"   额外用户数量: {len(additional_users)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置测试数据失败: {e}")
        return False

def run_basic_system_tests():
    """运行基础系统测试"""
    print("\n🧪 运行基础系统测试...")
    
    try:
        # 使用subprocess运行基础系统测试
        result = subprocess.run([
            sys.executable, "test/test_system_basic.py"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        if result.returncode == 0:
            print("✅ 基础系统测试通过")
            return True
        else:
            print("❌ 基础系统测试失败")
            print(f"错误输出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 基础系统测试异常: {e}")
        return False

def run_literature_upload_tests():
    """运行文献上传测试"""
    print("\n📚 运行文献上传测试...")
    
    try:
        tester = LiteratureUploadTester()
        success = tester.run_all_tests()
        
        # 清理测试文件
        tester.cleanup()
        
        print(f"✅ 文献上传测试完成: {'通过' if success else '失败'}")
        
        return success
        
    except Exception as e:
        print(f"❌ 文献上传测试异常: {e}")
        return False

def run_ai_integration_tests():
    """运行AI集成测试"""
    print("\n🤖 运行AI集成测试...")
    
    try:
        tester = AIIntegrationTester()
        
        # 运行主要测试
        success = tester.run_all_tests()
        
        # 获取测试结果
        results = tester.test_results
        summary = results["summary"]
        
        print(f"✅ AI集成测试完成: {summary['passed']}/{summary['total']} 通过")
        
        if summary["errors"]:
            print("❌ 测试错误:")
            for error in summary["errors"][:3]:  # 只显示前3个错误
                print(f"   - {error}")
        
        return summary["passed"] > summary["total"] * 0.7
        
    except Exception as e:
        print(f"❌ AI集成测试异常: {e}")
        return False

def generate_test_report(results):
    """生成测试报告"""
    print("\n📊 生成测试报告...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if r),
            "success_rate": sum(1 for r in results.values() if r) / len(results) * 100
        }
    }
    
    # 保存到文件
    report_file = f"test_results_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"📄 测试报告已保存: {report_file}")
    
    # 打印摘要
    print("\n📈 测试摘要:")
    print(f"   总测试项: {report['summary']['total_tests']}")
    print(f"   通过测试: {report['summary']['passed_tests']}")
    print(f"   成功率: {report['summary']['success_rate']:.1f}%")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")

def main():
    """主测试流程"""
    print("🚀 启动综合测试...")
    print("=" * 60)
    
    test_results = {}
    
    # 1. 检查服务器
    if not run_server_check():
        print("\n❌ 服务器检查失败，退出测试")
        return
    
    # 2. 设置测试数据
    test_results["数据设置"] = setup_test_data()
    
    # 3. 运行基础系统测试
    test_results["基础系统测试"] = run_basic_system_tests()
    
    # 4. 运行文献上传测试
    test_results["文献上传测试"] = run_literature_upload_tests()
    
    # 5. 运行AI集成测试
    test_results["AI集成测试"] = run_ai_integration_tests()
    
    # 6. 生成测试报告
    print("\n" + "=" * 60)
    generate_test_report(test_results)
    
    # 7. 最终结果
    overall_success = all(test_results.values())
    if overall_success:
        print("\n🎉 所有测试通过！系统运行正常")
    else:
        print("\n⚠️ 部分测试失败，请检查具体问题")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
测试日志功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.error_handler import log_error, log_success, logger

def test_logging():
    """测试日志功能"""
    print("🔍 测试日志功能...")
    
    # 测试成功日志
    log_success("test_operation", "test_user_123", {
        "test_data": "这是一个测试",
        "timestamp": "2025-05-25"
    })
    
    # 测试错误日志
    try:
        raise Exception("这是一个测试异常")
    except Exception as e:
        log_error("test_error", e, "test_user_123", {
            "error_context": "测试错误处理"
        })
    
    # 直接使用logger
    logger.info("直接使用logger记录信息")
    logger.warning("这是一个警告消息")
    logger.error("这是一个错误消息")
    
    print("✅ 日志测试完成")
    print("📄 请检查 literature_system.log 文件")

if __name__ == "__main__":
    test_logging()
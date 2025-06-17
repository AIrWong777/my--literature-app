#!/usr/bin/env python3
"""
数据库迁移脚本：创建Literature表
运行此脚本来在现有数据库中添加Literature表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.models.research_group import Base
from app.models import Literature, User, ResearchGroup, UserResearchGroup

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./literature_system.db"

def create_literature_table():
    """创建Literature表"""
    print("🔧 开始创建Literature表...")
    
    try:
        # 创建数据库引擎
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        
        # 创建所有表（如果不存在）
        Base.metadata.create_all(bind=engine)
        
        print("✅ Literature表创建成功!")
        print("📋 当前数据库包含以下表:")
        
        # 显示所有表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            print(f"  - {table}")
            
        # 显示Literature表的列信息
        if 'literature' in tables:
            print("\n📝 Literature表结构:")
            columns = inspector.get_columns('literature')
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建Literature表失败: {e}")
        return False

def verify_table_creation():
    """验证表是否正确创建"""
    print("\n🔍 验证表创建...")
    
    try:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        
        # 测试连接和查询
        with engine.connect() as conn:
            # 检查literature表是否存在 - 使用text()包装SQL语句
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='literature'"))
            if result.fetchone():
                print("✅ Literature表存在")
                
                # 检查表结构
                result = conn.execute(text("PRAGMA table_info(literature)"))
                columns = result.fetchall()
                print(f"✅ Literature表有 {len(columns)} 个列")
                
                return True
            else:
                print("❌ Literature表不存在")
                return False
                
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("📚 Literature表创建脚本")
    print("="*50)
    
    # 1. 创建表
    if create_literature_table():
        # 2. 验证创建
        if verify_table_creation():
            print("\n🎉 Literature表创建和验证完成!")
            print("现在可以开始使用文献上传功能了。")
        else:
            print("\n⚠️  表创建成功但验证失败，请检查数据库状态")
    else:
        print("\n❌ 表创建失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
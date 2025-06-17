#!/usr/bin/env python3
"""
数据库重建脚本：重新创建所有数据库表
运行此脚本来重新创建数据库，解决模型关系映射问题
"""

import sys
import os
import shutil
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.models.research_group import Base
from app.models.user import User
from app.models.research_group import ResearchGroup, UserResearchGroup
from app.models.literature import Literature
from app.models.conversation import QASession, ConversationTurn, ConversationSummary

# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./literature_system.db"
BACKUP_DATABASE_URL = f"sqlite:///./literature_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_existing_database():
    """备份现有数据库"""
    print("🔄 备份现有数据库...")
    
    try:
        if os.path.exists("literature_system.db"):
            backup_filename = f"literature_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2("literature_system.db", backup_filename)
            print(f"✅ 数据库已备份到: {backup_filename}")
            return backup_filename
        else:
            print("ℹ️  没有找到现有数据库文件")
            return None
    except Exception as e:
        print(f"❌ 备份数据库失败: {e}")
        return None

def rebuild_database():
    """重建数据库"""
    print("🔧 开始重建数据库...")
    
    try:
        # 删除现有数据库文件
        if os.path.exists("literature_system.db"):
            os.remove("literature_system.db")
            print("🗑️  已删除现有数据库文件")
        
        # 创建数据库引擎
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✅ 数据库重建成功!")
        print("📋 创建的表:")
        
        # 显示所有表
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            print(f"  - {table}")
            
        return True, engine
        
    except Exception as e:
        print(f"❌ 重建数据库失败: {e}")
        return False, None

def verify_relationships():
    """验证模型关系"""
    print("\n🔍 验证模型关系...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from app.models.user import User
        from app.models.research_group import ResearchGroup
        from app.models.literature import Literature
        from app.models.conversation import QASession
        
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 测试查询各个模型
        user_count = db.query(User).count()
        group_count = db.query(ResearchGroup).count()
        literature_count = db.query(Literature).count()
        session_count = db.query(QASession).count()
        
        print(f"✅ User 表: {user_count} 条记录")
        print(f"✅ ResearchGroup 表: {group_count} 条记录")
        print(f"✅ Literature 表: {literature_count} 条记录")
        print(f"✅ QASession 表: {session_count} 条记录")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 验证关系失败: {e}")
        return False

def create_test_data():
    """创建测试数据"""
    print("\n🧪 创建测试数据...")
    
    try:
        from sqlalchemy.orm import sessionmaker
        from app.models.user import User
        from app.models.research_group import ResearchGroup, UserResearchGroup
        from passlib.context import CryptContext
        
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 创建密码加密上下文
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 创建测试用户
        test_user = User(
            username="testuser",
            email="test@example.com",
            password_hash=pwd_context.hash("testpassword")
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 创建测试研究组
        test_group = ResearchGroup(
            name="测试研究组",
            institution="测试机构",
            description="这是一个测试研究组",
            research_area="人工智能"
        )
        db.add(test_group)
        db.commit()
        db.refresh(test_group)
        
        # 创建用户-研究组关联
        membership = UserResearchGroup(
            user_id=test_user.id,
            group_id=test_group.id
        )
        db.add(membership)
        db.commit()
        
        print(f"✅ 创建测试用户: {test_user.username} (ID: {test_user.id})")
        print(f"✅ 创建测试研究组: {test_group.name} (ID: {test_group.id})")
        print(f"✅ 邀请码: {test_group.invitation_code}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        return False

def main():
    """主函数"""
    print("🔄 数据库重建脚本")
    print("="*50)
    
    # 1. 备份现有数据库
    backup_file = backup_existing_database()
    
    # 2. 重建数据库
    success, engine = rebuild_database()
    if not success:
        print("\n❌ 数据库重建失败")
        sys.exit(1)
    
    # 3. 验证关系
    if verify_relationships():
        print("\n✅ 模型关系验证成功")
    else:
        print("\n⚠️  模型关系验证失败")
    
    # 4. 创建测试数据
    if create_test_data():
        print("\n✅ 测试数据创建成功")
    else:
        print("\n⚠️  测试数据创建失败")
    
    print("\n🎉 数据库重建完成!")
    print("现在可以重新启动应用程序了。")
    
    if backup_file:
        print(f"💾 原数据库已备份到: {backup_file}")

if __name__ == "__main__":
    main() 
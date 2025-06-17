#!/usr/bin/env python3
"""
创建测试用户脚本 - 支持手机号登录
"""
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.user import User
from app.models.research_group import ResearchGroup, UserResearchGroup
from app.auth import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_user():
    """创建测试用户"""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 检查用户是否已存在（通过用户名）
        existing_user = db.query(User).filter(User.username == "testuser").first()
        if existing_user:
            logger.info(f"测试用户已存在: {existing_user.username} (手机号: {existing_user.phone_number})")
            return existing_user.id
        
        # 检查手机号是否已存在
        existing_phone = db.query(User).filter(User.phone_number == "13800000001").first()
        if existing_phone:
            logger.info(f"手机号已被使用: 13800000001 (用户: {existing_phone.username})")
            return existing_phone.id
        
        # 创建测试用户
        hashed_password = get_password_hash("testpass123")
        test_user = User(
            username="testuser",
            email="testuser@example.com",
            phone_number="13800000001",  # 添加手机号
            password_hash=hashed_password
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        logger.info(f"创建测试用户成功: {test_user.username} (ID: {test_user.id}, 手机号: {test_user.phone_number})")
        
        # 创建测试研究组
        existing_group = db.query(ResearchGroup).filter(ResearchGroup.name == "测试研究组").first()
        if not existing_group:
            test_group = ResearchGroup(
                name="测试研究组",
                institution="测试机构",
                description="用于测试的研究组",
                research_area="测试领域"
            )
            
            db.add(test_group)
            db.commit()
            db.refresh(test_group)
            
            # 添加用户到研究组
            membership = UserResearchGroup(
                user_id=test_user.id,
                group_id=test_group.id
            )
            db.add(membership)
            db.commit()
            
            logger.info(f"创建测试研究组成功: {test_group.name} (ID: {test_group.id})")
            logger.info(f"邀请码: {test_group.invitation_code}")
        else:
            # 检查用户是否已在组中
            existing_membership = db.query(UserResearchGroup).filter(
                UserResearchGroup.user_id == test_user.id,
                UserResearchGroup.group_id == existing_group.id
            ).first()
            
            if not existing_membership:
                membership = UserResearchGroup(
                    user_id=test_user.id,
                    group_id=existing_group.id
                )
                db.add(membership)
                db.commit()
                logger.info(f"将用户添加到现有测试研究组: {existing_group.name}")
            else:
                logger.info("用户已在测试研究组中")
        
        return test_user.id
        
    except Exception as e:
        logger.error(f"创建测试用户失败: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_additional_test_users():
    """创建更多测试用户"""
    db_gen = get_db()
    db = next(db_gen)
    
    additional_users = [
        {"username": "testuser2", "phone": "13800000002", "name": "测试用户2"},
        {"username": "testuser3", "phone": "13800000003", "name": "测试用户3"},
    ]
    
    created_users = []
    
    try:
        for user_info in additional_users:
            existing_user = db.query(User).filter(User.username == user_info["username"]).first()
            if existing_user:
                logger.info(f"{user_info['name']}已存在")
                created_users.append(existing_user.id)
                continue
            
            existing_phone = db.query(User).filter(User.phone_number == user_info["phone"]).first()
            if existing_phone:
                logger.info(f"手机号 {user_info['phone']} 已被使用")
                created_users.append(existing_phone.id)
                continue
            
            hashed_password = get_password_hash("testpass123")
            new_user = User(
                username=user_info["username"],
                email=f"{user_info['username']}@example.com",
                phone_number=user_info["phone"],
                password_hash=hashed_password
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"创建{user_info['name']}成功: {new_user.username} (手机号: {new_user.phone_number})")
            created_users.append(new_user.id)
        
        return created_users
        
    except Exception as e:
        logger.error(f"创建额外测试用户失败: {e}")
        db.rollback()
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("=== 创建测试用户和数据 ===")
    
    # 创建主要测试用户
    main_user_id = create_test_user()
    if main_user_id:
        print(f"✅ 主要测试用户创建成功: {main_user_id}")
    else:
        print("❌ 主要测试用户创建失败")
    
    # 创建额外测试用户
    additional_users = create_additional_test_users()
    if additional_users:
        print(f"✅ 额外测试用户创建成功: {len(additional_users)} 个")
    
    print("\n=== 测试用户信息 ===")
    print("主要测试用户:")
    print("  用户名: testuser")
    print("  手机号: 13800000001")
    print("  密码: testpass123")
    print("\n额外测试用户:")
    print("  testuser2 - 13800000002 - testpass123")
    print("  testuser3 - 13800000003 - testpass123")
    print("\n所有用户都已加入'测试研究组'") 
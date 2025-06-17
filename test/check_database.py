#!/usr/bin/env python3
"""
数据库状态检查脚本
用于验证用户、课题组、成员关系、文献是否正确存储
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = "literature_system.db"

def check_database_exists():
    """检查数据库文件是否存在"""
    try:
        import os
        if os.path.exists(DB_PATH):
            print(f"✅ 数据库文件存在: {DB_PATH}")
            return True
        else:
            print(f"❌ 数据库文件不存在: {DB_PATH}")
            return False
    except Exception as e:
        print(f"❌ 检查数据库文件错误: {e}")
        return False

def connect_database():
    """连接数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def check_tables(conn):
    """检查数据表是否存在"""
    print("\n📋 检查数据表...")
    
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"发现表: {[table[0] for table in tables]}")
    
    required_tables = ['users', 'research_groups', 'user_research_groups', 'literature']
    
    for table in required_tables:
        if any(table in t[0] for t in tables):
            print(f"✅ 表 '{table}' 存在")
        else:
            print(f"❌ 表 '{table}' 不存在")

def check_users(conn):
    """检查用户数据"""
    print("\n👥 检查用户数据...")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"用户总数: {user_count}")
        
        if user_count > 0:
            cursor.execute("SELECT id, username, email FROM users LIMIT 5")
            users = cursor.fetchall()
            print("用户列表:")
            for user in users:
                print(f"  - ID: {user[0][:8]}..., 用户名: {user[1]}, 邮箱: {user[2]}")
        else:
            print("⚠️  没有用户数据，请运行 create_test_user.py")
            
    except Exception as e:
        print(f"❌ 查询用户数据错误: {e}")

def check_research_groups(conn):
    """检查研究组数据"""
    print("\n🏢 检查研究组数据...")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM research_groups")
        group_count = cursor.fetchone()[0]
        print(f"研究组总数: {group_count}")
        
        if group_count > 0:
            cursor.execute("SELECT id, name, institution, invitation_code FROM research_groups")
            groups = cursor.fetchall()
            print("研究组列表:")
            for group in groups:
                print(f"  - ID: {group[0][:8]}...")
                print(f"    名称: {group[1]}")
                print(f"    机构: {group[2]}")
                print(f"    邀请码: {group[3]}")
                print()
        else:
            print("ℹ️  没有研究组数据")
            
    except Exception as e:
        print(f"❌ 查询研究组数据错误: {e}")

def check_literature(conn):
    """检查文献数据"""
    print("\n📚 检查文献数据...")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM literature")
        lit_count = cursor.fetchone()[0]
        print(f"文献总数: {lit_count}")
        
        if lit_count > 0:
            # 联合查询显示详细文献信息
            query = """
            SELECT l.id, l.title, l.filename, l.file_size, l.file_type, 
                   l.upload_time, l.status, u.username, rg.name
            FROM literature l
            JOIN users u ON l.uploaded_by = u.id
            JOIN research_groups rg ON l.research_group_id = rg.id
            ORDER BY l.upload_time DESC
            """
            cursor.execute(query)
            literature = cursor.fetchall()
            
            print("文献列表:")
            for lit in literature:
                print(f"  - ID: {lit[0][:8]}...")
                print(f"    标题: {lit[1]}")
                print(f"    文件名: {lit[2]}")
                print(f"    文件大小: {lit[3]} 字节")
                print(f"    文件类型: {lit[4]}")
                print(f"    上传时间: {lit[5]}")
                print(f"    状态: {lit[6]}")
                print(f"    上传者: {lit[7]}")
                print(f"    所属研究组: {lit[8]}")
                print()
        else:
            print("ℹ️  没有文献数据")
            
    except Exception as e:
        print(f"❌ 查询文献数据错误: {e}")

def check_memberships(conn):
    """检查成员关系数据"""
    print("\n🤝 检查成员关系...")
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM user_research_groups")
        membership_count = cursor.fetchone()[0]
        print(f"成员关系总数: {membership_count}")
        
        if membership_count > 0:
            # 联合查询显示详细成员关系
            query = """
            SELECT u.username, rg.name 
            FROM user_research_groups urg
            JOIN users u ON urg.user_id = u.id
            JOIN research_groups rg ON urg.group_id = rg.id
            """
            cursor.execute(query)
            memberships = cursor.fetchall()
            
            print("成员关系:")
            for membership in memberships:
                print(f"  - 用户 '{membership[0]}' 加入了 '{membership[1]}'")
        else:
            print("ℹ️  没有成员关系数据")
            
    except Exception as e:
        print(f"❌ 查询成员关系错误: {e}")

def check_table_structure(conn):
    """检查表结构"""
    print("\n🏗️  检查表结构...")
    
    cursor = conn.cursor()
    tables_to_check = ['users', 'research_groups', 'user_research_groups', 'literature']
    
    for table in tables_to_check:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n表 '{table}' 的列:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        except Exception as e:
            print(f"❌ 检查表 '{table}' 结构错误: {e}")

def main():
    """主检查函数"""
    print("🔍 数据库状态检查")
    print("="*50)
    
    # 1. 检查数据库文件
    if not check_database_exists():
        print("\n请先运行应用创建数据库，或检查数据库路径")
        sys.exit(1)
    
    # 2. 连接数据库
    conn = connect_database()
    if not conn:
        sys.exit(1)
    
    try:
        # 3. 检查表
        check_tables(conn)
        
        # 4. 检查表结构
        check_table_structure(conn)
        
        # 5. 检查数据
        check_users(conn)
        check_research_groups(conn)
        check_literature(conn)
        check_memberships(conn)
        
    finally:
        conn.close()
        print("\n✅ 数据库连接已关闭")
    
    print("\n" + "="*50)
    print("🎯 数据库检查完成!")

if __name__ == "__main__":
    main()
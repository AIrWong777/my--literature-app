#!/usr/bin/env python3
import sqlite3

def view_database():
    conn = sqlite3.connect('literature_system.db')
    cursor = conn.cursor()
    
    print("🔍 AI+协同文献管理系统 - 数据库完整内容")
    print("=" * 80)
    
    # 1. 用户信息
    print("\n👥 用户列表:")
    print("-" * 40)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for i, user in enumerate(users, 1):
        print(f"{i}. ID: {user[0]}")
        print(f"   用户名: {user[1]}")
        print(f"   邮箱: {user[2] if user[2] else '未设置'}")
        print(f"   手机号: {user[3]}")
        print(f"   密码(加密): {user[4][:20]}...")
        print()
    
    # 2. 研究组信息
    print("\n🏢 研究组列表:")
    print("-" * 40)
    cursor.execute("SELECT * FROM research_groups")
    groups = cursor.fetchall()
    for i, group in enumerate(groups, 1):
        print(f"{i}. ID: {group[0]}")
        print(f"   名称: {group[1]}")
        print(f"   机构: {group[2]}")
        print(f"   描述: {group[3]}")
        print(f"   研究领域: {group[4]}")
        print(f"   邀请码: {group[5]}")
        print()
    
    # 3. 文献信息 - 先查看字段结构
    print("\n📚 文献列表:")
    print("-" * 40)
    cursor.execute("PRAGMA table_info(literature)")
    lit_columns = [col[1] for col in cursor.fetchall()]
    print(f"文献表字段: {', '.join(lit_columns)}")
    
    cursor.execute("SELECT * FROM literature")
    literature = cursor.fetchall()
    if not literature:
        print("暂无文献")
    else:
        for i, lit in enumerate(literature, 1):
            print(f"\n{i}. 文献信息:")
            for j, field in enumerate(lit_columns):
                if j < len(lit):
                    value = lit[j]
                    if field == 'abstract' and value and len(str(value)) > 100:
                        value = str(value)[:100] + "..."
                    print(f"   {field}: {value}")
    
    # 4. 检查其他可能的表
    print("\n📋 其他表信息:")
    print("-" * 40)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [table[0] for table in cursor.fetchall()]
    
    for table in all_tables:
        if table not in ['users', 'research_groups', 'literature']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} 条记录")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    for row in rows:
                        print(f"  样本: {row}")
            except Exception as e:
                print(f"{table}: 查询失败 - {e}")
    
    conn.close()

if __name__ == "__main__":
    view_database() 
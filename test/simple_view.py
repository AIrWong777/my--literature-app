#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的数据库内容查看工具
"""

import sqlite3
from datetime import datetime

def connect_db():
    """连接数据库"""
    return sqlite3.connect('literature_system.db')

def get_table_info():
    """获取表结构信息"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("🔍 数据库表结构信息")
    print("=" * 60)
    
    for table in tables:
        table_name = table[0]
        print(f"\n📊 表: {table_name}")
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"字段: {', '.join([col[1] for col in columns])}")
        
        # 获取记录数
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"记录数: {count}")
        
        # 如果记录数不为0，显示前几条数据
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            print("样本数据:")
            for i, row in enumerate(rows, 1):
                print(f"  {i}: {row}")
    
    conn.close()

def view_simple_data():
    """简单查看各表数据"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📋 详细数据内容")
    print("=" * 60)
    
    # 查看用户数据
    print("\n👥 用户信息:")
    try:
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for i, user in enumerate(users, 1):
            print(f"  用户{i}: {user}")
    except Exception as e:
        print(f"  查看用户表出错: {e}")
    
    # 查看研究组数据
    print("\n🏢 研究组信息:")
    try:
        cursor.execute("SELECT * FROM research_groups")
        groups = cursor.fetchall()
        for i, group in enumerate(groups, 1):
            print(f"  研究组{i}: {group}")
    except Exception as e:
        print(f"  查看研究组表出错: {e}")
    
    # 查看文献数据
    print("\n📚 文献信息:")
    try:
        cursor.execute("SELECT * FROM literature")
        literature = cursor.fetchall()
        for i, lit in enumerate(literature, 1):
            print(f"  文献{i}: {lit}")
    except Exception as e:
        print(f"  查看文献表出错: {e}")
    
    # 查看研究组成员关系
    print("\n👥 研究组成员关系:")
    try:
        cursor.execute("SELECT * FROM group_members")
        members = cursor.fetchall()
        for i, member in enumerate(members, 1):
            print(f"  成员关系{i}: {member}")
    except Exception as e:
        print(f"  查看成员关系表出错: {e}")
    
    conn.close()

def main():
    """主函数"""
    print("🔍 AI+协同文献管理系统 - 数据库内容查看")
    print(f"查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 获取表结构信息
        get_table_info()
        
        # 查看详细数据
        view_simple_data()
        
    except Exception as e:
        print(f"❌ 查看数据库时出错: {e}")

if __name__ == "__main__":
    main() 
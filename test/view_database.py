#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库内容查看工具
用于查看 literature_system.db 中的所有数据
"""

import sqlite3
import json
from datetime import datetime

def connect_db():
    """连接数据库"""
    return sqlite3.connect('literature_system.db')

def view_users():
    """查看用户表"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("👥 用户表 (users)")
    print("=" * 60)
    
    cursor.execute("SELECT id, username, phone_number, created_at FROM users")
    users = cursor.fetchall()
    
    if not users:
        print("暂无用户数据")
    else:
        print(f"{'ID':<40} {'用户名':<15} {'手机号':<15} {'创建时间':<20}")
        print("-" * 90)
        for user in users:
            user_id, username, phone, created_at = user
            print(f"{user_id:<40} {username:<15} {phone:<15} {created_at:<20}")
    
    conn.close()
    print()

def view_groups():
    """查看研究组表"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🏢 研究组表 (research_groups)")
    print("=" * 60)
    
    cursor.execute("""
        SELECT id, name, institution, description, research_area, 
               invitation_code, created_at 
        FROM research_groups
    """)
    groups = cursor.fetchall()
    
    if not groups:
        print("暂无研究组数据")
    else:
        print(f"{'ID':<40} {'名称':<20} {'机构':<15}")
        print("-" * 75)
        for group in groups:
            group_id, name, institution, desc, area, code, created_at = group
            print(f"{group_id:<40} {name:<20} {institution:<15}")
            print(f"  描述: {desc}")
            print(f"  研究领域: {area}")
            print(f"  邀请码: {code}")
            print(f"  创建时间: {created_at}")
            print()
    
    conn.close()

def view_literature():
    """查看文献表"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📚 文献表 (literature)")
    print("=" * 60)
    
    cursor.execute("""
        SELECT id, title, authors, abstract, keywords, 
               upload_date, file_path, uploader_id
        FROM literature 
        ORDER BY upload_date DESC
        LIMIT 10
    """)
    literature = cursor.fetchall()
    
    if not literature:
        print("暂无文献数据")
    else:
        for lit in literature:
            lit_id, title, authors, abstract, keywords, upload_date, file_path, uploader_id = lit
            print(f"ID: {lit_id}")
            print(f"标题: {title}")
            print(f"作者: {authors}")
            print(f"摘要: {abstract[:100]}..." if abstract and len(abstract) > 100 else f"摘要: {abstract}")
            print(f"关键词: {keywords}")
            print(f"上传时间: {upload_date}")
            print(f"上传者ID: {uploader_id}")
            print(f"文件路径: {file_path}")
            print("-" * 80)
    
    conn.close()

def view_group_members():
    """查看研究组成员关系"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("👥 研究组成员关系 (group_members)")
    print("=" * 60)
    
    cursor.execute("""
        SELECT gm.group_id, gm.user_id, gm.role, gm.joined_at,
               u.username, rg.name as group_name
        FROM group_members gm
        JOIN users u ON gm.user_id = u.id
        JOIN research_groups rg ON gm.group_id = rg.id
        ORDER BY gm.joined_at DESC
    """)
    members = cursor.fetchall()
    
    if not members:
        print("暂无成员关系数据")
    else:
        print(f"{'研究组':<20} {'用户名':<15} {'角色':<10} {'加入时间':<20}")
        print("-" * 65)
        for member in members:
            group_id, user_id, role, joined_at, username, group_name = member
            print(f"{group_name:<20} {username:<15} {role:<10} {joined_at:<20}")
    
    conn.close()
    print()

def view_conversations():
    """查看AI对话记录"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🤖 AI对话记录 (conversations)")
    print("=" * 60)
    
    cursor.execute("""
        SELECT id, user_id, title, created_at, updated_at
        FROM conversations 
        ORDER BY updated_at DESC
        LIMIT 5
    """)
    conversations = cursor.fetchall()
    
    if not conversations:
        print("暂无对话记录")
    else:
        for conv in conversations:
            conv_id, user_id, title, created_at, updated_at = conv
            print(f"对话ID: {conv_id}")
            print(f"用户ID: {user_id}")
            print(f"标题: {title}")
            print(f"创建时间: {created_at}")
            print(f"更新时间: {updated_at}")
            print("-" * 40)
    
    conn.close()

def view_table_info():
    """查看数据库表结构信息"""
    conn = connect_db()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("📊 数据库表统计信息")
    print("=" * 60)
    
    tables = [
        ('users', '用户'),
        ('research_groups', '研究组'),
        ('literature', '文献'),
        ('group_members', '研究组成员'),
        ('conversations', 'AI对话'),
        ('messages', '消息记录')
    ]
    
    for table_name, table_desc in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_desc}({table_name}): {count} 条记录")
        except sqlite3.OperationalError:
            print(f"{table_desc}({table_name}): 表不存在")
    
    conn.close()
    print()

def main():
    """主函数"""
    print("🔍 AI+协同文献管理系统 - 数据库内容查看")
    print("=" * 60)
    print(f"查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 查看表统计信息
        view_table_info()
        
        # 查看用户信息
        view_users()
        
        # 查看研究组信息
        view_groups()
        
        # 查看研究组成员关系
        view_group_members()
        
        # 查看文献信息
        view_literature()
        
        # 查看对话记录
        view_conversations()
        
    except Exception as e:
        print(f"❌ 查看数据库时出错: {e}")

if __name__ == "__main__":
    main() 
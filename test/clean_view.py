#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime
import re

def connect_db():
    return sqlite3.connect('literature_system.db')

def print_section(title, emoji="📋"):
    print(f"\n{emoji} {title}")
    print("=" * 60)

def view_users():
    conn = connect_db()
    cursor = conn.cursor()
    
    print_section("用户列表", "👥")
    
    try:
        cursor.execute("SELECT id, username, email, phone_number FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("暂无用户")
        else:
            for i, user in enumerate(users, 1):
                user_id, username, email, phone = user
                print(f"{i}. 用户名: {username}")
                print(f"   手机号: {phone}")
                print(f"   邮箱: {email}")
                print(f"   ID: {user_id}")
                print()
    except Exception as e:
        print(f"查看用户表出错: {e}")
    
    conn.close()

def view_groups():
    conn = connect_db()
    cursor = conn.cursor()
    
    print_section("研究组列表", "🏢")
    
    try:
        cursor.execute("SELECT id, name, institution, description, research_area, invitation_code FROM research_groups")
        groups = cursor.fetchall()
        
        if not groups:
            print("暂无研究组")
        else:
            for i, group in enumerate(groups, 1):
                group_id, name, institution, description, research_area, invitation_code = group
                print(f"{i}. 研究组名称: {name}")
                print(f"   所属机构: {institution}")
                print(f"   研究领域: {research_area}")
                print(f"   描述: {description}")
                print(f"   邀请码: {invitation_code}")
                print(f"   ID: {group_id}")
                print()
    except Exception as e:
        print(f"查看研究组表出错: {e}")
    
    conn.close()

def view_literature():
    conn = connect_db()
    cursor = conn.cursor()
    
    print_section("文献列表", "📚")
    
    try:
        cursor.execute("SELECT id, title, authors, abstract, keywords, upload_date, file_path FROM literature")
        literature = cursor.fetchall()
        
        if not literature:
            print("暂无文献")
        else:
            for i, lit in enumerate(literature, 1):
                lit_id, title, authors, abstract, keywords, upload_date, file_path = lit
                print(f"{i}. 标题: {title}")
                print(f"   作者: {authors}")
                print(f"   关键词: {keywords}")
                if abstract:
                    abstract_short = abstract[:100] + "..." if len(abstract) > 100 else abstract
                    print(f"   摘要: {abstract_short}")
                print(f"   上传时间: {upload_date}")
                print(f"   文件路径: {file_path}")
                print(f"   ID: {lit_id}")
                print()
    except Exception as e:
        print(f"查看文献表出错: {e}")
    
    conn.close()

def view_group_members():
    conn = connect_db()
    cursor = conn.cursor()
    
    print_section("研究组成员关系", "👥")
    
    try:
        cursor.execute("""
            SELECT gm.group_id, gm.user_id, gm.role, 
                   u.username, rg.name as group_name
            FROM group_members gm
            LEFT JOIN users u ON gm.user_id = u.id
            LEFT JOIN research_groups rg ON gm.group_id = rg.id
        """)
        members = cursor.fetchall()
        
        if not members:
            print("暂无成员关系")
        else:
            for i, member in enumerate(members, 1):
                group_id, user_id, role, username, group_name = member
                print(f"{i}. 研究组: {group_name}")
                print(f"   用户: {username}")
                print(f"   角色: {role}")
                print(f"   用户ID: {user_id}")
                print(f"   研究组ID: {group_id}")
                print()
    except Exception as e:
        print(f"查看成员关系表出错: {e}")
    
    conn.close()

def view_summary():
    conn = connect_db()
    cursor = conn.cursor()
    
    print_section("数据概览", "📊")
    
    tables = [
        ('users', '用户'),
        ('research_groups', '研究组'),
        ('literature', '文献'),
        ('group_members', '研究组成员关系'),
        ('conversations', 'AI对话'),
        ('messages', '消息记录')
    ]
    
    for table_name, table_desc in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_desc}: {count} 条记录")
        except sqlite3.OperationalError:
            print(f"{table_desc}: 表不存在")
    
    conn.close()

def main():
    print("🔍 AI+协同文献管理系统 - 数据库内容")
    print(f"查看时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        view_summary()
        view_users()
        view_groups()
        view_group_members()
        view_literature()
    except Exception as e:
        print(f"❌ 查看数据库时出错: {e}")

if __name__ == "__main__":
    main() 
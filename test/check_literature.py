#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的文献记录
"""

import sqlite3
import os
from pathlib import Path

def check_literature():
    """检查数据库中的文献记录"""
    
    # 连接数据库
    try:
        conn = sqlite3.connect('literature_system.db')
        cursor = conn.cursor()
        
        # 查询文献记录
        cursor.execute('SELECT id, title, file_path, file_size FROM literature ORDER BY file_size DESC LIMIT 10')
        results = cursor.fetchall()
        
        print('文献记录（按文件大小排序）:')
        for row in results:
            lit_id, title, file_path, file_size = row
            exists = os.path.exists(file_path) if file_path else False
            size_mb = (file_size / 1024 / 1024) if file_size else 0
            print(f'ID: {lit_id}')
            print(f'  标题: {title[:80] if title else "无标题"}...')
            print(f'  路径: {file_path}')
            print(f'  大小: {size_mb:.2f} MB')
            print(f'  存在: {exists}')
            print('-' * 50)
        
        # 查找最大的几个PDF文件
        print('\n查找最大的PDF文件...')
        cursor.execute('''
        SELECT id, title, file_path, file_size 
        FROM literature 
        WHERE file_path IS NOT NULL 
        AND file_path LIKE '%.pdf' 
        AND file_size > 100000
        ORDER BY file_size DESC 
        LIMIT 5
        ''')
        
        pdf_results = cursor.fetchall()
        for row in pdf_results:
            lit_id, title, file_path, file_size = row
            exists = os.path.exists(file_path) if file_path else False
            if exists:
                size_mb = (file_size / 1024 / 1024) if file_size else 0
                print(f'找到大PDF文件: {file_path} ({size_mb:.2f} MB)')
        
        conn.close()
        
    except Exception as e:
        print(f'检查数据库时出错: {e}')

if __name__ == "__main__":
    check_literature() 
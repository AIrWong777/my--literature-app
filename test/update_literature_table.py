#!/usr/bin/env python3
"""
数据库迁移脚本：为Literature表添加软删除字段
"""

import sqlite3
import sys
import os

DB_PATH = "literature_system.db"

def add_soft_delete_columns():
    """为Literature表添加软删除相关字段"""
    print("🔧 为Literature表添加软删除字段...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(literature)")
        columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = [
            ("deleted_at", "DATETIME"),
            ("deleted_by", "VARCHAR"),
            ("delete_reason", "TEXT"),
            ("restored_at", "DATETIME"),
            ("restored_by", "VARCHAR")
        ]
        
        added_columns = []
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE literature ADD COLUMN {col_name} {col_type}")
                    added_columns.append(col_name)
                    print(f"   ✅ 添加字段: {col_name} ({col_type})")
                except Exception as e:
                    print(f"   ❌ 添加字段失败 {col_name}: {e}")
            else:
                print(f"   ℹ️  字段已存在: {col_name}")
        
        conn.commit()
        conn.close()
        
        if added_columns:
            print(f"✅ 成功添加 {len(added_columns)} 个字段")
        else:
            print("ℹ️  所有字段都已存在，无需添加")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

def verify_migration():
    """验证迁移是否成功"""
    print("\n🔍 验证迁移结果...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(literature)")
        columns = cursor.fetchall()
        
        print("📋 Literature表当前字段:")
        for col in columns:
            print(f"   - {col[1]}: {col[2]}")
        
        # 检查必要字段是否存在
        column_names = [col[1] for col in columns]
        required_fields = ["deleted_at", "deleted_by", "delete_reason", "restored_at", "restored_by"]
        
        missing_fields = [field for field in required_fields if field not in column_names]
        
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
            return False
        else:
            print("✅ 所有必要字段都已存在")
            return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("📚 Literature表软删除字段迁移")
    print("="*40)
    
    # 1. 添加字段
    if add_soft_delete_columns():
        # 2. 验证迁移
        if verify_migration():
            print("\n🎉 数据库迁移完成!")
            print("现在Literature表支持软删除功能了。")
        else:
            print("\n⚠️  迁移完成但验证失败，请检查数据库状态")
    else:
        print("\n❌ 数据库迁移失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
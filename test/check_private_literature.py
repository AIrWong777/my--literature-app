#!/usr/bin/env python3
"""
检查私人文献状态和向量存储
"""
import sqlite3
import os
from pathlib import Path

def check_private_literature():
    """检查私人文献"""
    print("🔍 检查私人文献...")
    
    try:
        conn = sqlite3.connect('literature_system.db')
        cursor = conn.cursor()
        
        # 查询私人文献
        cursor.execute("""
        SELECT id, title, filename, uploaded_by, upload_time, status 
        FROM literature 
        WHERE research_group_id IS NULL 
        ORDER BY upload_time DESC
        """)
        
        private_docs = cursor.fetchall()
        
        if private_docs:
            print(f"📚 找到 {len(private_docs)} 篇私人文献：")
            for doc in private_docs:
                print(f"  ID: {doc[0]}")
                print(f"  标题: {doc[1]}")
                print(f"  文件: {doc[2]}")
                print(f"  上传者: {doc[3]}")
                print(f"  状态: {doc[5]}")
                print("  ---")
        else:
            print("📚 未找到私人文献")
            
        conn.close()
        return private_docs
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return []

def check_vector_collections():
    """检查向量集合"""
    print("\n🔍 检查向量集合...")
    
    vector_db_path = "./vector_db"
    if not os.path.exists(vector_db_path):
        print("❌ 向量数据库目录不存在")
        return False
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path=vector_db_path)
        collections = client.list_collections()
        
        print(f"📊 找到 {len(collections)} 个向量集合：")
        for collection in collections:
            print(f"  - {collection.name}")
            
        # 检查是否有private集合
        has_private = any("private" in c.name for c in collections)
        if has_private:
            print("✅ 找到私人文献向量集合")
            
            # 查看private集合的详细信息
            private_collection = next(c for c in collections if "private" in c.name)
            count = private_collection.count()
            print(f"   私人文献向量数量: {count}")
        else:
            print("❌ 未找到私人文献向量集合")
            
        return True
        
    except Exception as e:
        print(f"❌ 检查向量集合失败: {e}")
        return False

def create_private_vector_collection():
    """为私人文献创建向量集合"""
    print("\n🛠️ 创建私人文献向量集合...")
    
    try:
        from app.utils.vector_store import vector_store
        
        # 为私人文献创建集合（group_id传None）
        success = vector_store.create_collection_for_group(None)
        
        if success:
            print("✅ 私人文献向量集合创建成功")
        else:
            print("❌ 私人文献向量集合创建失败")
            
        return success
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

def reprocess_private_literature():
    """重新处理私人文献的向量"""
    print("\n🔄 重新处理私人文献向量...")
    
    private_docs = check_private_literature()
    if not private_docs:
        print("没有需要处理的私人文献")
        return
    
    print("⚠️ 注意：重新处理向量需要重新上传文献")
    print("建议步骤：")
    print("1. 删除并重新上传私人文献")
    print("2. 或者运行文档处理脚本重新生成向量")
    
    # 创建向量集合
    create_private_vector_collection()

def main():
    """主函数"""
    print("🚀 私人文献状态检查工具")
    print("=" * 40)
    
    # 1. 检查私人文献
    private_docs = check_private_literature()
    
    # 2. 检查向量集合
    vector_ok = check_vector_collections()
    
    # 3. 如果有私人文献但没有向量集合，尝试修复
    if private_docs and not vector_ok:
        reprocess_private_literature()
    elif private_docs:
        print("\n✅ 私人文献和向量集合都存在")
    else:
        print("\n📝 没有私人文献需要处理")

if __name__ == "__main__":
    main() 
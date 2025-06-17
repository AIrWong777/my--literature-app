#!/usr/bin/env python3
"""
修复私人文献向量存储问题
"""
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_private_collection():
    """创建私人文献向量集合"""
    print("🛠️ 创建私人文献向量集合...")
    
    try:
        from app.utils.vector_store import vector_store
        
        # 为私人文献创建集合（group_id=None）
        success = vector_store.create_collection_for_group(None)
        
        if success:
            print("✅ 私人文献向量集合创建成功")
            return True
        else:
            print("❌ 私人文献向量集合创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

def check_collections():
    """检查集合状态"""
    print("\n🔍 检查向量集合...")
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./vector_db")
        collections = client.list_collections()
        
        print(f"📊 找到 {len(collections)} 个向量集合：")
        for collection in collections:
            print(f"  - {collection.name}")
            
        # 检查private集合
        has_private = any("private" in c.name for c in collections)
        if has_private:
            print("✅ 私人文献向量集合存在")
            private_collection = next(c for c in collections if "private" in c.name)
            count = private_collection.count()
            print(f"   向量数量: {count}")
        else:
            print("❌ 私人文献向量集合不存在")
            
        return has_private
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 修复私人文献向量存储")
    print("=" * 40)
    
    # 1. 检查当前状态
    has_private = check_collections()
    
    # 2. 如果没有私人集合，创建它
    if not has_private:
        print("\n需要创建私人文献向量集合...")
        success = create_private_collection()
        
        if success:
            # 再次检查
            check_collections()
            print("\n✅ 修复完成!")
            print("💡 建议：")
            print("1. 重启后端服务器")
            print("2. 重新上传私人文献以生成向量")
        else:
            print("\n❌ 修复失败")
    else:
        print("\n✅ 私人文献向量集合已存在，无需修复")

if __name__ == "__main__":
    main() 
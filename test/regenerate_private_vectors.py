#!/usr/bin/env python3
"""
为现有私人文献重新生成向量
"""
import sys
import os
import sqlite3
from pathlib import Path

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_private_literature():
    """获取私人文献列表"""
    try:
        conn = sqlite3.connect('literature_system.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, title, filename, file_path, uploaded_by 
        FROM literature 
        WHERE research_group_id IS NULL AND status = 'active'
        """)
        
        docs = cursor.fetchall()
        conn.close()
        return docs
        
    except Exception as e:
        print(f"❌ 获取私人文献失败: {e}")
        return []

def process_literature_file(lit_id, file_path, title):
    """处理单个文献文件，生成向量"""
    print(f"📄 处理文献: {title}")
    
    try:
        # 修复文件路径 - 确保使用正确的路径格式
        if not os.path.exists(file_path):
            # 尝试修复路径格式
            if "\\" in file_path:
                file_path = file_path.replace("\\", "/")
            if not file_path.startswith("uploads/"):
                file_path = f"uploads/{file_path}"
            
            print(f"🔧 修正后的文件路径: {file_path}")
        
        # 再次检查文件是否存在
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            
            # 尝试寻找替代文件名
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            base_name = filename.split('_')[0]  # 去掉后缀数字
            
            if os.path.exists(directory):
                # 列出目录中的文件
                files = os.listdir(directory)
                matching_files = [f for f in files if f.startswith(base_name) and f.endswith('.pdf')]
                
                if matching_files:
                    file_path = os.path.join(directory, matching_files[0])
                    print(f"🔍 找到替代文件: {file_path}")
                else:
                    print(f"❌ 在目录 {directory} 中未找到匹配的文件")
                    return False
            else:
                print(f"❌ 目录不存在: {directory}")
                return False
        
        # 导入所需模块
        from app.utils.text_extractor import extract_text_from_file
        from app.utils.text_processor import split_text_into_chunks, prepare_chunks_for_embedding
        from app.utils.vector_store import vector_store
        
        # 1. 提取文本
        print(f"📝 提取文本...")
        extracted_text = extract_text_from_file(file_path)
        if not extracted_text:
            print(f"❌ 文本提取失败")
            return False
        
        print(f"📊 提取文本长度: {len(extracted_text)} 字符")
        
        # 2. 分割文本为块
        print(f"🔪 分割文本为块...")
        chunks = split_text_into_chunks(extracted_text)
        if not chunks:
            print(f"❌ 文本分块失败")
            return False
            
        print(f"📊 分割为 {len(chunks)} 个文本块")
        
        # 3. 准备文本块数据
        chunks_data = prepare_chunks_for_embedding(
            chunks=chunks,
            literature_id=lit_id,
            group_id=None,  # 私人文献group_id为None
            literature_title=title
        )
        
        if not chunks_data:
            print(f"❌ 文档处理失败，未提取到文本块")
            return False
        
        print(f"📊 提取到 {len(chunks_data)} 个文本块")
        
        # 4. 生成embedding
        print(f"🧠 生成向量...")
        from app.utils.embedding_service import embedding_service
        texts = [chunk['text'] for chunk in chunks_data]
        embeddings, failed = embedding_service.batch_generate_embeddings(texts)
        
        if not embeddings or len(embeddings) != len(chunks_data):
            print(f"❌ 向量生成失败")
            return False
        
        print(f"📊 生成了 {len(embeddings)} 个向量")
        
        # 5. 存储向量
        success = vector_store.store_document_chunks(
            chunks_data=chunks_data,
            embeddings=embeddings,
            literature_id=lit_id,
            group_id=None  # 私人文献
        )
        
        if success:
            print(f"✅ 向量生成成功")
            return True
        else:
            print(f"❌ 向量生成失败")
            return False
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_vector_count():
    """检查私人向量数量"""
    try:
        from app.utils.vector_store import vector_store
        
        # 检查集合统计信息
        stats = vector_store.get_collection_stats(None)  # None表示私人文献
        
        if "error" in stats:
            print(f"❌ 检查向量数量失败: {stats['error']}")
            return 0
        
        count = stats.get("total_chunks", 0)
        print(f"📊 私人文献向量数量: {count}")
        return count
        
    except Exception as e:
        print(f"❌ 检查向量数量失败: {e}")
        return 0

def main():
    """主函数"""
    print("🚀 私人文献向量重新生成工具")
    print("=" * 50)
    
    # 1. 检查当前向量数量
    print("🔍 检查当前向量数量...")
    initial_count = check_vector_count()
    
    # 2. 获取私人文献
    print("\n📚 获取私人文献列表...")
    private_docs = get_private_literature()
    
    if not private_docs:
        print("📝 没有找到私人文献")
        return
    
    print(f"找到 {len(private_docs)} 篇私人文献")
    
    # 3. 逐个处理文献
    print("\n🔄 开始重新生成向量...")
    success_count = 0
    
    for doc in private_docs:
        lit_id, title, filename, file_path, uploaded_by = doc
        print(f"\n处理文献 {success_count + 1}/{len(private_docs)}:")
        print(f"  ID: {lit_id}")
        print(f"  标题: {title}")
        print(f"  文件: {filename}")
        
        if process_literature_file(lit_id, file_path, title):
            success_count += 1
        
        print("-" * 30)
    
    # 4. 检查最终结果
    print(f"\n📊 处理完成!")
    print(f"成功处理: {success_count}/{len(private_docs)} 篇文献")
    
    final_count = check_vector_count()
    print(f"向量数量变化: {initial_count} → {final_count}")
    
    if final_count > initial_count:
        print("✅ 向量生成成功，现在可以测试AI助手功能了！")
    else:
        print("⚠️ 向量数量没有增加，请检查文档处理器是否正常工作")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
修复AI配置和向量存储问题

主要功能：
1. 检查AI配置
2. 修复私人文献的向量存储
3. 重新处理已上传的文献
"""
import os
import sys
import sqlite3
from pathlib import Path

def check_ai_config():
    """检查AI配置"""
    print("🔍 检查AI配置...")
    
    # 检查环境变量
    google_api_key = os.getenv("GOOGLE_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if google_api_key and google_api_key != "请替换为您的Google_API_密钥":
        print("✅ Google API配置已设置")
        return True
    elif openai_api_key:
        print("✅ OpenAI API配置已设置")
        return True
    else:
        print("❌ 未配置AI API密钥")
        print("\n请按以下步骤配置：")
        print("1. 复制 env_example.txt 为 .env")
        print("2. 在 .env 文件中设置 GOOGLE_API_KEY=您的密钥")
        print("3. 获取Google API密钥：https://aistudio.google.com/app/apikey")
        return False

def check_private_literature():
    """检查数据库中的私人文献"""
    print("\n🔍 检查私人文献...")
    
    try:
        conn = sqlite3.connect('literature_system.db')
        cursor = conn.cursor()
        
        # 查询私人文献
        cursor.execute("""
        SELECT id, title, filename, uploaded_by, research_group_id 
        FROM literature 
        WHERE research_group_id IS NULL AND status = 'active'
        """)
        
        private_literature = cursor.fetchall()
        
        if private_literature:
            print(f"📚 找到 {len(private_literature)} 篇私人文献：")
            for lit in private_literature[:5]:  # 只显示前5篇
                print(f"  - {lit[1]} ({lit[2]})")
            if len(private_literature) > 5:
                print(f"  ... 还有 {len(private_literature) - 5} 篇")
        else:
            print("📚 未找到私人文献")
            
        conn.close()
        return private_literature
        
    except Exception as e:
        print(f"❌ 检查私人文献失败: {e}")
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
        else:
            print("❌ 未找到私人文献向量集合")
            
        return True
        
    except Exception as e:
        print(f"❌ 检查向量集合失败: {e}")
        return False

def create_env_file():
    """创建.env文件"""
    if not os.path.exists('.env'):
        print("\n📝 创建.env文件...")
        
        try:
            with open('env_example.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换示例内容
            content = content.replace('请替换为您的Google_API_密钥', 'YOUR_GOOGLE_API_KEY_HERE')
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
                
            print("✅ .env文件已创建")
            print("⚠️  请在 .env 文件中设置您的 GOOGLE_API_KEY")
            return True
            
        except Exception as e:
            print(f"❌ 创建.env文件失败: {e}")
            return False
    else:
        print("✅ .env文件已存在")
        return True

def test_ai_service():
    """测试AI服务"""
    print("\n🧪 测试AI服务...")
    
    try:
        # 加载环境变量
        from dotenv import load_dotenv
        load_dotenv()
        
        # 检查Google AI
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key and google_api_key not in ["YOUR_GOOGLE_API_KEY_HERE", "请替换为您的Google_API_密钥"]:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_api_key)
                
                # 测试生成模型
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                response = model.generate_content("测试")
                
                print("✅ Google AI服务正常")
                return True
                
            except Exception as e:
                print(f"❌ Google AI测试失败: {e}")
                print("   请检查API密钥是否正确")
                return False
        else:
            print("❌ Google API密钥未配置或无效")
            return False
            
    except Exception as e:
        print(f"❌ AI服务测试失败: {e}")
        return False

def cleanup_vector_db():
    """清理并重建向量数据库"""
    print("\n🧹 清理向量数据库...")
    
    try:
        vector_db_path = "./vector_db"
        if os.path.exists(vector_db_path):
            import shutil
            shutil.rmtree(vector_db_path)
            print("✅ 已清理旧的向量数据库")
        
        # 重新创建目录
        os.makedirs(vector_db_path, exist_ok=True)
        print("✅ 重新创建向量数据库目录")
        return True
        
    except Exception as e:
        print(f"❌ 清理向量数据库失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 AI+协同文献管理平台 - 配置修复工具")
    print("=" * 50)
    
    # 1. 创建.env文件
    create_env_file()
    
    # 2. 检查AI配置
    ai_configured = check_ai_config()
    
    # 3. 检查私人文献
    private_literature = check_private_literature()
    
    # 4. 检查向量集合
    vector_ok = check_vector_collections()
    
    # 5. 测试AI服务（如果配置了）
    if ai_configured:
        ai_working = test_ai_service()
    else:
        ai_working = False
    
    print("\n" + "=" * 50)
    print("📋 诊断总结：")
    print(f"  - AI配置: {'✅' if ai_configured else '❌'}")
    print(f"  - AI服务: {'✅' if ai_working else '❌'}")
    print(f"  - 私人文献: {len(private_literature)} 篇")
    print(f"  - 向量数据库: {'✅' if vector_ok else '❌'}")
    
    if not ai_working:
        print("\n💡 解决建议：")
        print("1. 获取Google API密钥：https://aistudio.google.com/app/apikey")
        print("2. 在 .env 文件中设置 GOOGLE_API_KEY")
        print("3. 重启后端服务器")
        
    if private_literature and not vector_ok:
        print("4. 重新上传私人文献以创建向量索引")
        
        # 询问是否清理向量数据库
        while True:
            choice = input("\n是否清理并重建向量数据库？这将删除所有现有的向量数据。(y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                cleanup_vector_db()
                print("⚠️  请重新上传所有文献以重建向量索引")
                break
            elif choice in ['n', 'no', '否']:
                print("跳过向量数据库清理")
                break
            else:
                print("请输入 y 或 n")

if __name__ == "__main__":
    main() 
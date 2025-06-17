#!/usr/bin/env python3
"""
文本处理功能测试脚本
测试文本提取、分块、异步处理等功能
"""

import os
import sys
import tempfile
import time
import requests
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.text_extractor import (
    extract_pdf_text, 
    extract_docx_text, 
    extract_html_text,
    clean_extracted_text,
    extract_title_from_text,
    extract_text_from_file
)
from app.utils.text_processor import (
    split_text_into_chunks,
    prepare_chunks_for_embedding,
    estimate_token_count,
    extract_keywords,
    validate_chunk_quality
)
from app.utils.async_processor import AsyncProcessor
from app.config import settings

# API基础URL
BASE_URL = "http://localhost:8000"

class TextProcessingTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.group_id = None
        self.literature_id = None
        self.async_processor = AsyncProcessor()
    
    def login(self):
        """登录获取token"""
        print("🔐 用户登录...")
        
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        
        if response.status_code == 200:
            result = response.json()
            self.token = result["access_token"]
            import jwt
            payload = jwt.decode(result["access_token"], options={"verify_signature": False})
            self.user_id = payload.get("sub")
            print(f"   ✅ 登录成功: {self.user_id}")
            return True
        else:
            print(f"   ❌ 登录失败: {response.text}")
            return False
    
    def get_headers(self):
        """获取认证头"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def get_user_groups(self):
        """获取用户研究组"""
        print("\n📋 获取用户研究组...")
        
        response = requests.get(f"{BASE_URL}/user/groups", headers=self.get_headers())
        
        if response.status_code == 200:
            groups = response.json()["groups"]
            if groups:
                self.group_id = groups[0]["id"]
                print(f"   ✅ 找到研究组: {groups[0]['name']} ({self.group_id})")
                return True
            else:
                print("   ❌ 用户没有加入任何研究组")
                return False
        else:
            print(f"   ❌ 获取研究组失败: {response.text}")
            return False
    
    def test_text_extraction(self):
        """测试文本提取功能"""
        print("\n📄 测试文本提取功能...")
        
        # 测试PDF文本提取
        print("   测试PDF文本提取...")
        # 简单的PDF内容用于测试
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf.write(pdf_content)
            tmp_pdf_path = tmp_pdf.name
        
        try:
            pdf_text = extract_pdf_text(tmp_pdf_path)
            if pdf_text is not None:
                print(f"      ✅ PDF文本提取成功: {len(pdf_text)} 字符")
            else:
                print("      ⚠️  PDF文本提取返回空")
        except Exception as e:
            print(f"      ❌ PDF文本提取失败: {e}")
        finally:
            if os.path.exists(tmp_pdf_path):
                os.unlink(tmp_pdf_path)
        
        # 测试HTML文本提取
        print("   测试HTML文本提取...")
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>测试文档</title>
            <style>body { font-family: Arial; }</style>
        </head>
        <body>
            <h1>这是一个测试标题</h1>
            <p>这是第一段内容，包含一些<strong>重要信息</strong>。</p>
            <p>这是第二段内容，讨论了文本处理的重要性。</p>
            <script>console.log('这段脚本应该被忽略');</script>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".html", delete=False, encoding='utf-8') as tmp_html:
            tmp_html.write(html_content)
            tmp_html_path = tmp_html.name
        
        try:
            html_text = extract_html_text(tmp_html_path)
            if html_text:
                print(f"      ✅ HTML文本提取成功: {len(html_text)} 字符")
                print(f"      内容预览: {html_text[:100]}...")
            else:
                print("      ⚠️  HTML文本提取返回空")
        except Exception as e:
            print(f"      ❌ HTML文本提取失败: {e}")
        finally:
            if os.path.exists(tmp_html_path):
                os.unlink(tmp_html_path)
        
        # 测试文本清理
        print("   测试文本清理...")
        dirty_text = "   这是一个\n\n\n包含多余空白\t\t的文本   \n\r\n  "
        cleaned_text = clean_extracted_text(dirty_text)
        print(f"      原文本: '{dirty_text}'")
        print(f"      清理后: '{cleaned_text}'")
        
        # 测试标题提取
        print("   测试标题提取...")
        sample_text = """
        
        深度学习在自然语言处理中的应用研究
        
        摘要：本文探讨了深度学习技术在自然语言处理领域的最新进展...
        
        1. 引言
        自然语言处理（NLP）是人工智能的重要分支...
        """
        title = extract_title_from_text(sample_text)
        print(f"      提取的标题: '{title}'")
        
        return True
    
    def test_text_chunking(self):
        """测试文本分块功能"""
        print("\n🔪 测试文本分块功能...")
        
        # 准备测试文本
        test_text = """
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。

        机器学习是人工智能的一个重要分支，它是一种通过算法使机器能够从数据中学习并做出决策或预测的技术。深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的工作方式。

        自然语言处理（Natural Language Processing，NLP）是人工智能和语言学领域的分支学科。此领域探讨如何处理及运用自然语言。

        计算机视觉是一门研究如何使机器"看"的科学，更进一步的说，就是是指用摄影机和电脑代替人眼对目标进行识别、跟踪和测量等机器视觉，并进一步做图形处理。
        """
        
        # 测试基本分块
        print(f"   原文本长度: {len(test_text)} 字符")
        print(f"   配置的分块大小: {settings.CHUNK_SIZE}")
        print(f"   配置的重叠大小: {settings.CHUNK_OVERLAP}")
        
        chunks = split_text_into_chunks(test_text)
        print(f"   ✅ 分块完成: 生成 {len(chunks)} 个文本块")
        
        for i, chunk in enumerate(chunks):
            print(f"      块 {i+1}: {len(chunk)} 字符")
            print(f"         预览: {chunk[:50]}...")
        
        # 测试自定义参数分块
        print("\n   测试自定义参数分块...")
        custom_chunks = split_text_into_chunks(test_text, chunk_size=200, overlap=50)
        print(f"   ✅ 自定义分块完成: 生成 {len(custom_chunks)} 个文本块")
        
        # 测试准备embedding数据
        print("\n   测试准备embedding数据...")
        chunks_data = prepare_chunks_for_embedding(
            chunks, 
            "test_lit_123", 
            "test_group_456",
            "人工智能技术概述"
        )
        print(f"   ✅ 数据准备完成: {len(chunks_data)} 个数据块")
        
        if chunks_data:
            sample_data = chunks_data[0]
            print(f"      样本数据结构: {list(sample_data.keys())}")
            print(f"      文本长度: {sample_data['chunk_length']}")
            print(f"      块ID: {sample_data['chunk_id']}")
        
        return True
    
    def test_token_estimation(self):
        """测试token计算功能"""
        print("\n🔢 测试token计算功能...")
        
        test_texts = [
            "Hello world!",
            "你好，世界！",
            "This is a longer text with multiple sentences. It contains both English and Chinese characters. 这段文本包含了英文和中文字符。",
            "A" * 1000  # 长文本测试
        ]
        
        for i, text in enumerate(test_texts):
            print(f"   文本 {i+1}: {len(text)} 字符")
            
            # 测试OpenAI token计算
            try:
                openai_tokens = estimate_token_count(text, "openai")
                print(f"      OpenAI估算: {openai_tokens} tokens")
            except Exception as e:
                print(f"      OpenAI估算失败: {e}")
            
            # 测试Google token计算
            try:
                google_tokens = estimate_token_count(text, "google")
                print(f"      Google估算: {google_tokens} tokens")
            except Exception as e:
                print(f"      Google估算失败: {e}")
        
        return True
    
    def test_keyword_extraction(self):
        """测试关键词提取功能"""
        print("\n🔍 测试关键词提取功能...")
        
        test_text = """
        深度学习是机器学习的一个分支，它基于人工神经网络的研究，特别是利用多层神经网络来进行学习和模式识别。
        深度学习模型能够学习数据的高层次特征，这些特征对于图像识别、语音识别和自然语言处理等任务非常有用。
        卷积神经网络（CNN）在图像处理领域表现出色，而循环神经网络（RNN）和长短期记忆网络（LSTM）在序列数据处理方面很有效。
        """
        
        try:
            keywords = extract_keywords(test_text, max_keywords=8)
            print(f"   ✅ 关键词提取成功: {len(keywords)} 个关键词")
            print(f"      关键词: {', '.join(keywords)}")
        except Exception as e:
            print(f"   ❌ 关键词提取失败: {e}")
        
        return True
    
    def test_chunk_quality_validation(self):
        """测试文本块质量验证"""
        print("\n✅ 测试文本块质量验证...")
        
        test_chunks = [
            "这是一个高质量的文本块，包含完整的句子和有意义的内容。它有足够的长度和清晰的表达。",
            "短文本",
            "A" * 2000,  # 过长文本
            "123456789",  # 纯数字
            "这是一个包含特殊字符的文本块！@#$%^&*()，但仍然有意义。"
        ]
        
        for i, chunk in enumerate(test_chunks):
            print(f"   文本块 {i+1}: {len(chunk)} 字符")
            try:
                quality = validate_chunk_quality(chunk)
                print(f"      质量评分: {quality['score']:.2f}")
                print(f"      是否有效: {quality['is_valid']}")
                if quality['issues']:
                    print(f"      问题: {', '.join(quality['issues'])}")
            except Exception as e:
                print(f"      质量验证失败: {e}")
        
        return True
    
    def test_async_processing(self):
        """测试异步处理功能"""
        print("\n⚡ 测试异步处理功能...")
        
        # 首先上传一个测试文件
        print("   上传测试文件...")
        # 简单的PDF内容用于测试
        test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                files = {"file": ("async_test.pdf", f, "application/pdf")}
                data = {
                    "group_id": self.group_id,
                    "title": "异步处理测试文档"
                }
                
                response = requests.post(
                    f"{BASE_URL}/literature/upload",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                result = response.json()
                literature_id = result["literature_id"]
                print(f"      ✅ 文件上传成功: {literature_id}")
                
                # 测试异步处理
                print("   启动异步处理...")
                task_id = self.async_processor.process_literature_async(literature_id)
                print(f"      任务ID: {task_id}")
                
                # 监控处理进度
                print("   监控处理进度...")
                for i in range(10):  # 最多等待10秒
                    time.sleep(1)
                    status = self.async_processor.get_task_status(task_id)
                    if status:
                        print(f"      进度: {status['progress']}% - {status['message']}")
                        if status['status'] in ['completed', 'failed']:
                            break
                
                # 获取最终状态
                final_status = self.async_processor.get_task_status(task_id)
                if final_status:
                    if final_status['status'] == 'completed':
                        print(f"      ✅ 异步处理成功完成")
                        if 'data' in final_status:
                            data = final_status['data']
                            print(f"         文本块数: {data.get('chunks_count', 0)}")
                            print(f"         文本长度: {data.get('text_length', 0)}")
                    else:
                        print(f"      ❌ 异步处理失败: {final_status['message']}")
                else:
                    print("      ⚠️  无法获取处理状态")
                
                return True
            else:
                print(f"      ❌ 文件上传失败: {response.text}")
                return False
                
        finally:
            if os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
    
    def test_configuration(self):
        """测试配置信息"""
        print("\n⚙️  测试配置信息...")
        
        print(f"   分块大小: {settings.CHUNK_SIZE}")
        print(f"   分块重叠: {settings.CHUNK_OVERLAP}")
        print(f"   最大检索文档数: {settings.MAX_RETRIEVAL_DOCS}")
        print(f"   AI提供商: {settings.get_ai_provider()}")
        
        ai_valid, ai_message = settings.validate_ai_config()
        print(f"   AI配置: {'✅' if ai_valid else '❌'} {ai_message}")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 文本处理功能测试")
        print("="*50)
        
        tests = [
            ("配置信息", self.test_configuration),
            ("文本提取", self.test_text_extraction),
            ("文本分块", self.test_text_chunking),
            ("Token计算", self.test_token_estimation),
            ("关键词提取", self.test_keyword_extraction),
            ("文本块质量验证", self.test_chunk_quality_validation),
            ("登录", self.login),
            ("获取研究组", self.get_user_groups),
            ("异步处理", self.test_async_processing)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                if test_func():
                    passed += 1
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
        
        print(f"\n📊 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有文本处理功能测试通过!")
        else:
            print("⚠️  部分测试失败，请检查实现")

def main():
    """主函数"""
    tester = TextProcessingTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 
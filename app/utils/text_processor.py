"""
文本处理工具
用于文本分块、预处理和token计算
"""

import re
import logging
from typing import List, Dict, Optional
from app.config import settings

# 配置日志
logger = logging.getLogger(__name__)

def split_text_into_chunks(
    text: str, 
    chunk_size: int = None, 
    overlap: int = None,
    preserve_paragraphs: bool = True
) -> List[str]:
    """
    将文本分割成块
    
    Args:
        text: 要分割的文本
        chunk_size: 每块的大小（字符数）
        overlap: 块之间的重叠大小
        preserve_paragraphs: 是否尽量保持段落完整
        
    Returns:
        List[str]: 分割后的文本块列表
    """
    if not text or not text.strip():
        return []
    
    # 使用配置中的默认值
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    
    # 确保overlap不超过chunk_size的一半
    overlap = min(overlap, chunk_size // 2)
    
    chunks = []
    
    if preserve_paragraphs:
        # 按段落分割，尽量保持段落完整
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前段落加上现有chunk不超过限制，就添加
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个段落就超过了chunk_size，需要强制分割
                if len(paragraph) > chunk_size:
                    sub_chunks = _force_split_text(paragraph, chunk_size, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)
    
    else:
        # 简单的固定大小分割
        chunks = _force_split_text(text, chunk_size, overlap)
    
    # 清理和验证chunks
    cleaned_chunks = []
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk and len(chunk) >= 50:  # 过滤太短的chunk
            cleaned_chunks.append(chunk)
    
    logger.info(f"文本分块完成: {len(text)} 字符 -> {len(cleaned_chunks)} 个块")
    return cleaned_chunks

def _force_split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    强制按固定大小分割文本
    
    Args:
        text: 要分割的文本
        chunk_size: 块大小
        overlap: 重叠大小
        
    Returns:
        List[str]: 分割后的文本块
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # 尝试在句号、问号、感叹号处断开
        if end < len(text):
            # 寻找最近的句子结束符
            sentence_end = -1
            for i in range(len(chunk) - 1, max(0, len(chunk) - 100), -1):
                if chunk[i] in '.!?。！？':
                    sentence_end = i + 1
                    break
            
            if sentence_end > 0:
                chunk = chunk[:sentence_end]
                end = start + sentence_end
        
        chunks.append(chunk.strip())
        
        # 计算下一个开始位置（考虑重叠）
        start = max(start + 1, end - overlap)
        
        if start >= len(text):
            break
    
    return chunks

def prepare_chunks_for_embedding(
    chunks: List[str], 
    literature_id: str, 
    group_id: str,
    literature_title: str = ""
) -> List[Dict]:
    """
    为文本块准备元数据，用于向量化存储
    
    Args:
        chunks: 文本块列表
        literature_id: 文献ID
        group_id: 研究组ID
        literature_title: 文献标题
        
    Returns:
        List[Dict]: 包含元数据的文本块列表
    """
    prepared_chunks = []
    
    for i, chunk in enumerate(chunks):
        chunk_data = {
            "text": chunk,
            "chunk_index": i,
            "literature_id": literature_id,
            "group_id": group_id,
            "literature_title": literature_title,
            "chunk_length": len(chunk),
            "chunk_id": f"{literature_id}_chunk_{i}"
        }
        prepared_chunks.append(chunk_data)
    
    logger.info(f"为文献 {literature_id} 准备了 {len(prepared_chunks)} 个文本块")
    return prepared_chunks

def estimate_token_count(text: str, model_type: str = "openai") -> int:
    """
    估算文本的token数量
    
    Args:
        text: 文本内容
        model_type: 模型类型 ("openai", "google")
        
    Returns:
        int: 估算的token数量
    """
    if not text:
        return 0
    
    try:
        if model_type == "openai":
            # 尝试使用tiktoken进行精确计算
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")  # GPT-3.5/4使用的编码
            return len(encoding.encode(text))
        else:
            # 简单估算：英文按4字符/token，中文按1.5字符/token
            english_chars = len(re.findall(r'[a-zA-Z0-9\s]', text))
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            other_chars = len(text) - english_chars - chinese_chars
            
            estimated_tokens = (english_chars // 4) + (chinese_chars // 1.5) + (other_chars // 3)
            return int(estimated_tokens)
            
    except ImportError:
        # 如果tiktoken不可用，使用简单估算
        return len(text) // 4

def clean_text_for_processing(text: str) -> str:
    """
    清理文本以便进行AI处理
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除过多的空白行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    # 移除行首行尾空白
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # 移除特殊字符和控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # 标准化引号
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text.strip()

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    从文本中提取关键词（简单实现）
    
    Args:
        text: 文本内容
        max_keywords: 最大关键词数量
        
    Returns:
        List[str]: 关键词列表
    """
    if not text:
        return []
    
    # 移除标点符号，转换为小写
    clean_text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
    
    # 分词
    words = clean_text.split()
    
    # 过滤停用词（简单版本）
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
    }
    
    # 统计词频
    word_freq = {}
    for word in words:
        if len(word) > 2 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 按频率排序，返回前N个
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in keywords[:max_keywords]]

def validate_chunk_quality(chunk: str) -> Dict[str, any]:
    """
    验证文本块的质量
    
    Args:
        chunk: 文本块
        
    Returns:
        Dict: 质量评估结果，包含score, is_valid, issues等字段
    """
    if not chunk:
        return {
            "score": 0.0,
            "is_valid": False,
            "issues": ["空文本块"],
            "length": 0,
            "word_count": 0
        }
    
    chunk = chunk.strip()
    issues = []
    score = 1.0  # 基础分数
    
    # 检查长度
    if len(chunk) < 50:
        issues.append("文本块太短")
        score -= 0.3
    
    if len(chunk) > settings.CHUNK_SIZE * 2:
        issues.append("文本块太长")
        score -= 0.2
    
    # 检查内容质量
    words = chunk.split()
    if len(words) < 10:
        issues.append("词数太少")
        score -= 0.2
    
    # 检查是否主要是重复字符
    unique_chars = len(set(chunk.lower()))
    if unique_chars < 10:
        issues.append("内容重复度过高")
        score -= 0.3
    
    # 检查是否包含有意义的内容
    meaningful_chars = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', chunk))
    meaningful_ratio = meaningful_chars / len(chunk) if len(chunk) > 0 else 0
    if meaningful_ratio < 0.5:
        issues.append("有意义字符比例过低")
        score -= 0.2
    
    # 检查是否主要是数字
    digit_ratio = len(re.findall(r'\d', chunk)) / len(chunk) if len(chunk) > 0 else 0
    if digit_ratio > 0.8:
        issues.append("主要由数字组成")
        score -= 0.3
    
    # 确保分数在0-1范围内
    score = max(0.0, min(1.0, score))
    
    return {
        "score": score,
        "is_valid": score >= 0.6 and len(issues) == 0,
        "issues": issues,
        "length": len(chunk),
        "word_count": len(words),
        "unique_chars": unique_chars,
        "meaningful_ratio": meaningful_ratio
    }

def merge_overlapping_chunks(chunks: List[str], similarity_threshold: float = 0.8) -> List[str]:
    """
    合并高度相似的重叠文本块
    
    Args:
        chunks: 文本块列表
        similarity_threshold: 相似度阈值
        
    Returns:
        List[str]: 合并后的文本块列表
    """
    if len(chunks) <= 1:
        return chunks
    
    merged_chunks = []
    skip_indices = set()
    
    for i, chunk1 in enumerate(chunks):
        if i in skip_indices:
            continue
        
        current_chunk = chunk1
        
        # 检查与后续chunks的相似度
        for j in range(i + 1, len(chunks)):
            if j in skip_indices:
                continue
            
            chunk2 = chunks[j]
            similarity = _calculate_text_similarity(current_chunk, chunk2)
            
            if similarity > similarity_threshold:
                # 合并chunks
                current_chunk = _merge_two_chunks(current_chunk, chunk2)
                skip_indices.add(j)
        
        merged_chunks.append(current_chunk)
    
    logger.info(f"文本块合并: {len(chunks)} -> {len(merged_chunks)}")
    return merged_chunks

def _calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单实现）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        float: 相似度 (0-1)
    """
    # 简单的基于共同词汇的相似度计算
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def _merge_two_chunks(chunk1: str, chunk2: str) -> str:
    """
    合并两个文本块
    
    Args:
        chunk1: 文本块1
        chunk2: 文本块2
        
    Returns:
        str: 合并后的文本块
    """
    # 简单合并：如果有重叠部分，去除重复
    words1 = chunk1.split()
    words2 = chunk2.split()
    
    # 寻找重叠部分
    max_overlap = min(len(words1), len(words2)) // 2
    overlap_len = 0
    
    for i in range(1, max_overlap + 1):
        if words1[-i:] == words2[:i]:
            overlap_len = i
    
    if overlap_len > 0:
        # 有重叠，合并时去除重复
        merged_words = words1 + words2[overlap_len:]
    else:
        # 无重叠，直接连接
        merged_words = words1 + words2
    
    return ' '.join(merged_words)
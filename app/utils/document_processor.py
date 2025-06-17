import re
import unicodedata
from typing import List, Dict, Tuple

class DocumentProcessor:
    def __init__(self):
        # 学术论文章节标识符
        self.section_patterns = {
            'abstract': [
                r'(?i)\babstract\b',
                r'(?i)\b摘\s*要\b',
                r'(?i)\bsummary\b'
            ],
            'introduction': [
                r'(?i)\bintroduction\b',
                r'(?i)\b引\s*言\b',
                r'(?i)\b前\s*言\b',
                r'(?i)\b背\s*景\b'
            ],
            'method': [
                r'(?i)\bmethods?\b',
                r'(?i)\bmethodology\b',
                r'(?i)\b方\s*法\b',
                r'(?i)\b实\s*验\s*方\s*法\b'
            ],
            'results': [
                r'(?i)\bresults?\b',
                r'(?i)\bfindings?\b',
                r'(?i)\b结\s*果\b',
                r'(?i)\b实\s*验\s*结\s*果\b'
            ],
            'discussion': [
                r'(?i)\bdiscussion\b',
                r'(?i)\b讨\s*论\b',
                r'(?i)\b分\s*析\b'
            ],
            'conclusion': [
                r'(?i)\bconclusions?\b',
                r'(?i)\b结\s*论\b',
                r'(?i)\b总\s*结\b'
            ]
        }
    
    def _clean_garbage_text(self, text: str) -> str:
        """
        清理文档中的乱码和无用字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除常见的乱码模式
        garbage_patterns = [
            r'\[fOMN-_Ã\[fOMºe\(ÏvÑmK\^sSð\s*\d+\s*\d+',  # 特定乱码模式
            r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+',  # 非ASCII、非中文、非日文字符
            r'(\d+)\s*\1\s*\1',  # 重复数字
            r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef.,，。、；：""''（）()[\]【】<>《》-]+',  # 保留基本字符
        ]
        
        cleaned_text = text
        for pattern in garbage_patterns:
            cleaned_text = re.sub(pattern, ' ', cleaned_text)
        
        # 标准化Unicode字符
        cleaned_text = unicodedata.normalize('NFKC', cleaned_text)
        
        # 移除多余空白
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        # 如果清理后文本太短或主要是数字，返回空字符串
        if len(cleaned_text) < 10 or re.match(r'^\d+\s*$', cleaned_text):
            return ""
            
        return cleaned_text

    def _identify_section_type(self, text: str) -> str:
        """
        识别文本块所属的论文章节类型
        
        Args:
            text: 文本内容
            
        Returns:
            str: 章节类型
        """
        text_lower = text.lower()
        
        # 检查各种章节模式
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return section_type
        
        # 根据内容特征推断章节类型
        if self._is_likely_abstract(text):
            return 'abstract'
        elif self._is_likely_conclusion(text):
            return 'conclusion'
        elif self._is_likely_method(text):
            return 'method'
        elif self._is_likely_results(text):
            return 'results'
        
        return 'content'  # 默认为一般内容
    
    def _is_likely_abstract(self, text: str) -> bool:
        """判断是否可能是摘要"""
        abstract_keywords = [
            'study', 'research', 'investigate', 'analyze', 'examine',
            'findings', 'results', 'conclusion', 'purpose', 'objective',
            '研究', '分析', '调查', '实验', '发现', '结果', '结论', '目的'
        ]
        
        keyword_count = sum(1 for keyword in abstract_keywords if keyword.lower() in text.lower())
        return keyword_count >= 3 and len(text) < 1500  # 摘要通常较短且包含多个关键词
    
    def _is_likely_conclusion(self, text: str) -> bool:
        """判断是否可能是结论"""
        conclusion_keywords = [
            'conclude', 'demonstrated', 'showed', 'found', 'suggest',
            'implication', 'significance', 'contribution', 'future work',
            '结论', '证明', '显示', '发现', '建议', '意义', '贡献', '未来工作'
        ]
        
        keyword_count = sum(1 for keyword in conclusion_keywords if keyword.lower() in text.lower())
        return keyword_count >= 2
    
    def _is_likely_method(self, text: str) -> bool:
        """判断是否可能是方法"""
        method_keywords = [
            'procedure', 'algorithm', 'technique', 'approach', 'implementation',
            'experimental', 'measurement', 'analysis', 'protocol',
            '方法', '算法', '技术', '实验', '测量', '分析', '协议', '流程'
        ]
        
        keyword_count = sum(1 for keyword in method_keywords if keyword.lower() in text.lower())
        return keyword_count >= 2
    
    def _is_likely_results(self, text: str) -> bool:
        """判断是否可能是结果"""
        results_keywords = [
            'table', 'figure', 'graph', 'chart', 'data', 'statistics',
            'significant', 'correlation', 'comparison', 'performance',
            '表', '图', '数据', '统计', '显著', '相关', '比较', '性能'
        ]
        
        keyword_count = sum(1 for keyword in results_keywords if keyword.lower() in text.lower())
        return keyword_count >= 2

    def _extract_structured_chunks(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[Dict]:
        """
        提取结构化文本块
        
        Args:
            text: 原始文本
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            List[Dict]: 包含文本和元数据的块列表
        """
        # 首先清理整个文本
        text = self._clean_garbage_text(text)
        
        if not text:
            return []
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # 尝试在句子边界处分割
            if end < len(text):
                # 向后查找句子结束符
                for i in range(end, min(end + 200, len(text))):
                    if text[i] in '.。!！?？':
                        end = i + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            # 清理单个chunk
            chunk_text = self._clean_garbage_text(chunk_text)
            
            # 只保留有意义的chunk
            if len(chunk_text) > 30 and not re.match(r'^\s*[.\s]*$', chunk_text):
                # 识别章节类型
                section_type = self._identify_section_type(chunk_text)
                
                # 计算内容质量分数
                quality_score = self._calculate_content_quality(chunk_text, section_type)
                
                chunk_data = {
                    'text': chunk_text,
                    'section_type': section_type,
                    'quality_score': quality_score,
                    'chunk_index': chunk_index,
                    'start_pos': start,
                    'end_pos': end,
                    'length': len(chunk_text)
                }
                
                chunks.append(chunk_data)
                chunk_index += 1
            
            # 更新起始位置
            start += chunk_size - overlap
            
            # 避免无限循环
            if start >= end:
                start = end
        
        # 按质量分数和章节重要性重新排序
        chunks = self._prioritize_chunks(chunks)
        
        return chunks
    
    def _calculate_content_quality(self, text: str, section_type: str) -> float:
        """
        计算内容质量分数
        
        Args:
            text: 文本内容
            section_type: 章节类型
            
        Returns:
            float: 质量分数 (0-1)
        """
        score = 0.0
        
        # 基于章节类型的权重
        section_weights = {
            'abstract': 1.0,
            'introduction': 0.9,
            'conclusion': 1.0,
            'discussion': 0.8,
            'method': 0.6,
            'results': 0.7,
            'content': 0.5
        }
        
        score += section_weights.get(section_type, 0.5)
        
        # 基于关键词的评分
        academic_keywords = [
            # 英文学术关键词
            'research', 'study', 'analysis', 'investigation', 'experiment',
            'theory', 'hypothesis', 'methodology', 'findings', 'conclusion',
            'significance', 'contribution', 'innovation', 'novel', 'approach',
            'framework', 'model', 'algorithm', 'technique', 'evaluation',
            'comparison', 'performance', 'effectiveness', 'improvement',
            
            # 中文学术关键词
            '研究', '分析', '调查', '实验', '理论', '假设', '方法', '发现',
            '结论', '意义', '贡献', '创新', '新颖', '方法', '框架', '模型',
            '算法', '技术', '评估', '比较', '性能', '效果', '改进'
        ]
        
        keyword_count = sum(1 for keyword in academic_keywords if keyword.lower() in text.lower())
        score += min(keyword_count * 0.1, 0.5)  # 最多加0.5分
        
        # 基于文本长度的评分 (适中长度最好)
        text_length = len(text)
        if 100 <= text_length <= 1000:
            score += 0.2
        elif text_length < 50:
            score -= 0.3
        
        # 检查是否包含完整句子
        sentence_count = len([s for s in text.split('.') if len(s.strip()) > 10])
        if sentence_count >= 2:
            score += 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def _prioritize_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        根据质量和重要性对块进行优先级排序
        
        Args:
            chunks: 原始块列表
            
        Returns:
            List[Dict]: 排序后的块列表
        """
        # 定义章节重要性权重
        section_priority = {
            'abstract': 10,
            'conclusion': 9,
            'introduction': 8,
            'discussion': 7,
            'results': 6,
            'method': 5,
            'content': 4
        }
        
        # 为每个块计算综合评分
        for chunk in chunks:
            section_type = chunk['section_type']
            quality_score = chunk['quality_score']
            priority_weight = section_priority.get(section_type, 4)
            
            # 综合评分 = 质量分数 * 章节重要性权重
            chunk['final_priority'] = quality_score * priority_weight
        
        # 按综合评分排序
        chunks.sort(key=lambda x: x['final_priority'], reverse=True)
        
        return chunks

    def _extract_text_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        向后兼容的简单分块方法
        """
        structured_chunks = self._extract_structured_chunks(text, chunk_size, overlap)
        return [chunk['text'] for chunk in structured_chunks] 
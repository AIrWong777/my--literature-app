"""
RAG问答系统答案处理器

负责处理AI生成的答案，提取引用来源，计算置信度，格式化输出
"""
from typing import Dict, List, Optional, Any, Tuple
import re
import json
from datetime import datetime
from app.config import Config

class AnswerProcessor:
    """答案处理器类"""
    
    def __init__(self):
        """初始化答案处理器"""
        self.min_confidence = Config.RAG_MIN_CONFIDENCE
        self.max_answer_length = Config.RAG_MAX_ANSWER_LENGTH
        self.min_answer_length = Config.RAG_MIN_ANSWER_LENGTH
        
        # 置信度关键词映射
        self.confidence_keywords = {
            "高": 0.8,
            "中": 0.6,
            "低": 0.4,
            "very high": 0.9,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
            "very low": 0.3
        }

    def process_answer(
        self, 
        raw_answer: str, 
        context_chunks: List[Dict],
        question: str,
        literature_id: str
    ) -> Dict[str, Any]:
        """
        处理AI原始答案
        
        Args:
            raw_answer: AI生成的原始答案
            context_chunks: 相关文档块
            question: 用户问题
            literature_id: 文献ID
            
        Returns:
            Dict: 处理后的答案数据
        """
        try:
            # 解析答案结构
            parsed_answer = self._parse_answer_structure(raw_answer)
            
            # 提取引用来源
            sources = self._extract_sources(parsed_answer, context_chunks)
            
            # 计算置信度
            confidence = self._calculate_confidence(parsed_answer, sources, context_chunks)
            
            # 格式化答案
            formatted_answer = self._format_answer(parsed_answer["main_answer"])
            
            # 质量检验
            quality_score = self._assess_answer_quality(formatted_answer, sources, question)
            
            # 构建结果
            result = {
                "answer": formatted_answer,
                "key_findings": parsed_answer["key_findings"],
                "limitations": parsed_answer["limitations"],
                "sources": sources,
                "confidence": confidence,
                "quality_score": quality_score,
                "metadata": {
                    "literature_id": literature_id,
                    "question": question,
                    "timestamp": datetime.now().isoformat(),
                    "chunks_used": len(context_chunks),
                    "raw_answer": raw_answer
                }
            }
            
            # 验证结果
            if self._validate_answer(result):
                return result
            else:
                # return self._create_fallback_answer(question, "validation_failed")
                return result
        except Exception as e:
            print(f"答案处理出错: {str(e)}")
            return self._create_fallback_answer(question, "processing_error")

    def _clean_ai_response(self, response: str) -> str:
        """
        清理AI回答文本
        
        Args:
            response: 原始AI回答
            
        Returns:
            str: 清理后的文本
        """
        if not response:
            return ""

        text = response

        # 1. Normalize newlines (to \n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 2. Strip leading/trailing whitespace from the whole response
        text = text.strip()
        
        # 3. Reduce multiple spaces/tabs to single spaces, but preserve newlines.
        # This will not affect newlines, only horizontal spacing.
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 4. Collapse 3 or more newlines into exactly two (for paragraph separation)
        # and leave single newlines as they are.
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 5. Remove preamble like "Okay, here's the answer based on the context:"
        #    The previous regex for this might have been too aggressive.
        #    A more targeted removal might be needed if specific preambles are common.
        #    For now, let's assume the AI starts relatively clean or the prompt guides it.
        #    Example of a more specific preamble removal if needed later:
        #    known_preambles = [
        #        "好的，这是基于您提供文献的分析结果：\n", 
        #        "Okay, here is the information based on the document provided:\n"
        #    ]
        #    for preamble in known_preambles:
        #        if text.startswith(preamble):
        #            text = text[len(preamble):]
        #            break
            
        return text

    def _parse_answer_structure(self, answer_text: str) -> Dict[str, Any]:
        """
        解析AI回答的结构化内容 - 智能按顺序分割回答
        
        Args:
            answer_text: AI回答文本
            
        Returns:
            Dict: 解析后的结构化内容
        """
        parsed = {
            "main_answer": "",
            "key_findings": [],
            "limitations": "",
            "sources": [],
            "confidence": "中"
        }
        cleaned_answer = self._clean_ai_response(answer_text)

        kf_keyword = "关键发现："
        lim_keyword = "局限性说明："

        # Start with the full cleaned answer as the potential main_answer
        current_main_text = cleaned_answer
        key_findings_section_text = ""
        limitations_section_text = ""

        # Step 1: Try to find and extract Limitations section
        # Search from the end or assume it's after key findings if both exist
        lim_start_index = current_main_text.rfind(lim_keyword) # Use rfind to get the last occurrence

        if lim_start_index != -1:
            # Check if "关键发现:" appears before this "局限性说明:"
            # to avoid incorrectly splitting if "局限性说明:" is mentioned within key findings.
            kf_check_index = current_main_text.rfind(kf_keyword, 0, lim_start_index)
            
            # Only treat as actual limitations section if it's the last major section
            # or if there's no KF section, or KF is clearly before it.
            # This logic assumes KF, if present, comes before the final LIMITATIONS.
            
            # A simpler approach: if "局限性说明：" is found, assume text after it is limitations.
            # And text before it is a candidate for main_answer + key_findings.
            limitations_section_text = current_main_text[lim_start_index + len(lim_keyword):].strip()
            current_main_text = current_main_text[:lim_start_index].strip()

        # Step 2: Try to find and extract Key Findings section from the (potentially shortened) current_main_text
        kf_start_index = current_main_text.rfind(kf_keyword) # Use rfind for the last "关键发现:"
        
        if kf_start_index != -1:
            key_findings_section_text = current_main_text[kf_start_index + len(kf_keyword):].strip()
            current_main_text = current_main_text[:kf_start_index].strip() # This becomes the final main_answer

        parsed["main_answer"] = current_main_text.strip()
        parsed["limitations"] = limitations_section_text.strip()

        if key_findings_section_text:
            # Regex to find items like "1. ...", "2. ...", etc.
            # It captures text after "number." up to the next "number." or end of string.
            findings_matches = re.findall(r'\d+\.\s*(.*?)(?=\s*\d+\.\s*|$)', key_findings_section_text, re.DOTALL)
            if findings_matches:
                parsed["key_findings"] = [f.strip(" 。.") for f in findings_matches if f.strip(" 。.")]
            else:
                # Fallback if no "1. item" structure is found, split by sentences or newlines.
                # This is for cases where findings are not numbered but are distinct points.
                potential_findings = re.split(r'[。\n]', key_findings_section_text)
                parsed["key_findings"] = [
                    f.strip() for f in potential_findings if f.strip() and len(f.strip()) > 5 # Avoid very short fragments
                ][:5] # Limit to a max of 5 findings in fallback

        # Extract sources from the original full cleaned_answer to ensure all references are caught
        source_numbers = re.findall(r'【来源(\d+)】', cleaned_answer)
        parsed["sources"] = list(set(source_numbers))
        
        # Evaluate confidence based on sources
        if len(parsed["sources"]) >= 3:
            parsed["confidence"] = "高"
        elif len(parsed["sources"]) >= 1:
            parsed["confidence"] = "中"
        else:
            parsed["confidence"] = "低"
            
        return parsed

    def _extract_sources(self, parsed_answer: Dict[str, Any], context_chunks: List[Dict]) -> List[Dict]:
        """
        提取引用来源
        
        Args:
            parsed_answer: 解析后的答案
            context_chunks: 文档块列表
            
        Returns:
            List[Dict]: 引用来源列表
        """
        sources = []
        
        # 从答案文本中查找引用标记
        answer_text = parsed_answer["main_answer"]
        key_findings_text = " ".join(parsed_answer["key_findings"]) if parsed_answer["key_findings"] else ""
        limitations_text = parsed_answer["limitations"]
        
        # 合并所有文本来查找引用
        all_text = f"{answer_text} {key_findings_text} {limitations_text}"
        
        # 查找【来源X】标记
        source_refs = re.findall(r'【来源(\d+)】', all_text)
        
        for ref_num in source_refs:
            try:
                source_index = int(ref_num) - 1  # 转换为0基索引
                if 0 <= source_index < len(context_chunks):
                    chunk = context_chunks[source_index]
                    
                    source_info = {
                        "source_id": ref_num,
                        "chunk_index": chunk.get("chunk_index", source_index),
                        "text": chunk.get("text", "").strip()[:500],  # 限制长度
                        "similarity": chunk.get("similarity", 0),
                        "description": f"来源{ref_num}的相关内容",
                        "page_number": chunk.get("page_number"),
                        "section": chunk.get("section")
                    }
                    sources.append(source_info)
            except (ValueError, IndexError):
                continue
        
        # 如果没有找到明确的引用，使用相似度最高的块
        if not sources and context_chunks:
            for i, chunk in enumerate(context_chunks[:3]):  # 最多3个来源
                source_info = {
                    "source_id": str(i + 1),
                    "chunk_index": chunk.get("chunk_index", i),
                    "text": chunk.get("text", "").strip()[:500],
                    "similarity": chunk.get("similarity", 0),
                    "description": f"相关度最高的文档块{i + 1}",
                    "page_number": chunk.get("page_number"),
                    "section": chunk.get("section")
                }
                sources.append(source_info)
        
        return sources

    def _calculate_confidence(
        self, 
        parsed_answer: Dict[str, Any], 
        sources: List[Dict],
        context_chunks: List[Dict]
    ) -> float:
        """
        计算答案置信度
        
        Args:
            parsed_answer: 解析后的答案
            sources: 引用来源
            context_chunks: 文档块
            
        Returns:
            float: 置信度分数 (0-1)
        """
        confidence_score = 0.5  # 基础分数
        
        # 1. 从AI明确给出的置信度提取
        ai_confidence = self._extract_ai_confidence(parsed_answer["confidence"])
        if ai_confidence:
            confidence_score = ai_confidence
        
        # 2. 基于引用来源质量调整
        if sources:
            avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
            source_factor = min(avg_similarity * 1.2, 1.0)  # 相似度加权
            confidence_score = (confidence_score + source_factor) / 2
        
        # 3. 基于答案长度和结构调整
        answer_text = parsed_answer["main_answer"]
        if answer_text:
            # 长度适中的答案更可信
            length_factor = self._calculate_length_factor(len(answer_text))
            confidence_score *= length_factor
            
            # 结构化的答案更可信
            if self._has_good_structure(answer_text):
                confidence_score *= 1.1
        
        # 4. 基于文档块数量调整
        if len(context_chunks) >= 3:
            confidence_score *= 1.05  # 多个来源支持
        elif len(context_chunks) == 0:
            confidence_score *= 0.3  # 没有相关内容
        
        # 确保在有效范围内
        return max(0.1, min(1.0, confidence_score))

    def _extract_ai_confidence(self, confidence_text: str) -> Optional[float]:
        """
        从AI回答中提取置信度
        
        Args:
            confidence_text: 置信度文本
            
        Returns:
            Optional[float]: 置信度数值
        """
        if not confidence_text:
            return None
        
        # 查找关键词
        for keyword, score in self.confidence_keywords.items():
            if keyword in confidence_text.lower():
                return score
        
        # 查找数字
        number_match = re.search(r'(\d+(?:\.\d+)?)', confidence_text)
        if number_match:
            try:
                value = float(number_match.group(1))
                if value <= 1.0:
                    return value
                elif value <= 100:
                    return value / 100
            except ValueError:
                pass
        
        return None

    def _calculate_length_factor(self, length: int) -> float:
        """
        基于答案长度计算调整因子
        
        Args:
            length: 答案长度
            
        Returns:
            float: 长度调整因子
        """
        if length < self.min_answer_length:
            return 0.7  # 太短
        elif length > self.max_answer_length:
            return 0.8  # 太长
        elif 100 <= length <= 800:
            return 1.1  # 适中长度
        else:
            return 1.0  # 正常长度

    def _has_good_structure(self, text: str) -> bool:
        """
        检查答案是否有良好的结构
        
        Args:
            text: 答案文本
            
        Returns:
            bool: 是否有良好结构
        """
        structure_indicators = [
            r'\d+[.、]',  # 数字列表
            r'[一二三四五六七八九十][、.]',  # 中文数字列表
            r'[（(]\d+[）)]',  # 带括号的数字
            r'首先|其次|然后|最后|另外',  # 连接词
            r'第一|第二|第三',  # 序数词
            r'总结|综上|因此|所以'  # 结论词
        ]
        
        return sum(1 for pattern in structure_indicators if re.search(pattern, text)) >= 2

    def _format_answer(self, answer_text: str) -> str:
        """
        格式化答案文本 - 只返回主要回答部分
        
        Args:
            answer_text: 主要回答文本（已经在_parse_answer_structure中分离）
            
        Returns:
            str: 格式化后的主要回答
        """
        if not answer_text:
            return "抱歉，无法生成答案。"
        
        # 清理文本
        formatted = re.sub(r'\s+', ' ', answer_text)  # 标准化空白字符
        formatted = re.sub(r'\n\s*\n', '\n\n', formatted)  # 规范化段落间距
        
        # 去掉开头的"答案："前缀
        formatted = re.sub(r'^答案：\s*', '', formatted, flags=re.IGNORECASE)
        formatted = re.sub(r'^\*\*答案：?\*\*\s*', '', formatted, flags=re.IGNORECASE)
        
        # 移除markdown格式符号
        formatted = re.sub(r'\*\*([^*]+)\*\*', r'\1', formatted)  # 移除粗体
        formatted = re.sub(r'\*([^*]+)\*', r'\1', formatted)  # 移除斜体
        formatted = re.sub(r'^#+\s*', '', formatted, flags=re.MULTILINE)  # 移除标题符号
        
        # 移除任何残留的关键发现和局限性说明标记
        formatted = re.sub(r'\n\s*关键发现：?.*?$', '', formatted, flags=re.DOTALL | re.IGNORECASE)
        formatted = re.sub(r'\n\s*局限性说明：?.*?$', '', formatted, flags=re.DOTALL | re.IGNORECASE)
        formatted = re.sub(r'^关键发现：?.*?$', '', formatted, flags=re.MULTILINE | re.IGNORECASE)
        formatted = re.sub(r'^局限性说明：?.*?$', '', formatted, flags=re.MULTILINE | re.IGNORECASE)
        
        # 移除引用标记（这些会在sources中单独处理）
        formatted = re.sub(r'【来源\d+】', '', formatted)
        
        # 清理多余的空行
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = formatted.strip()
        
        # 如果清理后内容为空，返回默认消息
        if not formatted or len(formatted.strip()) < 10:
            return "抱歉，无法生成有效的回答内容。"
        
        return formatted

    def _assess_answer_quality(self, answer: str, sources: List[Dict], question: str) -> Dict[str, float]:
        """
        评估答案质量
        
        Args:
            answer: 格式化后的答案
            sources: 引用来源
            question: 用户问题
            
        Returns:
            Dict[str, float]: 质量评分
        """
        quality_scores = {
            "relevance": 0.7,  # 相关性
            "completeness": 0.6,  # 完整性
            "accuracy": 0.8,  # 准确性
            "clarity": 0.7,  # 清晰度
            "citation": 0.5   # 引用质量
        }
        
        # 相关性评估
        question_keywords = self._extract_keywords(question)
        answer_keywords = self._extract_keywords(answer)
        keyword_overlap = len(set(question_keywords) & set(answer_keywords))
        if keyword_overlap > 0:
            quality_scores["relevance"] = min(1.0, 0.5 + keyword_overlap * 0.1)
        
        # 完整性评估
        if len(answer) >= 200:
            quality_scores["completeness"] = 0.8
        elif len(answer) >= 100:
            quality_scores["completeness"] = 0.7
        
        # 引用质量评估
        if sources:
            avg_similarity = sum(s.get("similarity", 0) for s in sources) / len(sources)
            quality_scores["citation"] = min(1.0, avg_similarity * 1.5)
        
        # 清晰度评估（基于结构和可读性）
        if self._has_good_structure(answer):
            quality_scores["clarity"] = 0.9
        
        return quality_scores

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取（移除停用词）
        stopwords = {'的', '是', '在', '有', '和', '与', '对', '为', '了', '也', '可以', '能够', '这个', '那个', '什么', '如何', '怎么'}
        
        # 提取中文词汇和英文单词
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 过滤停用词和短词
        keywords = []
        for word in chinese_words + english_words:
            if len(word) >= 2 and word not in stopwords:
                keywords.append(word)
        
        return keywords[:10]  # 返回前10个关键词

    def _validate_answer(self, result: Dict[str, Any]) -> bool:
        """
        验证答案质量
        
        Args:
            result: 答案结果
            
        Returns:
            bool: 是否通过验证
        """
        answer = result.get("answer", "")
        confidence = result.get("confidence", 0)
        
        # 基本验证
        if len(answer) < self.min_answer_length:
            return False
        
        if confidence < self.min_confidence:
            return False
        
        # 检查是否包含错误内容
        error_indicators = ["抱歉", "无法", "不知道", "不清楚", "错误"]
        if any(indicator in answer[:50] for indicator in error_indicators):
            return False
        
        return True

    def _create_fallback_answer(self, question: str, error_type: str) -> Dict[str, Any]:
        """
        创建降级答案
        
        Args:
            question: 用户问题
            error_type: 错误类型
            
        Returns:
            Dict: 降级答案
        """
        fallback_messages = {
            "no_content": "抱歉，我在文献中没有找到与您的问题相关的内容。请尝试重新表述问题或查看预设问题。",
            "validation_failed": "抱歉，生成的答案质量不够理想。请重新提问或尝试更具体的问题。",
            "processing_error": "处理您的问题时出现了技术问题。请稍后重试。"
        }
        
        return {
            "answer": fallback_messages.get(error_type, "抱歉，无法处理您的问题。"),
            "key_findings": [],
            "limitations": "由于处理过程中出现问题，无法提供详细的分析。",
            "sources": [],
            "confidence": 0.1,
            "quality_score": {"relevance": 0.1, "completeness": 0.1, "accuracy": 0.1, "clarity": 0.1, "citation": 0.1},
            "metadata": {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "is_fallback": True
            }
        }

    def format_response_for_api(self, processed_answer: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化答案用于API响应
        
        Args:
            processed_answer: 处理后的答案
            
        Returns:
            Dict: API格式的响应
        """
        return {
            "answer": processed_answer["answer"],
            "sources": [
                {
                    "id": source["source_id"],
                    "text": source["text"][:300],  # 限制返回长度
                    "similarity": source["similarity"],
                    "description": source["description"],
                    "chunk_index": source["chunk_index"]
                }
                for source in processed_answer["sources"]
            ],
            "confidence": round(processed_answer["confidence"], 2),
            "metadata": {
                "timestamp": processed_answer["metadata"]["timestamp"],
                "quality": round(
                    sum(processed_answer["quality_score"].values()) / len(processed_answer["quality_score"]), 
                    2
                )
            }
        } 
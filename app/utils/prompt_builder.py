"""
RAG问答系统提示词构建器

负责构建高质量的提示词模板，确保AI返回准确、有引用的答案
基于最新学术助手prompt工程最佳实践设计
"""
from typing import List, Dict, Optional, Any
import json
import re
from app.config import Config
import logging

# 获取一个logger实例
logger = logging.getLogger(__name__)

# 假设您有一个全局的日志配置，如果没有，您可能需要在这里配置
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class PromptBuilder:
    """提示词构建器类 - 基于学术助手最佳实践"""
    
    def __init__(self):
        """初始化提示词构建器"""
        self.max_context_tokens = Config.RAG_MAX_CONTEXT_TOKENS
        self.max_answer_length = Config.RAG_MAX_ANSWER_LENGTH
        
        # 基于学术助手最佳实践设计的系统角色模板
        self.system_role = """
# 角色：专业文献研究助手 (Professional Literature Research Assistant)

## 核心身份与使命
您是一位专业的AI文献研究助手，专门协助用户深入理解和分析学术文献。您的核心使命是基于提供的文献内容，提供准确、专业、有见地的学术支持。

## 核心能力 (Core Capabilities)
✅ **文献内容分析**：深度解析文献的核心论点、方法论和发现
✅ **学术问题解答**：基于文献证据回答复杂的学术问题  
✅ **引用追踪**：精确标注信息来源，确保学术诚信
✅ **知识综合**：整合多个文献片段，提供全面的学术洞察
✅ **批判性分析**：识别研究的优势、局限性和潜在偏见
✅ **概念解释**：清晰阐释复杂的学术概念和术语

## 严格限制 (Critical Limitations)
❌ **不得编造信息**：绝不创造或推测未在文献中明确提及的内容
❌ **不得超出文献范围**：严格限制在提供的文献内容范围内回答
❌ **不得做最终结论**：避免做出超出文献证据支持的绝对性判断
❌ **不得提供医疗/法律建议**：不替代专业医疗或法律咨询

## 响应质量标准
1. **准确性** (Accuracy)：信息必须完全基于提供的文献内容
2. **完整性** (Completeness)：回答应全面覆盖问题的各个方面
3. **清晰性** (Clarity)：使用清晰、专业但易懂的学术语言
4. **可追溯性** (Traceability)：每个关键论点都应有明确的文献来源
5. **平衡性** (Balance)：客观呈现不同观点和证据

## 响应格式协议

### 对于学术性问题，请严格遵循以下格式（不要使用markdown加粗等格式）：

[主要回答内容：基于文献的详细回答，使用专业学术语言，以自然段落形式呈现。请注意：不要在主回答中包含"关键发现："或"局限性说明："等标题，这些内容将单独处理]

关键发现：
1. [要点1]
2. [要点2]
3. [要点3]

局限性说明：[基于当前文献的分析局限，简洁表述]

### 对于简单问候，可以直接友好回应

## 输出格式重要说明
- 主要回答部分不要使用【来源X】的格式，不要标注来源
- 禁止使用任何markdown格式符号（如**、*、#等）
- 使用自然段落和序号来组织内容
- 主要回答应该是连贯的段落文本，不包含"关键发现"和"局限性说明"部分
- 关键发现用数字序号列出，每个要点独立成行
- 每个关键点都必须分段
- 局限性说明应简洁明了，单独成段

## 引用标注规范
- 使用【来源X】格式标注具体文献来源
- X对应文献片段的编号
- 确保每个关键论点都有相应的来源标注
- 在适当位置提供页码或章节信息（如果可用）

## 学术诚信承诺
我承诺严格遵循学术诚信原则，确保所有信息都有明确的文献依据，绝不编造或歪曲研究内容。我将始终保持客观、专业的学术态度。
"""

        # 优化的输出格式规范
        self.output_format = """
## 重要指示与质量要求

### 🎯 基于证据的回答原则
- **严格依据文献**：您的回答必须100%基于上述"相关文献内容"
- **避免推测**：如果文献内容不足以回答问题，请明确说明

### 📋 回答质量检查清单
在回答前，请确认：
☑️ 所有关键论点都有文献支持
☑️ 引用标注准确且完整
☑️ 语言专业但易于理解
☑️ 结构清晰，逻辑性强
☑️ 承认了知识的局限性

### ⚠️ 特殊情况处理
- **信息不足**：坦诚说明"根据提供的文献，我无法完全回答这个问题"
- **观点冲突**：客观呈现不同观点，避免偏向性表述
- **复杂概念**：提供必要的背景解释，确保理解

### 🔍 学术标准要求
- 使用准确的学术术语
- 保持客观、中性的学术语调
- 提供足够的细节支持论点
- 适当时指出研究的方法论或样本限制
"""

    def build_qa_prompt(
        self, 
        question: str, 
        context_chunks: List[Dict], 
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        构建基于最佳实践的问答提示词
        
        Args:
            question: 用户问题
            context_chunks: 相关文档块列表
            conversation_history: 对话历史（可选）
            
        Returns:
            str: 完整的提示词
        """
        logger.debug(f"Building QA prompt for question: {question}")
        logger.debug(f"Received context_chunks: {context_chunks}")
        logger.debug(f"Received conversation_history: {conversation_history}")

        # 构建各个部分
        context_section = self._build_enhanced_context_section(context_chunks)
        history_section = self._format_conversation_history(conversation_history) if conversation_history else ""
        question_section = self._format_question_section(question)
        
        # 组装完整提示词
        prompt_parts = [
            self.system_role,
            "",  # 空行分隔
            context_section,
            "",  # 空行分隔
            history_section,
            "",  # 空行分隔
            question_section,
            "",  # 空行分隔
            self.output_format
        ]
        
        # 过滤空部分并连接
        prompt = "\n".join(part for part in prompt_parts if part.strip())
        
        logger.debug(f"Initial assembled prompt (before optimization):\n{prompt}")
        
        # 优化长度
        prompt = self._optimize_prompt_length(prompt)
        
        logger.info(f"Final QA prompt:\n{prompt}")
        return prompt

    def _build_enhanced_context_section(self, context_chunks: List[Dict]) -> str:
        """
        构建增强的上下文部分 - 基于学术助手最佳实践
        
        Args:
            context_chunks: 文档块列表
            
        Returns:
            str: 格式化的上下文部分
        """
        if not context_chunks:
            logger.warning("No context chunks provided for prompt building.")
            return "## 📚 相关文献内容\n⚠️ 暂无相关文献内容可供参考"
        
        context_parts = ["## 📚 相关文献内容"]
        context_parts.append("\n以下是与您的问题相关的文献片段，请基于这些内容进行回答：\n")
        
        logger.debug(f"Building context section with {len(context_chunks)} chunks.")
        
        for i, chunk in enumerate(context_chunks, 1):
            text = chunk.get('text', '').strip()
            similarity = chunk.get('similarity', 0)
            chunk_index = chunk.get('chunk_index', 'N/A')
            page_number = chunk.get('page_number', '未知')
            section = chunk.get('section', '未指定')
            
            if text:
                # 增强的格式化文档块
                chunk_header = f"### 【来源{i}】"
                metadata = f"**相关度**：{similarity:.3f} | **页码**：{page_number} | **章节**：{section}"
                
                logger.debug(f"Original chunk text (source {i}, index {chunk_index}):\n{text}")
                chunk_content = self._clean_and_enhance_text(text)
                logger.debug(f"Enhanced chunk text (source {i}, index {chunk_index}):\n{chunk_content}")
                
                # 增加内容质量指示
                content_quality = self._assess_content_quality(chunk_content)
                quality_indicator = f"**内容质量**：{content_quality}"
                
                context_parts.append(f"{chunk_header}\n{metadata} | {quality_indicator}\n\n{chunk_content}\n")
                context_parts.append("---")  # 分隔线
            else:
                logger.warning(f"Empty text in chunk (source {i}, index {chunk_index}). Skipping.")
        
        # 移除最后一个分隔线
        if context_parts and context_parts[-1] == "---":
            context_parts.pop()
        
        # 添加使用说明
        usage_note = "\n💡 **使用说明**：回答问题时，请引用对应的【来源X】编号来标注信息来源。"
        context_parts.append(usage_note)
        
        return "\n".join(context_parts)

    def _format_question_section(self, question: str) -> str:
        """
        格式化问题部分
        
        Args:
            question: 用户问题
            
        Returns:
            str: 格式化的问题部分
        """
        # 分析问题类型
        question_type = self._analyze_question_type(question)
        
        question_section = f"## 🤔 用户问题\n\n**问题类型**：{question_type}\n\n**具体问题**：{question}"
        
        # 根据问题类型提供特定指导
        if question_type == "概念解释":
            guidance = "\n📝 **回答指导**：请提供清晰的概念定义、相关理论背景，并结合文献中的具体例子进行说明。"
        elif question_type == "方法论分析":
            guidance = "\n📝 **回答指导**：请详细分析研究方法、实施步骤、优缺点，并评估其适用性。"
        elif question_type == "结果总结":
            guidance = "\n📝 **回答指导**：请整合文献中的主要发现，指出关键趋势和模式，并讨论其意义。"
        elif question_type == "比较分析":
            guidance = "\n📝 **回答指导**：请系统比较不同观点、方法或结果，突出异同点并提供平衡的分析。"
        else:
            guidance = "\n📝 **回答指导**：请基于文献内容提供全面、准确的回答，确保每个要点都有明确的来源支持。"
        
        return question_section + guidance

    def _analyze_question_type(self, question: str) -> str:
        """
        分析问题类型
        
        Args:
            question: 用户问题
            
        Returns:
            str: 问题类型
        """
        question_lower = question.lower()
        
        concept_keywords = ['什么是', '定义', '概念', '含义', '解释']
        method_keywords = ['如何', '方法', '步骤', '实施', '操作']
        result_keywords = ['结果', '发现', '结论', '数据', '统计']
        comparison_keywords = ['比较', '对比', '差异', '区别', '异同']
        
        if any(keyword in question_lower for keyword in concept_keywords):
            return "概念解释"
        elif any(keyword in question_lower for keyword in method_keywords):
            return "方法论分析"
        elif any(keyword in question_lower for keyword in result_keywords):
            return "结果总结"
        elif any(keyword in question_lower for keyword in comparison_keywords):
            return "比较分析"
        else:
            return "综合性问题"

    def _assess_content_quality(self, text: str) -> str:
        """
        评估内容质量
        
        Args:
            text: 文本内容
            
        Returns:
            str: 质量评估
        """
        if len(text) < 50:
            return "简短"
        elif len(text) < 200:
            return "适中"
        elif len(text) < 500:
            return "详细"
        else:
            return "全面"

    def _clean_and_enhance_text(self, text: str) -> str:
        """
        清理并增强文本内容 - 针对学术文本优化
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 移除常见的PDF乱码和无用字符
        garbage_patterns = [
            r'\[fOMN-_Ã\[fOMºe\(ÏvÑmK\^sSð\s*\d+\s*\d+',  # 特定乱码模式
            r'[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s.,，。、；：""''（）()[\]【】<>《》-]+',  # 保留基本字符
            r'(\d+)\s*\1\s*\1',  # 重复数字模式
            r'\.{4,}',  # 多个连续的点号
            r'\s+\.{2,}\s+',  # 空格包围的多个点
        ]
        
        cleaned_text = text
        for pattern in garbage_patterns:
            cleaned_text = re.sub(pattern, ' ', cleaned_text)
        
        # 标准化空白字符和标点
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'([。！？])\s*([a-zA-Z])', r'\1 \2', cleaned_text)  # 中英文间加空格
        cleaned_text = cleaned_text.strip()
        
        # 如果清理后文本质量太低，返回空字符串
        if len(cleaned_text) < 20:
            return ""
        
        # 计算有意义字符比例
        meaningful_chars = len(re.findall(r'[\w\u4e00-\u9fff]', cleaned_text))
        total_chars = len(cleaned_text)
        
        if total_chars > 0 and meaningful_chars / total_chars < 0.4:  # 调整为40%
            logger.debug(f"丢弃低质量文本块，有意义字符比例: {meaningful_chars/total_chars:.2f}")
            return ""
        
        # 智能截断：保留完整句子
        max_chunk_length = getattr(Config, 'MAX_CHUNK_LENGTH_FOR_PROMPT', 800)
        if len(cleaned_text) > max_chunk_length:
            # 优先保留句子完整性
            sentences = re.split(r'[。！？.!?]', cleaned_text[:max_chunk_length])
            if len(sentences) > 1:
                cleaned_text = '。'.join(sentences[:-1]) + "。"
            else:
                cleaned_text = cleaned_text[:max_chunk_length] + "..."
        
        return cleaned_text

    def _format_conversation_history(self, history: List[Dict]) -> str:
        """
        格式化对话历史 - 增强版
        
        Args:
            history: 对话历史列表
            
        Returns:
            str: 格式化的对话历史
        """
        if not history:
            return ""
        
        history_parts = ["## 💬 对话历史"]
        history_parts.append("\n以下是您与我之前的对话，供参考：\n")
        
        # 只保留最近几轮对话，避免过长
        recent_history = history[-Config.RAG_CONVERSATION_MAX_TURNS:]
        logger.debug(f"Formatting {len(recent_history)} turns of conversation history.")
        
        for i, turn in enumerate(recent_history, 1):
            role = turn.get('role', 'unknown')
            content = turn.get('content', '').strip()
            
            if content:
                if role == 'user':
                    history_parts.append(f"**👤 您的问题 {i}**：{content}")
                elif role == 'assistant':
                    # 简化AI回答，只保留核心内容
                    simplified_content = self._simplify_ai_response(content)
                    history_parts.append(f"**🤖 我的回答 {i}**：{simplified_content}")
                    
                history_parts.append("")  # 空行分隔
        
        return "\n".join(history_parts)

    def _simplify_ai_response(self, response: str) -> str:
        """
        简化AI回答，提取关键信息 - 增强版
        
        Args:
            response: 原始AI回答
            
        Returns:
            str: 简化后的回答
        """
        # 提取主要回答部分
        main_answer_patterns = [
            r'\*\*主要回答\*\*[：:]?\s*(.+?)(?=\n\*\*|$)',
            r'(?:^|\n)([^*\n][^*\n]*?)(?=\n\*\*|$)',
        ]
        
        for pattern in main_answer_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                
                # 清理答案内容
                answer = re.sub(r'【来源\d+】', '', answer)  # 移除来源标记
                answer = re.sub(r'\s+', ' ', answer).strip()  # 标准化空白
                
                # 限制长度
                if len(answer) > 150:
                    # 尝试在句号处截断
                    sentences = re.split(r'[。！？.!?]', answer[:150])
                    if len(sentences) > 1:
                        answer = '。'.join(sentences[:-1]) + "。"
                    else:
                        answer = answer[:150] + "..."
                
                logger.debug(f"Simplified AI response to: {answer}")
                return answer
        
        # 如果没有找到格式化的答案，直接截取前150字符
        simplified = response[:150] + "..." if len(response) > 150 else response
        simplified = re.sub(r'【来源\d+】', '', simplified)
        simplified = re.sub(r'\s+', ' ', simplified).strip()
        
        return simplified

    def _optimize_prompt_length(self, prompt: str) -> str:
        """
        优化提示词长度，确保不超过token限制
        
        Args:
            prompt: 原始提示词
            
        Returns:
            str: 优化后的提示词
        """
        estimated_tokens = self._estimate_tokens(prompt)
        logger.debug(f"Estimated tokens for prompt: {estimated_tokens}. Max allowed context tokens: {self.max_context_tokens}")

        if estimated_tokens <= self.max_context_tokens:
            return prompt
        
        logger.warning(f"Prompt is too long ({estimated_tokens} tokens). Attempting to compress.")
        # 如果超长，需要压缩上下文部分
        compressed_prompt = self._compress_prompt(prompt, estimated_tokens)
        final_estimated_tokens = self._estimate_tokens(compressed_prompt)
        logger.info(f"Compressed prompt. Original tokens: {estimated_tokens}, New tokens: {final_estimated_tokens}")
        return compressed_prompt

    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量 - 改进版
        
        Args:
            text: 输入文本
            
        Returns:
            int: 估算的token数量
        """
        # 中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        # 英文单词数
        english_words = len(re.findall(r'\b[a-zA-Z0-9]+\b', text))
        
        # 特殊符号和标点
        special_chars = len(re.findall(r'[^\w\s\u4e00-\u9fff]', text))
        
        # 基于实际经验的token估算
        # 中文：1.3个字符≈1个token
        # 英文：4个字符≈1个token
        # 符号：按0.5计算
        estimated_tokens = int(chinese_chars * 1.3 + english_words * 1.0 + special_chars * 0.5)
        
        return estimated_tokens

    def _compress_prompt(self, prompt: str, current_tokens: int) -> str:
        """
        压缩提示词，主要通过截断上下文来实现
        
        Args:
            prompt: 原始提示词
            current_tokens: 当前估算的token数量
            
        Returns:
            str: 压缩后的提示词
        """
        # 分解提示词的各个部分
        parts = prompt.split("\n\n")
        
        # 找到文献内容部分
        context_start = -1
        context_end = -1
        for i, part in enumerate(parts):
            if "📚 相关文献内容" in part:
                context_start = i
            elif context_start != -1 and ("🤔 用户问题" in part or "💬 对话历史" in part or "重要指示" in part):
                context_end = i
                break
        
        if context_start == -1:
            logger.error("Could not find context section to compress")
            return prompt
        
        if context_end == -1:
            context_end = len(parts)
        
        # 计算非上下文部分的token
        non_context_parts = parts[:context_start] + parts[context_end:]
        non_context_text = "\n\n".join(non_context_parts)
        non_context_tokens = self._estimate_tokens(non_context_text)
        
        # 计算上下文部分允许的最大token
        allowed_context_tokens = self.max_context_tokens - non_context_tokens - 200  # 留200token缓冲
        
        if allowed_context_tokens <= 0:
            logger.error("Not enough tokens for context after reserving for other parts")
            return "\n\n".join(parts[:context_start] + ["## 📚 相关文献内容\n⚠️ 上下文内容因长度限制已被移除"] + parts[context_end:])
        
        # 压缩上下文部分
        context_parts = parts[context_start:context_end]
        context_text = "\n\n".join(context_parts)
        
        # 按来源逐个添加，直到达到token限制
        compressed_context = parts[context_start]  # 保留标题
        current_context_tokens = self._estimate_tokens(compressed_context)
        
        # 提取各个来源
        source_pattern = r'### 【来源\d+】.*?(?=### 【来源\d+】|---|\n\n💡|$)'
        sources = re.findall(source_pattern, context_text, re.DOTALL)
        
        for source in sources:
            source_tokens = self._estimate_tokens(source)
            if current_context_tokens + source_tokens <= allowed_context_tokens:
                compressed_context += "\n\n" + source
                current_context_tokens += source_tokens
            else:
                logger.info(f"Context truncation: Stopped adding sources. Used {current_context_tokens} of {allowed_context_tokens} allowed tokens")
                break
        
        # 重新组装提示词
        final_parts = parts[:context_start] + [compressed_context] + parts[context_end:]
        return "\n\n".join(final_parts)

    def build_preset_questions_prompt(self, literature_title: str, literature_summary: str = "") -> List[str]:
        """
        构建预设问题列表
        
        Args:
            literature_title: 文献标题
            literature_summary: 文献摘要（可选）
            
        Returns:
            List[str]: 预设问题列表
        """
        base_questions = [
            "这篇文献的主要论点是什么？",
            "文献中使用了哪些研究方法？",
            "这项研究有什么创新点和贡献？",
            "研究存在哪些局限性？",
            "主要结论和发现是什么？",
            "文献的理论框架是什么？",
            "研究的实际应用价值如何？",
            "文献中提到了哪些未来研究方向？"
        ]
        
        # 根据文献标题生成个性化问题
        if literature_title:
            title_based_questions = [
                f"请解释《{literature_title}》这篇文献的核心内容",
                f"《{literature_title}》与其他相关研究有什么区别？"
            ]
            base_questions.extend(title_based_questions)
        
        return base_questions[:8]  # 返回最多8个问题

    def build_error_response_prompt(self, error_type: str, question: str) -> str:
        """
        构建错误响应提示词 - 增强版
        
        Args:
            error_type: 错误类型
            question: 用户问题
            
        Returns:
            str: 错误响应内容
        """
        error_responses = {
            "no_content": f"""
抱歉，我在当前文献中没有找到与您的问题「{question}」相关的内容。

🔍 **建议尝试**：
1. 使用不同的关键词重新表述问题
2. 确认问题是否与当前文献的主题相关
3. 查看我提供的预设问题获取灵感
4. 尝试更具体或更宽泛的问题表述

💡 **提示**：您可以询问文献的主要内容、研究方法、主要发现等核心问题。
            """,
            
            "api_error": f"""
抱歉，AI服务暂时遇到技术问题，无法处理您的问题：「{question}」

🔧 **请稍后重试**：
- 系统正在自动恢复中
- 通常几分钟内即可恢复正常
- 您可以先查看预设问题或浏览文献内容

如果问题持续，请联系技术支持。
            """,
            
            "context_too_long": f"""
您的问题「{question}」涉及的内容较为广泛，建议将其分解为更具体的子问题。

📝 **建议分解方式**：
1. 将复合问题拆分为单个概念
2. 针对特定的研究方面提问
3. 逐步深入，从一般到具体

💡 **示例**：如果问题涉及多个理论，可以分别询问每个理论的内容。
            """,
            
            "low_confidence": f"""
基于当前文献内容，我对问题「{question}」的回答把握度较低。

⚠️ **可能原因**：
- 文献中相关信息有限
- 问题超出了文献的研究范围
- 需要更多背景信息才能准确回答

🎯 **建议**：
1. 尝试询问文献中明确讨论的主题
2. 参考预设问题获取思路
3. 查阅更多相关文献获得全面理解
            """
        }
        
        return error_responses.get(error_type, f"处理问题「{question}」时出现未知错误，请重试。")

    def validate_prompt_quality(self, prompt: str) -> Dict[str, Any]:
        """
        验证提示词质量 - 基于最佳实践
        
        Args:
            prompt: 提示词内容
            
        Returns:
            Dict: 质量评估结果
        """
        validation_result = {
            "is_valid": True,
            "issues": [],
            "token_count": self._estimate_tokens(prompt),
            "has_context": "📚 相关文献内容" in prompt,
            "has_role_definition": "专业文献研究助手" in prompt,
            "has_capability_list": "核心能力" in prompt,
            "has_limitation_list": "严格限制" in prompt,
            "has_format_specification": "响应格式协议" in prompt,
            "has_citation_guidance": "引用标注规范" in prompt,
            "quality_score": 0.0
        }
        
        # 检查长度
        if validation_result["token_count"] > self.max_context_tokens:
            validation_result["issues"].append("提示词过长")
            validation_result["is_valid"] = False
        
        # 检查必要组件
        required_components = [
            ("has_context", "缺少文献内容"),
            ("has_role_definition", "缺少角色定义"),
            ("has_capability_list", "缺少能力说明"),
            ("has_limitation_list", "缺少限制说明"),
            ("has_format_specification", "缺少格式规范"),
            ("has_citation_guidance", "缺少引用指导")
        ]
        
        valid_components = 0
        for component, error_msg in required_components:
            if validation_result[component]:
                valid_components += 1
            else:
                validation_result["issues"].append(error_msg)
        
        # 计算质量分数
        validation_result["quality_score"] = valid_components / len(required_components)
        
        # 如果质量分数低于0.8，标记为无效
        if validation_result["quality_score"] < 0.8:
            validation_result["is_valid"] = False
        
        return validation_result 
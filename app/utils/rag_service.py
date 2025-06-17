"""
RAG问答系统核心服务

统筹整个RAG问答流程，协调各个组件完成智能问答
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import traceback
import re

# 导入相关组件
from app.utils.embedding_service import embedding_service
from app.utils.vector_store import vector_store
from app.utils.prompt_builder import PromptBuilder
from app.utils.answer_processor import AnswerProcessor
from app.utils.cache_manager import cache_manager
from app.config import Config

# Google AI 相关导入
from google import genai
from google.genai import types

class RAGService:
    """RAG问答系统核心服务类"""
    
    def __init__(self):
        """初始化RAG服务"""
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.prompt_builder = PromptBuilder()
        self.answer_processor = AnswerProcessor()
        
        # 配置参数
        self.max_context_tokens = Config.RAG_MAX_CONTEXT_TOKENS
        self.top_k_retrieval = Config.RAG_TOP_K_RETRIEVAL
        self.ai_timeout = Config.RAG_AI_TIMEOUT
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化Google AI
        self._init_google_ai()

    def _init_google_ai(self):
        """初始化Google AI服务"""
        try:
            # 检查API密钥
            if not Config.GOOGLE_API_KEY:
                self.logger.error("Google API密钥未配置")
                self.client = None
                return
            
            # 创建Google GenAI客户端
            self.client = genai.Client(api_key=Config.GOOGLE_API_KEY)
            
            # 使用最新的模型
            self.model_name = Config.GEMINI_MODEL  # gemini-2.0-flash-exp
            
            self.logger.info(f"Google AI服务初始化成功，使用模型: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Google AI服务初始化失败: {str(e)}")
            self.client = None

    async def process_question(
        self,
        question: str,
        literature_id: str,
        group_id: str,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理用户问题的完整RAG流程（带缓存支持）
        
        Args:
            question: 用户问题
            literature_id: 文献ID
            group_id: 研究组ID
            session_id: 会话ID（可选）
            conversation_history: 对话历史（可选）
            top_k: 检索数量（可选）
            
        Returns:
            Dict: 处理结果
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"开始处理问题: {question[:50]}... (文献ID: {literature_id})")
            
            # 1. 问题预处理和验证
            validated_question = self._preprocess_question(question)
            if not validated_question:
                return self._create_error_response("invalid_question", question)
            
            # 2. 并行执行Embedding生成和历史处理
            embedding_task = self._generate_question_embedding(validated_question)
            history_task = self._process_conversation_history(conversation_history)
            
            # 等待并行任务完成
            question_embedding, processed_history = await asyncio.gather(
                embedding_task, history_task, return_exceptions=True
            )
            
            # 检查并行任务结果
            if isinstance(question_embedding, Exception):
                self.logger.error(f"Embedding生成失败: {str(question_embedding)}")
                return self._create_error_response("embedding_failed", question)
            
            if isinstance(processed_history, Exception):
                self.logger.warning(f"历史处理失败: {str(processed_history)}")
                processed_history = []
            
            # 3. 检索相关文档块
            context_chunks = await self._retrieve_relevant_chunks(
                question_embedding, literature_id, group_id, top_k or self.top_k_retrieval
            )
            
            if not context_chunks:
                return self._create_error_response("no_relevant_content", question)
            
            # 4. 检查答案缓存
            cached_answer = cache_manager.get_answer(validated_question, literature_id, context_chunks)
            if cached_answer is not None:
                self.logger.info(f"答案缓存命中: {question[:30]}...")
                # 更新处理时间
                processing_time = (datetime.now() - start_time).total_seconds()
                cached_answer["metadata"]["processing_time"] = processing_time
                cached_answer["metadata"]["from_cache"] = True
                return cached_answer
            
            # 5. 构建提示词
            prompt = self.prompt_builder.build_qa_prompt(
                validated_question, context_chunks, processed_history
            )
            
            # 验证提示词质量
            prompt_validation = self.prompt_builder.validate_prompt_quality(prompt)
            if not prompt_validation["is_valid"]:
                self.logger.warning(f"提示词质量问题: {prompt_validation['issues']}")
                # 尝试压缩提示词
                prompt = self.prompt_builder._compress_prompt(prompt)
            
            # 6. 调用AI生成答案
            raw_answer = await self._generate_ai_answer(prompt)
            if not raw_answer:
                return self._create_error_response("ai_generation_failed", question)
            
            # 7. 处理答案
            processed_answer = self.answer_processor.process_answer(
                raw_answer, context_chunks, validated_question, literature_id
            )
            
            # 8. 添加元数据
            processing_time = (datetime.now() - start_time).total_seconds()
            processed_answer["metadata"].update({
                "session_id": session_id,
                "group_id": group_id,
                "processing_time": processing_time,
                "prompt_tokens": self.prompt_builder._estimate_tokens(prompt),
                "chunks_retrieved": len(context_chunks),
                "from_cache": False
            })
            
            # 9. 缓存答案
            cache_manager.set_answer(validated_question, literature_id, context_chunks, processed_answer)
            
            self.logger.info(f"问题处理完成，耗时: {processing_time:.2f}秒")
            return processed_answer
            
        except Exception as e:
            self.logger.error(f"RAG处理出错: {str(e)}\n{traceback.format_exc()}")
            return self._create_error_response("system_error", question)

    def _preprocess_question(self, question: str) -> Optional[str]:
        """
        预处理用户问题
        
        Args:
            question: 原始问题
            
        Returns:
            Optional[str]: 处理后的问题，如果无效则返回None
        """
        if not question or not question.strip():
            return None
        
        # 清理和标准化问题
        cleaned_question = question.strip()
        
        # 长度检查
        if len(cleaned_question) < 2:
            return None
        if len(cleaned_question) > 1000:
            cleaned_question = cleaned_question[:1000] + "..."
        
        # 移除多余的空白字符
        cleaned_question = ' '.join(cleaned_question.split())
        
        return cleaned_question

    async def _generate_question_embedding(self, question: str) -> List[float]:
        """
        生成问题的embedding
        
        Args:
            question: 用户问题
            
        Returns:
            List[float]: 问题的embedding向量
        """
        try:
            # 使用异步方式生成embedding
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.embedding_service.generate_query_embedding, 
                question
            )
            return embedding
        except Exception as e:
            self.logger.error(f"生成问题embedding失败: {str(e)}")
            raise

    async def _process_conversation_history(self, history: Optional[List[Dict]]) -> List[Dict]:
        """
        处理对话历史
        
        Args:
            history: 原始对话历史
            
        Returns:
            List[Dict]: 处理后的对话历史
        """
        if not history:
            return []
        
        try:
            # 过滤和清理历史记录
            processed_history = []
            for turn in history[-Config.RAG_CONVERSATION_MAX_TURNS:]:
                if isinstance(turn, dict) and turn.get("content"):
                    processed_turn = {
                        "role": turn.get("role", "user"),
                        "content": turn["content"][:500],  # 限制长度
                        "timestamp": turn.get("timestamp", "")
                    }
                    processed_history.append(processed_turn)
            
            return processed_history
        except Exception as e:
            self.logger.warning(f"处理对话历史失败: {str(e)}")
            return []

    async def _retrieve_relevant_chunks(
        self, 
        question_embedding: List[float], 
        literature_id: str, 
        group_id: str, 
        top_k: int
    ) -> List[Dict]:
        """
        检索相关文档块
        
        Args:
            question_embedding: 问题embedding
            literature_id: 文献ID
            group_id: 研究组ID
            top_k: 检索数量
            
        Returns:
            List[Dict]: 相关文档块列表
        """
        try:
            self.logger.debug(f"开始检索相关文档块：literature_id={literature_id}, group_id={group_id}, top_k={top_k}")
            
            # 增加检索数量以提高找到高质量文档的概率
            search_top_k = max(top_k * 3, 20)  # 至少检索20个，或者是目标数量的3倍
            
            # 使用异步方式检索
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None,
                self.vector_store.search_similar_chunks,
                question_embedding,
                group_id,
                literature_id,
                search_top_k  # 使用更大的检索数量
            )
            
            self.logger.info(f"原始检索结果数量: {len(chunks)}")
            
            # 记录原始检索结果的详细信息
            if chunks:
                for i, chunk in enumerate(chunks[:5]):  # 只记录前5个
                    self.logger.debug(f"原始chunk {i}: similarity={chunk.get('similarity', 'N/A'):.4f}, "
                                    f"raw_distance={chunk.get('raw_distance', 'N/A'):.4f}, "
                                    f"chunk_index={chunk.get('chunk_index', 'N/A')}, "
                                    f"text_preview='{chunk.get('text', '')[:100]}'...")
            else:
                self.logger.warning("没有检索到任何文档块")
            
            # 重排序和过滤
            reranked_chunks = self._rerank_chunks(chunks, top_k)
            
            self.logger.info(f"重排序后返回文档块数量: {len(reranked_chunks)}")
            
            return reranked_chunks
            
        except Exception as e:
            self.logger.error(f"检索相关文档块失败: {str(e)}")
            return []

    def _rerank_chunks(self, chunks: List[Dict], top_k: int) -> List[Dict]:
        """
        重排序文档块
        
        Args:
            chunks: 原始文档块
            top_k: 返回数量
            
        Returns:
            List[Dict]: 重排序后的文档块
        """
        if not chunks:
            self.logger.debug("没有文档块需要重排序")
            return []
        
        self.logger.debug(f"开始重排序 {len(chunks)} 个文档块，目标返回 {top_k} 个")
        
        # 设置多层次的相似度阈值
        HIGH_SIMILARITY_THRESHOLD = 0.6  # 高相似度阈值
        MEDIUM_SIMILARITY_THRESHOLD = 0.4  # 中等相似度阈值
        MIN_SIMILARITY_THRESHOLD = 0.3  # 最低相似度阈值
        
        # 首先尝试获取高质量文档
        high_quality_chunks = []
        medium_quality_chunks = []
        low_quality_chunks = []
        
        for chunk in chunks:
            similarity = chunk.get("similarity", 0)
            text_quality = self._evaluate_text_quality(chunk.get("text", ""))
            
            # 根据相似度和文档质量分类
            if similarity >= HIGH_SIMILARITY_THRESHOLD:
                high_quality_chunks.append(chunk)
            elif similarity >= MEDIUM_SIMILARITY_THRESHOLD:
                # 中等相似度的文档，如果质量高也保留
                if text_quality >= 0.3:
                    medium_quality_chunks.append(chunk)
                else:
                    self.logger.debug(f"过滤中等相似度低质量文档: similarity={similarity:.3f}, quality={text_quality:.3f}")
            elif similarity >= MIN_SIMILARITY_THRESHOLD:
                # 低相似度的文档，只有质量很高才保留
                if text_quality >= 0.5:
                    low_quality_chunks.append(chunk)
                    self.logger.debug(f"保留低相似度高质量文档: similarity={similarity:.3f}, quality={text_quality:.3f}")
                else:
                    self.logger.debug(f"过滤低相似度文档: similarity={similarity:.3f}, quality={text_quality:.3f}")
            else:
                self.logger.debug(f"过滤超低相似度文档: similarity={similarity:.3f}")
        
        # 合并筛选后的文档块，优先级：高>中>低
        filtered_chunks = high_quality_chunks + medium_quality_chunks + low_quality_chunks
        
        if not filtered_chunks:
            self.logger.warning(f"经过质量和相似度过滤后无可用文档块")
            # 如果完全没有，则返回原始的最佳几个文档（降级处理）
            if chunks:
                self.logger.info("执行降级策略：返回原始最佳文档块")
                filtered_chunks = sorted(chunks, key=lambda x: x.get("similarity", 0), reverse=True)[:3]
            else:
                return []
        
        self.logger.debug(f"文档质量分类: 高质量={len(high_quality_chunks)}, 中质量={len(medium_quality_chunks)}, 低质量={len(low_quality_chunks)}")
        self.logger.debug(f"过滤后保留 {len(filtered_chunks)} 个文档块")
        
        # 基于相似度和其他因素重排序
        scored_chunks = []
        for i, chunk in enumerate(filtered_chunks):
            similarity = chunk.get("similarity", 0)
            text = chunk.get("text", "")
            text_length = len(text)
            
            # 评估文档质量（如果还没评估过）
            if "text_quality" not in chunk:
                text_quality = self._evaluate_text_quality(text)
                chunk["text_quality"] = text_quality
            else:
                text_quality = chunk["text_quality"]
            
            # 综合评分：相似度(50%) + 文档质量(30%) + 长度因子(20%)
            length_factor = min(text_length / 500, 1.0)  # 适中长度加分
            score = similarity * 0.5 + text_quality * 0.3 + length_factor * 0.2
            
            chunk["final_score"] = score
            scored_chunks.append(chunk)
            
            self.logger.debug(f"Chunk {i}: similarity={similarity:.3f}, quality={text_quality:.3f}, "
                            f"length={text_length}, final_score={score:.3f}")
        
        # 按综合得分排序
        scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)
        
        # 返回前top_k个结果
        final_chunks = scored_chunks[:top_k]
        
        # 记录最终选择的文档块信息
        for i, chunk in enumerate(final_chunks):
            self.logger.debug(f"Final chunk {i}: final_score={chunk['final_score']:.3f}, "
                            f"similarity={chunk.get('similarity', 0):.3f}, "
                            f"chunk_index={chunk.get('chunk_index', 'unknown')}")
        
        self.logger.debug(f"重排序完成，返回 {len(final_chunks)} 个高质量文档块")
        return final_chunks
    
    def _evaluate_text_quality(self, text: str) -> float:
        """
        评估文本块的质量
        
        Args:
            text: 文本内容
            
        Returns:
            float: 质量分数 (0-1)
        """
        if not text:
            return 0.0
        
        quality_score = 0.0
        text_lower = text.lower()
        
        # 检查是否包含高价值的学术内容关键词
        high_value_keywords = [
            # 中文关键词
            '摘要', '结论', '创新', '贡献', '意义', '目的', '方法', '结果', 
            '讨论', '背景', '研究', '发现', '提出', '证明', '表明', '显示',
            '分析', '实验', '理论', '模型', '算法', '技术', '系统',
            
            # 英文关键词  
            'abstract', 'conclusion', 'novelty', 'contribution', 'significance',
            'purpose', 'method', 'result', 'discussion', 'background', 
            'research', 'finding', 'propose', 'demonstrate', 'show', 'indicate',
            'analysis', 'experiment', 'theory', 'model', 'algorithm', 'system',
            'innovation', 'approach', 'framework', 'investigation', 'study'
        ]
        
        # 低价值内容关键词（版权、格式等）
        low_value_keywords = [
            'creative commons', 'attribution', 'license', 'copyright', 
            'permission', 'reproduce', 'distribution', 'doi.org',
            '版权', '许可', '授权', '转载', '引用格式'
        ]
        
        # 计算高价值关键词匹配度
        high_value_matches = sum(1 for keyword in high_value_keywords if keyword in text_lower)
        quality_score += min(high_value_matches * 0.1, 0.4)  # 最多0.4分
        
        # 检查低价值内容，降低分数
        low_value_matches = sum(1 for keyword in low_value_keywords if keyword in text_lower)
        quality_score -= min(low_value_matches * 0.2, 0.3)  # 最多扣0.3分
        
        # 检查文本长度合理性
        if 100 <= len(text) <= 2000:
            quality_score += 0.2
        elif len(text) < 50:
            quality_score -= 0.2
            
        # 检查是否主要是数字和符号（低质量指标）
        non_alphanumeric_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
        if non_alphanumeric_ratio > 0.3:
            quality_score -= 0.2
            
        # 检查是否包含完整句子
        sentence_count = len([s for s in text.split('.') if len(s.strip()) > 10])
        if sentence_count >= 2:
            quality_score += 0.1
            
        return max(0.0, min(1.0, quality_score))

    async def _generate_ai_answer(self, prompt: str) -> Optional[str]:
        """
        使用AI生成答案
        
        Args:
            prompt: 完整的提示词
            
        Returns:
            Optional[str]: AI生成的答案
        """
        if not self.client:
            self.logger.error("Google AI客户端未初始化")
            return None
        
        try:
            # 使用异步方式调用AI
            loop = asyncio.get_event_loop()
            
            # 生成配置
            config = types.GenerateContentConfig(
                temperature=0.3,  # 较低的温度保证准确性
                top_p=0.8,
                max_output_tokens=2000,
                candidate_count=1
            )
            
            # 使用最新的API格式异步调用
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_name,
                    contents=[prompt],
                    config=config
                )
            )
            
            if response and hasattr(response, 'text') and response.text:
                return response.text
            else:
                self.logger.warning("AI返回空响应")
                return None
                
        except Exception as e:
            self.logger.error(f"AI生成答案失败: {str(e)}")
            return None

    def get_preset_questions(self, literature_id: str, literature_title: str = "") -> List[str]:
        """
        获取预设问题列表
        
        Args:
            literature_id: 文献ID
            literature_title: 文献标题
            
        Returns:
            List[str]: 预设问题列表
        """
        try:
            return self.prompt_builder.build_preset_questions_prompt(literature_title)
        except Exception as e:
            self.logger.error(f"生成预设问题失败: {str(e)}")
            return [
                "这篇文献的主要论点是什么？",
                "文献中使用了哪些研究方法？",
                "这项研究有什么创新点？",
                "研究存在哪些局限性？",
                "主要结论是什么？"
            ]

    def _create_error_response(self, error_type: str, question: str) -> Dict[str, Any]:
        """
        创建错误响应
        
        Args:
            error_type: 错误类型
            question: 用户问题
            
        Returns:
            Dict[str, Any]: 错误响应
        """
        if error_type == "no_content":
            # 根据问题类型给出不同的建议
            high_level_questions = [
                "主要论点", "创新点", "贡献", "研究背景", "理论意义", "应用价值", 
                "结论", "发现", "意义"
            ]
            
            is_high_level = any(keyword in question for keyword in high_level_questions)
            
            if is_high_level:
                answer = """抱歉，当前检索到的文档片段主要包含技术细节、数据分析和方法描述，缺少能够回答您关于"{}"这类高层次问题的核心内容（如摘要、引言、结论等）。

建议：
1. 尝试询问更具体的技术问题，如"使用了什么研究方法？"、"实验设计是怎样的？"
2. 或者重新上传文献，确保包含完整的摘要和结论部分

我可以基于现有内容回答技术细节相关的问题。""".format(question)
            else:
                answer = "抱歉，在当前检索到的文档内容中，我无法找到足够相关的信息来回答您的问题。请尝试重新表述问题或询问文献中的其他内容。"
        else:
            answer = "处理您的问题时遇到了技术问题，请稍后重试。"
        
        return {
            "answer": answer,
            "key_findings": [],
            "limitations": "由于处理过程中出现问题，无法提供详细的分析。",
            "sources": [],
            "confidence": 0.1,
            "quality_score": {
                "relevance": 0.1,
                "completeness": 0.1,
                "accuracy": 0.1,
                "clarity": 0.1,
                "citation": 0.1
            },
            "metadata": {
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "is_fallback": True,
                "processing_time": 0.0
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        系统健康检查
        
        Returns:
            Dict: 健康检查结果
        """
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 检查Embedding服务
            try:
                test_embedding = await self._generate_question_embedding("测试")
                health_status["components"]["embedding_service"] = {
                    "status": "healthy" if test_embedding else "unhealthy",
                    "details": f"返回{len(test_embedding)}维向量" if test_embedding else "无法生成embedding"
                }
            except Exception as e:
                health_status["components"]["embedding_service"] = {
                    "status": "unhealthy",
                    "details": str(e)
                }
            
            # 检查向量数据库
            try:
                vector_health = self.vector_store.health_check()
                health_status["components"]["vector_store"] = vector_health
            except Exception as e:
                health_status["components"]["vector_store"] = {
                    "status": "unhealthy",
                    "details": str(e)
                }
            
            # 检查AI服务
            try:
                if self.client:
                    # 简单测试
                    test_response = await self._generate_ai_answer("你好，这是一个测试。请简单回复。")
                    health_status["components"]["ai_service"] = {
                        "status": "healthy" if test_response else "unhealthy",
                        "details": "AI服务正常" if test_response else "AI服务无响应"
                    }
                else:
                    health_status["components"]["ai_service"] = {
                        "status": "unhealthy",
                        "details": "AI客户端未初始化"
                    }
            except Exception as e:
                health_status["components"]["ai_service"] = {
                    "status": "unhealthy",
                    "details": str(e)
                }
            
            # 综合状态判断
            unhealthy_components = [
                name for name, component in health_status["components"].items()
                if component["status"] != "healthy"
            ]
            
            if unhealthy_components:
                health_status["status"] = "degraded" if len(unhealthy_components) == 1 else "unhealthy"
                health_status["unhealthy_components"] = unhealthy_components
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status

    def get_service_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息
        
        Returns:
            Dict: 服务统计信息
        """
        return {
            "service_name": "RAG问答服务",
            "version": "1.0.0",
            "config": {
                "max_context_tokens": self.max_context_tokens,
                "top_k_retrieval": self.top_k_retrieval,
                "ai_timeout": self.ai_timeout
            },
            "components": {
                "prompt_builder": "PromptBuilder",
                "answer_processor": "AnswerProcessor",
                "embedding_service": "EmbeddingService",
                "vector_store": "VectorStore"
            },
            "timestamp": datetime.now().isoformat()
        }


# 创建全局RAG服务实例
rag_service = RAGService() 
"""
RAG问答系统对话管理器

负责管理对话历史、会话状态和上下文压缩
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.conversation import QASession, ConversationTurn, ConversationSummary
from app.database import get_db
from app.config import Config

class ConversationManager:
    """对话管理器类"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.max_history_turns = Config.RAG_CONVERSATION_MAX_TURNS
        self.max_tokens_per_turn = 500
        self.compression_threshold = 0.8
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
    
    def create_session(
        self,
        user_id: int,
        group_id: str,
        literature_id: str,
        session_title: str = None,
        db: Session = None
    ) -> str:
        """
        创建新的对话会话
        
        Args:
            user_id: 用户ID
            group_id: 研究组ID
            literature_id: 文献ID
            session_title: 会话标题（可选）
            db: 数据库会话
            
        Returns:
            str: 会话ID
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 创建新会话
            session = QASession(
                user_id=user_id,
                group_id=group_id,
                literature_id=literature_id,
                session_title=session_title or f"会话-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            
            self.logger.info(f"创建新会话: {session.session_id}")
            return session.session_id
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"创建会话失败: {str(e)}")
            raise

    def get_or_create_session(
        self,
        user_id: int,
        group_id: str,
        literature_id: str,
        session_id: str = None,
        db: Session = None
    ) -> str:
        """
        获取或创建对话会话
        
        Args:
            user_id: 用户ID
            group_id: 研究组ID
            literature_id: 文献ID
            session_id: 会话ID（可选）
            db: 数据库会话
            
        Returns:
            str: 会话ID
        """
        if db is None:
            db = next(get_db())
        
        # 如果提供了session_id，尝试获取现有会话
        if session_id:
            existing_session = db.query(QASession).filter(
                and_(
                    QASession.session_id == session_id,
                    QASession.user_id == user_id,
                    QASession.is_active == True
                )
            ).first()
            
            if existing_session:
                # 更新最后活动时间
                existing_session.update_activity()
                db.commit()
                return existing_session.session_id
        
        # 创建新会话
        return self.create_session(user_id, group_id, literature_id, db=db)

    def add_qa_turn(
        self,
        session_id: str,
        question: str,
        answer: str = None,
        confidence: float = 0.0,
        quality_scores: Dict = None,
        chunks_used: int = 0,
        processing_time: float = 0.0,
        prompt_tokens: int = 0,
        metadata: Dict = None,
        db: Session = None
    ) -> str:
        """
        添加问答轮次
        
        Args:
            session_id: 会话ID
            question: 用户问题
            answer: AI回答（可选）
            confidence: 置信度
            quality_scores: 质量评分
            chunks_used: 使用的文档块数量
            processing_time: 处理时间
            prompt_tokens: 提示词token数
            metadata: 额外元数据
            db: 数据库会话
            
        Returns:
            str: 轮次ID
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 获取会话
            session = db.query(QASession).filter(QASession.session_id == session_id).first()
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
            
            # 获取下一个轮次索引
            next_turn_index = session.turn_count + 1
            
            # 创建新轮次
            turn = ConversationTurn(
                session_id=session_id,
                turn_index=next_turn_index,
                question=question,
                answer=answer,
                confidence=confidence,
                quality_scores=quality_scores or {},
                chunks_used=chunks_used,
                processing_time=processing_time,
                prompt_tokens=prompt_tokens
            )
            
            # 设置元数据
            if metadata:
                turn.answer_metadata.update(metadata)
            
            # 添加到数据库
            db.add(turn)
            
            # 更新会话统计
            session.increment_turn_count()
            session.add_question()
            if answer:
                session.add_answer(confidence)
            
            db.commit()
            db.refresh(turn)
            
            self.logger.info(f"添加对话轮次: {turn.turn_id} (会话: {session_id})")
            return turn.turn_id
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"添加对话轮次失败: {str(e)}")
            raise

    def update_turn_answer(
        self,
        turn_id: str,
        answer: str,
        confidence: float,
        quality_scores: Dict = None,
        metadata: Dict = None,
        db: Session = None
    ) -> bool:
        """
        更新轮次的答案信息
        
        Args:
            turn_id: 轮次ID
            answer: AI回答
            confidence: 置信度
            quality_scores: 质量评分
            metadata: 额外元数据
            db: 数据库会话
            
        Returns:
            bool: 是否成功更新
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 获取轮次
            turn = db.query(ConversationTurn).filter(ConversationTurn.turn_id == turn_id).first()
            if not turn:
                return False
            
            # 更新答案信息
            turn.set_answer(answer, confidence, quality_scores, metadata)
            
            # 更新会话统计
            session = db.query(QASession).filter(QASession.session_id == turn.session_id).first()
            if session:
                session.add_answer(confidence)
                session.update_activity()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"更新轮次答案失败: {str(e)}")
            return False

    def get_conversation_history(
        self,
        session_id: str,
        max_turns: int = None,
        include_metadata: bool = False,
        db: Session = None
    ) -> List[Dict]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            max_turns: 最大轮次数
            include_metadata: 是否包含元数据
            db: 数据库会话
            
        Returns:
            List[Dict]: 对话历史列表
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 设置默认值
            if max_turns is None:
                max_turns = self.max_history_turns
            
            # 查询对话轮次
            turns_query = db.query(ConversationTurn).filter(
                ConversationTurn.session_id == session_id
            ).order_by(desc(ConversationTurn.turn_index)).limit(max_turns)
            
            turns = turns_query.all()
            
            # 转换为对话格式
            history = []
            for turn in reversed(turns):  # 反转以获得正确的时间顺序
                conversation_turns = turn.to_conversation_format()
                history.extend(conversation_turns)
            
            return history
            
        except Exception as e:
            self.logger.error(f"获取对话历史失败: {str(e)}")
            return []

    def get_relevant_history(
        self,
        session_id: str,
        current_question: str,
        max_turns: int = 5,
        db: Session = None
    ) -> List[Dict]:
        """
        获取与当前问题相关的历史
        
        Args:
            session_id: 会话ID
            current_question: 当前问题
            max_turns: 最大轮次数
            db: 数据库会话
            
        Returns:
            List[Dict]: 相关的对话历史
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 获取最近的对话历史
            recent_history = self.get_conversation_history(
                session_id, max_turns * 2, db=db
            )
            
            if not recent_history:
                return []
            
            # 简单的相关性筛选（基于关键词匹配）
            relevant_history = self._filter_relevant_history(
                recent_history, current_question, max_turns
            )
            
            return relevant_history
            
        except Exception as e:
            self.logger.error(f"获取相关历史失败: {str(e)}")
            return []

    def _filter_relevant_history(
        self,
        history: List[Dict],
        current_question: str,
        max_turns: int
    ) -> List[Dict]:
        """
        过滤相关的对话历史
        
        Args:
            history: 完整对话历史
            current_question: 当前问题
            max_turns: 最大轮次数
            
        Returns:
            List[Dict]: 过滤后的相关历史
        """
        if not history:
            return []
        
        # 提取当前问题的关键词
        question_keywords = self._extract_keywords(current_question)
        
        # 计算每个历史轮次的相关性
        scored_history = []
        for turn in history:
            if turn.get("role") == "user":
                content = turn.get("content", "")
                content_keywords = self._extract_keywords(content)
                
                # 计算关键词重叠度
                overlap = len(set(question_keywords) & set(content_keywords))
                relevance_score = overlap / max(len(question_keywords), 1)
                
                scored_history.append({
                    "turn": turn,
                    "relevance": relevance_score
                })
        
        # 按相关性排序并取最相关的
        scored_history.sort(key=lambda x: x["relevance"], reverse=True)
        
        # 构建相关历史（包含前后文）
        relevant_history = []
        added_indices = set()
        
        for item in scored_history[:max_turns]:
            turn_index = next(
                (i for i, h in enumerate(history) if h == item["turn"]), -1
            )
            
            if turn_index != -1 and turn_index not in added_indices:
                # 添加用户问题
                relevant_history.append(history[turn_index])
                added_indices.add(turn_index)
                
                # 添加对应的AI回答（如果存在）
                if turn_index + 1 < len(history) and turn_index + 1 not in added_indices:
                    next_turn = history[turn_index + 1]
                    if next_turn.get("role") == "assistant":
                        relevant_history.append(next_turn)
                        added_indices.add(turn_index + 1)
        
        return relevant_history

    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取文本关键词
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 关键词列表
        """
        import re
        
        # 简单的关键词提取
        stopwords = {'的', '是', '在', '有', '和', '与', '对', '为', '了', '也', '可以', '能够', '这个', '那个', '什么', '如何', '怎么', '请问'}
        
        # 提取中文词汇和英文单词
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', text)
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 过滤停用词和短词
        keywords = []
        for word in chinese_words + english_words:
            if len(word) >= 2 and word not in stopwords:
                keywords.append(word)
        
        return keywords[:10]  # 返回前10个关键词

    def compress_history(
        self,
        session_id: str,
        target_turns: int = 5,
        db: Session = None
    ) -> Optional[str]:
        """
        压缩对话历史
        
        Args:
            session_id: 会话ID
            target_turns: 目标轮次数
            db: 数据库会话
            
        Returns:
            Optional[str]: 摘要ID
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 获取会话信息
            session = db.query(QASession).filter(QASession.session_id == session_id).first()
            if not session or session.turn_count <= target_turns:
                return None
            
            # 获取需要压缩的轮次
            turns_to_compress = db.query(ConversationTurn).filter(
                ConversationTurn.session_id == session_id
            ).order_by(ConversationTurn.turn_index).limit(
                session.turn_count - target_turns
            ).all()
            
            if not turns_to_compress:
                return None
            
            # 生成摘要
            summary_text = self._generate_summary(turns_to_compress)
            key_topics = self._extract_key_topics(turns_to_compress)
            important_entities = self._extract_important_entities(turns_to_compress)
            
            # 创建摘要记录
            summary = ConversationSummary(
                session_id=session_id,
                summary_text=summary_text,
                key_topics=key_topics,
                important_entities=important_entities,
                start_turn_index=turns_to_compress[0].turn_index,
                end_turn_index=turns_to_compress[-1].turn_index,
                compression_ratio=len(summary_text) / sum(len(turn.question + (turn.answer or "")) for turn in turns_to_compress)
            )
            
            db.add(summary)
            db.commit()
            db.refresh(summary)
            
            self.logger.info(f"创建会话摘要: {summary.summary_id}")
            return summary.summary_id
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"压缩历史失败: {str(e)}")
            return None

    def _generate_summary(self, turns: List[ConversationTurn]) -> str:
        """
        生成对话摘要
        
        Args:
            turns: 对话轮次列表
            
        Returns:
            str: 摘要文本
        """
        if not turns:
            return ""
        
        # 简单的摘要生成策略
        topics = []
        for turn in turns:
            question = turn.question[:100]  # 限制长度
            if turn.answer:
                answer_preview = turn.answer[:200]
                topics.append(f"问：{question}\n答：{answer_preview}")
            else:
                topics.append(f"问：{question}")
        
        summary = "对话主要涉及以下内容：\n" + "\n\n".join(topics)
        return summary[:1000]  # 限制摘要长度

    def _extract_key_topics(self, turns: List[ConversationTurn]) -> List[str]:
        """
        提取关键话题
        
        Args:
            turns: 对话轮次列表
            
        Returns:
            List[str]: 关键话题列表
        """
        all_text = " ".join([turn.question + (turn.answer or "") for turn in turns])
        keywords = self._extract_keywords(all_text)
        
        # 简单的话题聚类（基于关键词频率）
        from collections import Counter
        keyword_freq = Counter(keywords)
        
        # 返回最频繁的关键词作为话题
        return [keyword for keyword, freq in keyword_freq.most_common(5)]

    def _extract_important_entities(self, turns: List[ConversationTurn]) -> List[str]:
        """
        提取重要实体
        
        Args:
            turns: 对话轮次列表
            
        Returns:
            List[str]: 重要实体列表
        """
        import re
        
        all_text = " ".join([turn.question + (turn.answer or "") for turn in turns])
        
        # 简单的实体识别（数字、专有名词等）
        entities = []
        
        # 提取数字
        numbers = re.findall(r'\d+(?:\.\d+)?%?', all_text)
        entities.extend(numbers[:3])
        
        # 提取可能的专有名词（连续的大写字母开头的词）
        proper_nouns = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', all_text)
        entities.extend(proper_nouns[:3])
        
        return list(set(entities))[:5]  # 去重并限制数量

    def get_session_summary(
        self,
        session_id: str,
        db: Session = None
    ) -> Optional[Dict]:
        """
        获取会话摘要
        
        Args:
            session_id: 会话ID
            db: 数据库会话
            
        Returns:
            Optional[Dict]: 会话摘要信息
        """
        if db is None:
            db = next(get_db())
        
        try:
            session = db.query(QASession).filter(QASession.session_id == session_id).first()
            if not session:
                return None
            
            # 获取最新的摘要
            latest_summary = db.query(ConversationSummary).filter(
                ConversationSummary.session_id == session_id
            ).order_by(desc(ConversationSummary.created_at)).first()
            
            summary_info = session.to_dict()
            if latest_summary:
                summary_info["latest_summary"] = latest_summary.to_dict()
            
            return summary_info
            
        except Exception as e:
            self.logger.error(f"获取会话摘要失败: {str(e)}")
            return None

    def delete_session(
        self,
        session_id: str,
        user_id: int,
        db: Session = None
    ) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            bool: 是否成功删除
        """
        if db is None:
            db = next(get_db())
        
        try:
            # 验证会话所有权
            session = db.query(QASession).filter(
                and_(
                    QASession.session_id == session_id,
                    QASession.user_id == user_id
                )
            ).first()
            
            if not session:
                return False
            
            # 删除会话（级联删除相关记录）
            db.delete(session)
            db.commit()
            
            self.logger.info(f"删除会话: {session_id}")
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"删除会话失败: {str(e)}")
            return False

    def cleanup_old_sessions(
        self,
        days_old: int = 30,
        db: Session = None
    ) -> int:
        """
        清理旧会话
        
        Args:
            days_old: 天数阈值
            db: 数据库会话
            
        Returns:
            int: 清理的会话数量
        """
        if db is None:
            db = next(get_db())
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # 查找旧会话
            old_sessions = db.query(QASession).filter(
                QASession.last_activity < cutoff_date
            ).all()
            
            count = len(old_sessions)
            
            # 删除旧会话
            for session in old_sessions:
                db.delete(session)
            
            db.commit()
            
            self.logger.info(f"清理了 {count} 个旧会话")
            return count
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"清理旧会话失败: {str(e)}")
            return 0


# 创建全局对话管理器实例
conversation_manager = ConversationManager() 
"""
对话管理数据模型

定义问答会话和对话轮次的数据结构
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from app.models.base import BaseModel

class QASession(BaseModel):
    """问答会话模型"""
    __tablename__ = "qa_sessions"
    
    # 主键
    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    group_id = Column(String(36), ForeignKey("research_groups.id"), nullable=True)  # 允许为空，支持私人文献
    literature_id = Column(String(36), ForeignKey("literature.id"), nullable=False)
    
    # 会话信息
    session_title = Column(String(200))  # 会话标题（可选）
    start_time = Column(DateTime, default=datetime.now, nullable=False)
    last_activity = Column(DateTime, default=datetime.now, nullable=False)
    
    # 会话状态
    is_active = Column(Boolean, default=True, nullable=False)
    turn_count = Column(Integer, default=0, nullable=False)  # 对话轮次数
    
    # 会话统计
    total_questions = Column(Integer, default=0, nullable=False)
    total_answers = Column(Integer, default=0, nullable=False)
    avg_confidence = Column(Float, default=0.0, nullable=False)  # 平均置信度
    
    # 会话元数据
    session_metadata = Column(JSON)  # 存储额外的会话信息
    
    # 关联关系
    user = relationship("User", back_populates="qa_sessions")
    group = relationship("ResearchGroup", back_populates="qa_sessions")
    literature = relationship("Literature", back_populates="qa_sessions")
    conversation_turns = relationship("ConversationTurn", back_populates="session", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.session_metadata:
            self.session_metadata = {}
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
    
    def increment_turn_count(self):
        """增加对话轮次计数"""
        self.turn_count += 1
        self.update_activity()
    
    def add_question(self):
        """增加问题计数"""
        self.total_questions += 1
    
    def add_answer(self, confidence: float):
        """增加答案计数并更新平均置信度"""
        self.total_answers += 1
        # 计算新的平均置信度
        if self.total_answers == 1:
            self.avg_confidence = confidence
        else:
            self.avg_confidence = (self.avg_confidence * (self.total_answers - 1) + confidence) / self.total_answers
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "literature_id": self.literature_id,
            "session_title": self.session_title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "is_active": self.is_active,
            "turn_count": self.turn_count,
            "total_questions": self.total_questions,
            "total_answers": self.total_answers,
            "avg_confidence": round(self.avg_confidence, 2),
            "session_metadata": self.session_metadata or {}
        }


class ConversationTurn(BaseModel):
    """对话轮次模型"""
    __tablename__ = "conversation_turns"
    
    # 主键
    turn_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息
    session_id = Column(String(36), ForeignKey("qa_sessions.session_id"), nullable=False)
    
    # 轮次信息
    turn_index = Column(Integer, nullable=False)  # 在会话中的序号
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    
    # 用户问题
    question = Column(Text, nullable=False)
    question_metadata = Column(JSON)  # 问题相关元数据
    
    # AI回答
    answer = Column(Text)
    answer_metadata = Column(JSON)  # 答案相关元数据
    
    # 质量评估
    confidence = Column(Float, default=0.0)  # 置信度
    quality_scores = Column(JSON)  # 质量评分详情
    
    # 检索信息
    chunks_used = Column(Integer, default=0)  # 使用的文档块数量
    retrieval_metadata = Column(JSON)  # 检索相关元数据
    
    # 处理信息
    processing_time = Column(Float, default=0.0)  # 处理时间（秒）
    prompt_tokens = Column(Integer, default=0)  # 提示词token数
    
    # 用户反馈
    user_rating = Column(Integer)  # 用户评分 1-5
    user_feedback = Column(Text)  # 用户反馈文本
    
    # 状态信息
    is_successful = Column(Boolean, default=True)  # 是否成功回答
    error_type = Column(String(50))  # 错误类型（如果有）
    
    # 关联关系
    session = relationship("QASession", back_populates="conversation_turns")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.turn_id:
            self.turn_id = str(uuid.uuid4())
        if not self.question_metadata:
            self.question_metadata = {}
        if not self.answer_metadata:
            self.answer_metadata = {}
        if not self.quality_scores:
            self.quality_scores = {}
        if not self.retrieval_metadata:
            self.retrieval_metadata = {}
    
    def set_question(self, question: str, metadata: dict = None):
        """设置问题信息"""
        self.question = question
        if metadata:
            self.question_metadata.update(metadata)
    
    def set_answer(self, answer: str, confidence: float, quality_scores: dict = None, metadata: dict = None):
        """设置答案信息"""
        self.answer = answer
        self.confidence = confidence
        if quality_scores:
            self.quality_scores = quality_scores
        if metadata:
            self.answer_metadata.update(metadata)
        self.is_successful = True
    
    def set_retrieval_info(self, chunks_used: int, metadata: dict = None):
        """设置检索信息"""
        self.chunks_used = chunks_used
        if metadata:
            self.retrieval_metadata.update(metadata)
    
    def set_processing_info(self, processing_time: float, prompt_tokens: int):
        """设置处理信息"""
        self.processing_time = processing_time
        self.prompt_tokens = prompt_tokens
    
    def set_error(self, error_type: str, error_message: str = None):
        """设置错误信息"""
        self.is_successful = False
        self.error_type = error_type
        if error_message:
            self.answer = error_message
    
    def set_user_feedback(self, rating: int, feedback: str = None):
        """设置用户反馈"""
        if 1 <= rating <= 5:
            self.user_rating = rating
        if feedback:
            self.user_feedback = feedback
    
    def to_dict(self, include_full_content: bool = True):
        """转换为字典格式"""
        result = {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "confidence": round(self.confidence, 2),
            "quality_scores": self.quality_scores or {},
            "chunks_used": self.chunks_used,
            "processing_time": round(self.processing_time, 2),
            "prompt_tokens": self.prompt_tokens,
            "user_rating": self.user_rating,
            "is_successful": self.is_successful,
            "error_type": self.error_type
        }
        
        if include_full_content:
            result.update({
                "question": self.question,
                "answer": self.answer,
                "user_feedback": self.user_feedback,
                "question_metadata": self.question_metadata or {},
                "answer_metadata": self.answer_metadata or {},
                "retrieval_metadata": self.retrieval_metadata or {}
            })
        else:
            # 简化版本，只包含基本信息
            result.update({
                "question": self.question[:100] + "..." if self.question and len(self.question) > 100 else self.question,
                "answer": self.answer[:200] + "..." if self.answer and len(self.answer) > 200 else self.answer
            })
        
        return result
    
    def to_conversation_format(self):
        """转换为对话格式，用于RAG系统"""
        return [
            {
                "role": "user",
                "content": self.question,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None
            },
            {
                "role": "assistant", 
                "content": self.answer,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "confidence": self.confidence
            }
        ] if self.answer else [
            {
                "role": "user",
                "content": self.question,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None
            }
        ]


class ConversationSummary(BaseModel):
    """对话摘要模型"""
    __tablename__ = "conversation_summaries"
    
    # 主键
    summary_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息
    session_id = Column(String(36), ForeignKey("qa_sessions.session_id"), nullable=False)
    
    # 摘要信息
    summary_text = Column(Text, nullable=False)  # 摘要内容
    key_topics = Column(JSON)  # 关键话题列表
    important_entities = Column(JSON)  # 重要实体列表
    
    # 时间范围
    start_turn_index = Column(Integer, nullable=False)  # 起始轮次
    end_turn_index = Column(Integer, nullable=False)  # 结束轮次
    
    # 创建信息
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    summary_type = Column(String(20), default="auto", nullable=False)  # auto/manual
    
    # 质量信息
    compression_ratio = Column(Float)  # 压缩比例
    relevance_score = Column(Float)  # 相关性评分
    
    # 关联关系
    session = relationship("QASession")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.summary_id:
            self.summary_id = str(uuid.uuid4())
        if not self.key_topics:
            self.key_topics = []
        if not self.important_entities:
            self.important_entities = []
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "summary_id": self.summary_id,
            "session_id": self.session_id,
            "summary_text": self.summary_text,
            "key_topics": self.key_topics or [],
            "important_entities": self.important_entities or [],
            "start_turn_index": self.start_turn_index,
            "end_turn_index": self.end_turn_index,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "summary_type": self.summary_type,
            "compression_ratio": round(self.compression_ratio, 2) if self.compression_ratio else None,
            "relevance_score": round(self.relevance_score, 2) if self.relevance_score else None
        } 
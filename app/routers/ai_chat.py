"""
AI聊天路由

提供RAG问答系统的API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.literature import Literature
from app.models.research_group import ResearchGroup
from app.utils.rag_service import rag_service
from app.utils.conversation_manager import conversation_manager

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/ai", tags=["AI聊天"])

# Pydantic 模型定义
class QARequest(BaseModel):
    """问答请求模型"""
    question: str = Field(..., min_length=1, max_length=5000, description="用户问题")
    literature_id: str = Field(..., description="文献ID")
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
    max_sources: int = Field(default=5, ge=1, le=10, description="最大引用来源数量")
    include_history: bool = Field(default=True, description="是否包含对话历史")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('问题不能为空')
        return v.strip()

class SourceInfo(BaseModel):
    """引用来源信息模型"""
    id: str = Field(..., description="来源ID")
    text: str = Field(..., description="引用文本")
    similarity: float = Field(..., description="相似度分数")
    description: str = Field(..., description="来源描述")
    chunk_index: int = Field(..., description="文档块索引")

class QAResponse(BaseModel):
    """问答响应模型 - 支持新的格式化输出"""
    answer: str = Field(..., description="主要回答内容")
    key_findings: List[str] = Field(default=[], description="关键发现列表")
    limitations: str = Field(default="", description="局限性说明")
    sources: List[SourceInfo] = Field(..., description="引用来源列表")
    confidence: float = Field(..., description="置信度分数")
    session_id: str = Field(..., description="会话ID")
    turn_id: str = Field(..., description="轮次ID")
    metadata: Dict[str, Any] = Field(..., description="元数据信息")

class ConversationTurnInfo(BaseModel):
    """对话轮次信息模型"""
    turn_id: str
    turn_index: int
    timestamp: str
    question: str
    answer: Optional[str]
    confidence: float
    processing_time: float
    user_rating: Optional[int]

class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    session_title: str
    literature_id: str
    start_time: str
    last_activity: str
    turn_count: int
    total_questions: int
    total_answers: int
    avg_confidence: float
    is_active: bool

class UserFeedback(BaseModel):
    """用户反馈模型"""
    turn_id: str = Field(..., description="轮次ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    feedback: Optional[str] = Field(None, max_length=500, description="反馈文本")

@router.post("/ask", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    智能问答接口
    
    根据用户问题和指定文献，生成AI回答并提供引用来源
    """
    try:
        logger.info(f"用户 {current_user.id} 提问: {request.question[:50]}...")
        
        # 验证文献权限
        literature = db.query(Literature).filter(Literature.id == request.literature_id).first()
        if not literature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文献不存在"
            )
        
        # 检查用户是否有权限访问该文献
        if not _check_literature_access(current_user.id, literature, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该文献"
            )
        
        # 获取或创建会话
        session_id = conversation_manager.get_or_create_session(
            user_id=current_user.id,
            group_id=literature.research_group_id,
            literature_id=request.literature_id,
            session_id=request.session_id,
            db=db
        )
        
        # 获取对话历史（如果需要）
        conversation_history = []
        if request.include_history:
            conversation_history = conversation_manager.get_relevant_history(
                session_id=session_id,
                current_question=request.question,
                max_turns=5,
                db=db
            )
        
        # 调用RAG服务处理问题
        rag_result = await rag_service.process_question(
            question=request.question,
            literature_id=request.literature_id,
            group_id=literature.research_group_id,
            session_id=session_id,
            conversation_history=conversation_history,
            top_k=request.max_sources
        )
        
        # 记录对话轮次
        turn_id = conversation_manager.add_qa_turn(
            session_id=session_id,
            question=request.question,
            answer=rag_result["answer"],
            confidence=rag_result["confidence"],
            quality_scores=rag_result["quality_score"],
            chunks_used=rag_result["metadata"].get("chunks_retrieved", 0),
            processing_time=rag_result["metadata"].get("processing_time", 0),
            prompt_tokens=rag_result["metadata"].get("prompt_tokens", 0),
            metadata=rag_result["metadata"],
            db=db
        )
        
        # 构建响应
        sources = []
        for source in rag_result.get("sources", []):
            try:
                source_info = SourceInfo(
                    id=source.get("source_id", ""),
                    text=source.get("text", ""),
                    similarity=float(source.get("similarity", 0.0)),
                    description=source.get("description", ""),
                    chunk_index=int(source.get("chunk_index", 0))
                )
                sources.append(source_info)
            except (ValueError, TypeError) as e:
                logger.warning(f"构建source信息失败: {e}")
                continue
        
        # 确保所有数值字段都有有效值
        confidence = float(rag_result.get("confidence", 0.0))
        processing_time = float(rag_result.get("metadata", {}).get("processing_time", 0.0))
        
        response = QAResponse(
            answer=rag_result.get("answer", "抱歉，无法生成答案"),
            key_findings=rag_result.get("key_findings", []),
            limitations=rag_result.get("limitations", ""),
            sources=sources,
            confidence=confidence,
            session_id=session_id,
            turn_id=turn_id,
            metadata={
                **rag_result.get("metadata", {}),
                "processing_time": processing_time,
                "confidence": confidence
            }
        )
        
        logger.info(f"问答完成，会话: {session_id}, 轮次: {turn_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"问答处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="问答处理失败，请重试"
        )

@router.get("/preset-questions/{literature_id}")
async def get_preset_questions(
    literature_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取文献的预设问题列表
    """
    try:
        # 验证文献权限
        literature = db.query(Literature).filter(Literature.id == literature_id).first()
        if not literature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文献不存在"
            )
        
        if not _check_literature_access(current_user.id, literature, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该文献"
            )
        
        # 获取预设问题
        preset_questions = rag_service.get_preset_questions(
            literature_id=literature_id,
            literature_title=literature.title
        )
        
        return {
            "literature_id": literature_id,
            "literature_title": literature.title,
            "questions": preset_questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预设问题失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取预设问题失败"
        )

@router.get("/sessions")
async def get_user_sessions(
    literature_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取用户的对话会话列表
    """
    try:
        from app.models.conversation import QASession
        from sqlalchemy import desc, and_
        
        # 构建查询条件
        conditions = [QASession.user_id == current_user.id]
        if literature_id:
            conditions.append(QASession.literature_id == literature_id)
        
        # 查询会话
        query = db.query(QASession).filter(and_(*conditions))
        total = query.count()
        
        sessions = query.order_by(desc(QASession.last_activity)).offset(offset).limit(limit).all()
        
        # 转换为响应格式
        session_list = []
        for session in sessions:
            session_info = SessionInfo(
                session_id=session.session_id,
                session_title=session.session_title or "未命名会话",
                literature_id=session.literature_id,
                start_time=session.start_time.isoformat(),
                last_activity=session.last_activity.isoformat(),
                turn_count=session.turn_count,
                total_questions=session.total_questions,
                total_answers=session.total_answers,
                avg_confidence=session.avg_confidence,
                is_active=session.is_active
            )
            session_list.append(session_info)
        
        return {
            "sessions": session_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )

@router.get("/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    include_full_content: bool = True,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定会话的对话历史
    """
    try:
        from app.models.conversation import QASession, ConversationTurn
        from sqlalchemy import and_, desc
        
        # 验证会话所有权
        session = db.query(QASession).filter(
            and_(
                QASession.session_id == session_id,
                QASession.user_id == current_user.id
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        # 获取对话轮次
        turns_query = db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id
        ).order_by(ConversationTurn.turn_index)
        
        if limit > 0:
            turns_query = turns_query.limit(limit)
        
        turns = turns_query.all()
        
        # 转换为响应格式
        conversation_turns = []
        for turn in turns:
            turn_info = ConversationTurnInfo(
                turn_id=turn.turn_id,
                turn_index=turn.turn_index,
                timestamp=turn.timestamp.isoformat(),
                question=turn.question,
                answer=turn.answer,
                confidence=turn.confidence,
                processing_time=turn.processing_time,
                user_rating=turn.user_rating
            )
            conversation_turns.append(turn_info)
        
        # 会话信息
        session_info = SessionInfo(
            session_id=session.session_id,
            session_title=session.session_title or "未命名会话",
            literature_id=session.literature_id,
            start_time=session.start_time.isoformat(),
            last_activity=session.last_activity.isoformat(),
            turn_count=session.turn_count,
            total_questions=session.total_questions,
            total_answers=session.total_answers,
            avg_confidence=session.avg_confidence,
            is_active=session.is_active
        )
        
        return {
            "session": session_info,
            "turns": conversation_turns,
            "total_turns": len(turns)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取对话历史失败"
        )

@router.delete("/conversation/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    删除指定的对话会话
    """
    try:
        success = conversation_manager.delete_session(
            session_id=session_id,
            user_id=current_user.id,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或无权限删除"
            )
        
        return {"message": "会话删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败"
        )

@router.post("/feedback")
async def submit_feedback(
    feedback: UserFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    提交用户对AI回答的反馈
    """
    try:
        from app.models.conversation import ConversationTurn
        from sqlalchemy import and_
        
        # 验证轮次存在且属于当前用户
        turn = db.query(ConversationTurn).join(
            "session"  # 通过外键关系连接到QASession表
        ).filter(
            and_(
                ConversationTurn.turn_id == feedback.turn_id,
                ConversationTurn.session.has(user_id=current_user.id)
            )
        ).first()
        
        if not turn:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话轮次不存在"
            )
        
        # 更新评分和反馈
        turn.user_rating = feedback.rating
        turn.user_feedback = feedback.feedback
        turn.feedback_time = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"用户 {current_user.id} 提交反馈，轮次: {feedback.turn_id}, 评分: {feedback.rating}")
        
        # 异步发送反馈到模型提供商（如果需要）
        
        return {
            "message": "反馈提交成功",
            "turn_id": feedback.turn_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交反馈失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提交反馈失败"
        )

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    AI服务健康检查
    """
    try:
        health_status = await rag_service.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/stats")
async def get_service_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取AI服务统计信息（需要登录）
    """
    try:
        stats = rag_service.get_service_stats()
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )

@router.get("/sessions/literature/{literature_id}")
async def get_sessions_by_literature(
    literature_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取指定文献的对话会话列表
    """
    try:
        from app.models.conversation import QASession
        from sqlalchemy import desc, and_
        
        # 验证文献权限
        literature = db.query(Literature).filter(Literature.id == literature_id).first()
        if not literature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文献不存在"
            )
        
        if not _check_literature_access(current_user.id, literature, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该文献"
            )
        
        # 查询会话
        query = db.query(QASession).filter(
            and_(
                QASession.user_id == current_user.id,
                QASession.literature_id == literature_id
            )
        )
        total = query.count()
        
        sessions = query.order_by(desc(QASession.last_activity)).offset(offset).limit(limit).all()
        
        # 转换为响应格式
        session_list = []
        for session in sessions:
            session_info = SessionInfo(
                session_id=session.session_id,
                session_title=session.session_title or "未命名会话",
                literature_id=session.literature_id,
                start_time=session.start_time.isoformat(),
                last_activity=session.last_activity.isoformat(),
                turn_count=session.turn_count,
                total_questions=session.total_questions,
                total_answers=session.total_answers,
                avg_confidence=session.avg_confidence,
                is_active=session.is_active
            )
            session_list.append(session_info)
        
        return {
            "sessions": session_list,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文献会话列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文献会话列表失败"
        )

@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    删除指定的对话会话
    """
    try:
        success = conversation_manager.delete_session(
            session_id=session_id,
            user_id=current_user.id,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或已被删除"
            )
        
        logger.info(f"用户 {current_user.id} 删除会话: {session_id}")
        
        return {"message": "会话已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败"
        )

# 辅助函数
def _check_literature_access(user_id: str, literature: Literature, db: Session) -> bool:
    """
    检查用户是否有权限访问指定文献
    """
    try:
        # 如果是私人文献（group_id为None），只需验证文献是否属于该用户
        if literature.research_group_id is None:
            # 对于私人文献，直接检查上传者是否为当前用户
            return literature.uploaded_by == user_id
        
        # 对于课题组文献，检查用户是否是课题组成员
        from app.models.research_group import UserResearchGroup
        from sqlalchemy import and_
        
        member = db.query(UserResearchGroup).filter(
            and_(
                UserResearchGroup.user_id == user_id,
                UserResearchGroup.group_id == literature.research_group_id
            )
        ).first()
        
        return member is not None
        
    except Exception as e:
        logger.error(f"检查文献权限失败: {str(e)}")
        return False 
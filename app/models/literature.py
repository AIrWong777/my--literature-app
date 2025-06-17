# 导入需要的库
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# 从research_group.py导入Base
from .research_group import Base

# 定义Literature模型
class Literature(Base):
    __tablename__ = 'literature'
    
    # 定义列（字段）
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)  # 文献标题
    filename = Column(String, nullable=False)  # 原始文件名
    file_path = Column(String, nullable=False)  # 存储路径
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_type = Column(String, nullable=False)  # 文件类型：pdf/docx/html
    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False)  # 上传时间
    uploaded_by = Column(String, ForeignKey('users.id'), nullable=False)  # 上传用户ID
    research_group_id = Column(String, ForeignKey('research_groups.id'), nullable=True)  # 所属研究组ID，允许为空支持私人文献
    status = Column(String, default='active', nullable=False)  # 状态：active/deleted
    
    # 软删除相关字段
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    deleted_by = Column(String, ForeignKey('users.id'), nullable=True)  # 删除者ID
    delete_reason = Column(Text, nullable=True)  # 删除原因
    restored_at = Column(DateTime, nullable=True)  # 恢复时间
    restored_by = Column(String, ForeignKey('users.id'), nullable=True)  # 恢复者ID
    
    # 定义关系 - 明确指定外键以避免歧义
    uploader = relationship("User", foreign_keys=[uploaded_by], back_populates="uploaded_literature")
    deleter = relationship("User", foreign_keys=[deleted_by])
    restorer = relationship("User", foreign_keys=[restored_by])
    research_group = relationship("ResearchGroup", back_populates="literature")
    # 与问答会话的一对多关系
    qa_sessions = relationship("QASession", back_populates="literature")
    
    def __init__(self, title, filename, file_path, file_size, file_type, uploaded_by, research_group_id=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.uploaded_by = uploaded_by
        self.research_group_id = research_group_id  # 可以为None表示私人文献
        self.upload_time = datetime.utcnow()
        self.status = 'active'
        # 软删除字段初始化为None
        self.deleted_at = None
        self.deleted_by = None
        self.delete_reason = None
        self.restored_at = None
        self.restored_by = None
    
    def __repr__(self):
        return f"<Literature(title='{self.title}', filename='{self.filename}', type='{self.file_type}', status='{self.status}')>"
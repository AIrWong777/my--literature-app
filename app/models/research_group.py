# 导入需要的库
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

# 创建Base类 - 所有模型的基类
Base = declarative_base()

# 定义ResearchGroup模型
class ResearchGroup(Base):
    __tablename__ = 'research_groups'
    
    # 定义列（字段）
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    institution = Column(String)
    description = Column(String)
    research_area = Column(String)
    invitation_code = Column(String, unique=True)  # 随机生成，唯一
    
    # 定义关系
    users = relationship("User", secondary="user_research_groups", back_populates="research_groups")
    # 与文献的一对多关系（研究组的文献）
    literature = relationship("Literature", back_populates="research_group")
    # 与问答会话的一对多关系
    qa_sessions = relationship("QASession", back_populates="group")
    
    def __init__(self, name, institution, description, research_area):
        self.id = str(uuid.uuid4())
        self.name = name
        self.institution = institution
        self.description = description
        self.research_area = research_area
        self.invitation_code = self._generate_invitation_code()
        
    def _generate_invitation_code(self):
        """生成唯一的邀请码"""
        return str(uuid.uuid4())[:8]
    
    def __repr__(self):
        return f"<ResearchGroup(name='{self.name}', institution='{self.institution}')>"


# 定义UserResearchGroup关联表
class UserResearchGroup(Base):
    __tablename__ = 'user_research_groups'
    
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    group_id = Column(String, ForeignKey('research_groups.id'), primary_key=True)
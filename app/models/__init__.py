# 导入所有模型，确保SQLAlchemy能够发现它们
from .base import BaseModel
from .user import User
from .research_group import ResearchGroup, UserResearchGroup
from .literature import Literature
from .conversation import QASession, ConversationTurn, ConversationSummary

# 导出所有模型
__all__ = ['BaseModel', 'User', 'ResearchGroup', 'UserResearchGroup', 'Literature', 
           'QASession', 'ConversationTurn', 'ConversationSummary']
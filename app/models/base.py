"""
基础数据模型

提供所有模型的基类
"""
from sqlalchemy.ext.declarative import declarative_base

# 从research_group.py导入Base，确保所有模型共享同一个Base
from .research_group import Base

class BaseModel(Base):
    """所有模型的基类"""
    __abstract__ = True  # 标记为抽象类，不会创建表
    
    def to_dict(self):
        """将模型实例转换为字典"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def update_from_dict(self, data):
        """从字典更新模型实例"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self 
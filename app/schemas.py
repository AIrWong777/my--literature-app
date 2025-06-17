# app/schemas.py
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List
from datetime import datetime

# 用户注册模型 - 支持手机号注册
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    phone_number: str = Field(..., pattern=r"^\d{11}$")
    password: str = Field(..., min_length=8)
    password_confirm: str

    # 密码一致性验证
    @root_validator(pre=True)
    def check_passwords_match(cls, values):
        password = values.get('password')
        password_confirm = values.get('password_confirm')
        
        if password != password_confirm:
            raise ValueError("两次输入密码不一致")
        return values

# 用户登录模型 - 支持手机号登录
class UserLogin(BaseModel):
    phone_number: str
    password: str

# 用户响应模型（不返回密码）
class UserOut(BaseModel):
    id: str
    username: str
    phone_number: str

    class Config:
        orm_mode = True

# 用户信息模型
class UserInfo(BaseModel):
    id: str
    username: str
    phone_number: str

# Token 模型
class Token(BaseModel):
    access_token: str
    token_type: str

# 带刷新令牌的Token模型
class TokenWithRefresh(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    sub: Optional[str] = None

# 创建课题组请求模型
class GroupCreate(BaseModel):
    name: str
    institution: str
    description: Optional[str] = None
    research_area: Optional[str] = None

# 创建课题组响应模型
class GroupCreateResponse(BaseModel):
    id: str
    invitation_code: str

# 加入课题组请求模型
class GroupJoin(BaseModel):
    group_id: str
    invitation_code: str

# 通用消息响应模型
class Message(BaseModel):
    detail: str

# ===== 文献相关模型 =====

# 文献创建请求模型（用于API接口）
class LiteratureCreate(BaseModel):
    title: Optional[str] = Field(None, description="文献标题，如果为空则从文件中提取")
    research_group_id: str = Field(..., description="所属研究组ID")

# 文献响应模型（返回给客户端）
class LiteratureResponse(BaseModel):
    id: str
    title: str
    filename: str
    file_size: int
    file_type: str
    upload_time: datetime
    uploaded_by: str
    research_group_id: str
    status: str

    class Config:
        orm_mode = True

# 文献列表项模型（用于列表显示）
class LiteratureListItem(BaseModel):
    id: str
    title: str
    filename: str
    file_size: int
    file_type: str
    upload_time: datetime
    uploader_name: str  # 上传者用户名

    class Config:
        orm_mode = True

# 文献列表响应模型
class LiteratureListResponse(BaseModel):
    total: int
    literature: List[LiteratureListItem]

# 文件上传响应模型
class FileUploadResponse(BaseModel):
    message: str
    literature_id: str
    title: str
    filename: str
    file_size: int
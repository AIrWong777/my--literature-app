"""
用户认证模块

提供JWT令牌认证、密码验证等功能
"""
import warnings
# 抑制bcrypt版本警告
warnings.filterwarnings("ignore", message=".*bcrypt.*", category=UserWarning)

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app import schemas

# 配置日志
logger = logging.getLogger(__name__)

# 安全配置
SECRET_KEY = "aicodecode"  # 与main.py保持一致
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # Token 有效期设置为30天 (30 * 24 * 60 = 43200分钟)
REFRESH_TOKEN_EXPIRE_DAYS = 90  # 刷新令牌有效期延长到90天

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# 路由前缀
router = APIRouter()

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 生成密码哈希
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 校验用户身份（兼容原有用户名登录）
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# 校验用户身份（手机号登录）
def authenticate_user_by_phone(db: Session, phone_number: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# 生成访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 生成刷新令牌
def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 登录接口（保持原有接口兼容性）
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 依赖：获取当前用户
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            logger.warning("Token payload缺少sub字段")
            raise credentials_exception
        
        logger.debug(f"解析token成功，sub: {sub}")
            
    except JWTError as e:
        logger.warning(f"JWT解析失败: {e}")
        raise credentials_exception
    
    # 尝试通过用户ID查找用户（原有系统）
    user = db.query(User).filter(User.id == sub).first()
    if user:
        logger.debug(f"通过ID找到用户: {user.username}")
        return user
    
    # 如果通过ID找不到，尝试通过手机号查找（新系统）
    user = db.query(User).filter(User.phone_number == sub).first()
    if user is None:
        logger.warning(f"未找到用户，sub: {sub}")
        raise credentials_exception
    
    logger.debug(f"通过手机号找到用户: {user.username}")
    return user

import sys
import logging
import asyncio
import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.research_group import ResearchGroup, UserResearchGroup
from app.models.literature import Literature
from app.auth import verify_password, get_current_user, create_access_token, authenticate_user_by_phone, create_refresh_token, get_password_hash
from app.utils.auth_helper import require_group_membership, verify_group_membership, get_correct_file_path
from app.utils.file_handler import validate_upload_file, generate_file_path, save_uploaded_file, get_file_info
from app.utils.text_extractor import extract_metadata_from_file
from app.utils.error_handler import (
    log_error, log_success, handle_file_upload_error, handle_permission_error,
    validate_file_upload, safe_file_operation, FileUploadError, PermissionError, ValidationError
)
from app.schemas import FileUploadResponse, LiteratureListResponse, LiteratureListItem, UserCreate, UserLogin, TokenWithRefresh, UserInfo, Token
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.responses import FileResponse, JSONResponse
from app.utils.auth_helper import verify_literature_access, get_literature_with_permission, verify_file_exists, get_content_type
from app.routers import ai_chat

# 配置日志
# 设置环境变量强制使用UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志处理器
def setup_logging():
    """设置日志配置"""
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置文件处理器（使用UTF-8编码）
    file_handler = logging.FileHandler(
        'literature_system.log', 
        mode='a', 
        encoding='utf-8',
        errors='ignore'  # 忽略编码错误
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # 清除现有处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 防止重复日志
    root_logger.propagate = False

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(title="文献管理系统", description="AI驱动的协作文献管理平台", version="1.0.0")

# 添加CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ai_chat.router)

# 导入缓存管理路由
from app.routers import cache_admin
app.include_router(cache_admin.router)

# JWT 配置
SECRET_KEY = "aicodecode"  # 替换为随机字符串，例如 "mysecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # Token 有效期设置为30天 (30 * 24 * 60 = 43200分钟)
REFRESH_TOKEN_EXPIRE_DAYS = 90  # 刷新令牌有效期延长到90天

@app.get("/")
def read_root():
    """根路径 - 返回API基本信息"""
    return {
        "message": "欢迎使用文献管理系统API",
        "version": "1.0.0",
        "status": "运行中",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"用户登录尝试: {form_data.username}")
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        log_error("user_login", Exception("登录失败"), user_id=None, extra_info={"username": form_data.username})
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
    
    log_success("user_login", user.id, {"username": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/groups/create")
def create_group(name: str, institution: str, description: str, research_area: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # 只传4个参数，模型内部自己生成 invitation_code
        group = ResearchGroup(
            name=name,
            institution=institution,
            description=description,
            research_area=research_area,
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        membership = UserResearchGroup(user_id=current_user.id, group_id=group.id)
        db.add(membership)
        db.commit()
        
        log_success("group_create", current_user.id, {
            "group_id": group.id,
            "group_name": name,
            "institution": institution
        })
        
        return {"group_id": group.id, "invitation_code": group.invitation_code}
        
    except Exception as e:
        log_error("group_create", e, current_user.id, {"group_name": name})
        raise HTTPException(status_code=500, detail="创建研究组失败")

@app.get("/groups/info/{invitation_code}")
def get_group_by_invitation_code(invitation_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    根据邀请码获取课题组信息
    """
    try:
        group = db.query(ResearchGroup).filter(ResearchGroup.invitation_code == invitation_code).first()
        if not group:
            raise HTTPException(status_code=404, detail="无效的邀请码")
        
        return {
            "id": group.id,
            "name": group.name,
            "institution": group.institution,
            "description": group.description,
            "research_area": group.research_area
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error("group_info", e, current_user.id, {"invitation_code": invitation_code})
        raise HTTPException(status_code=500, detail="获取课题组信息失败")

@app.post("/groups/join-by-code")
def join_group_by_code(invitation_code: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    通过邀请码直接加入课题组
    """
    try:
        group = db.query(ResearchGroup).filter(ResearchGroup.invitation_code == invitation_code).first()
        if not group:
            log_error("group_join_by_code", Exception("无效的邀请码"), current_user.id, {
                "provided_code": invitation_code
            })
            raise HTTPException(status_code=400, detail="无效的邀请码")
        
        existing = db.query(UserResearchGroup).filter(
            UserResearchGroup.user_id == current_user.id,
            UserResearchGroup.group_id == group.id
        ).first()
        if existing:
            log_error("group_join_by_code", Exception("用户已加入该课题组"), current_user.id, {"group_id": group.id})
            raise HTTPException(status_code=400, detail="用户已加入该课题组")
        
        membership = UserResearchGroup(user_id=current_user.id, group_id=group.id)
        db.add(membership)
        db.commit()
        
        log_success("group_join_by_code", current_user.id, {
            "group_id": group.id,
            "group_name": group.name
        })
        
        return {
            "message": "成功加入课题组",
            "group": {
                "id": group.id,
                "name": group.name,
                "institution": group.institution
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("group_join_by_code", e, current_user.id, {"invitation_code": invitation_code})
        raise HTTPException(status_code=500, detail="加入研究组失败")

@app.post("/groups/join")
def join_group(group_id: str, invitation_code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        group = db.query(ResearchGroup).filter(ResearchGroup.id == group_id).first()
        if not group or group.invitation_code != invitation_code:
            log_error("group_join", Exception("无效的课题组ID或邀请码"), current_user.id, {
                "group_id": group_id,
                "provided_code": invitation_code
            })
            raise HTTPException(status_code=400, detail="无效的课题组ID或邀请码")
        
        existing = db.query(UserResearchGroup).filter(
            UserResearchGroup.user_id == current_user.id,
            UserResearchGroup.group_id == group_id
        ).first()
        if existing:
            log_error("group_join", Exception("用户已加入该课题组"), current_user.id, {"group_id": group_id})
            raise HTTPException(status_code=400, detail="用户已加入该课题组")
        
        membership = UserResearchGroup(user_id=current_user.id, group_id=group_id)
        db.add(membership)
        db.commit()
        
        log_success("group_join", current_user.id, {
            "group_id": group_id,
            "group_name": group.name
        })
        
        return {"message": "成功加入课题组"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("group_join", e, current_user.id, {"group_id": group_id})
        raise HTTPException(status_code=500, detail="加入研究组失败")

# ===== 文献管理接口 =====

@app.post("/literature/upload", response_model=FileUploadResponse)
async def upload_literature(
    file: UploadFile = File(...),
    group_id: str = Form(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文献到指定研究组 - 增强版错误处理
    """
    operation_info = {
        "filename": file.filename,
        "group_id": group_id,
        "file_size": None
    }
    
    try:
        # 1. 基础验证
        validate_file_upload(file, group_id, current_user.id)
        
        # 2. 验证用户是否为指定研究组成员
        try:
            require_group_membership(current_user.id, group_id, db)
        except HTTPException as e:
            raise PermissionError(e.detail)
        
        # 3. 验证文件
        is_valid, error_msg = validate_upload_file(file)
        if not is_valid:
            logger.warning(f"文件验证失败: {error_msg}")
            raise ValidationError(error_msg)
        
        # 4. 获取文件信息
        file_info = get_file_info(file)
        operation_info["file_size"] = file_info["file_size"]
        
        # 5. 生成存储路径
        full_path, relative_path = generate_file_path(group_id, file.filename)
        
        # 6. 安全保存文件到磁盘
        save_success = await save_uploaded_file(file, full_path)
        if not save_success:
            raise FileUploadError("文件保存失败")
        
        # 获取文件实际大小
        file_info["file_size"] = os.path.getsize(full_path)
        
        # 7. 提取元数据
        final_title = title if title else file.filename
        try:
            metadata = extract_metadata_from_file(full_path, file.filename)
            if not title and metadata.get("title"):
                final_title = metadata.get("title")
        except Exception as e:
            logger.warning(f"元数据提取失败，使用默认标题: {e}")
        
        # 8. 创建数据库记录
        try:
            literature = Literature(
                title=final_title,
                filename=file.filename,
                file_path=relative_path,
                file_size=file_info["file_size"],
                file_type=file_info["file_type"],
                uploaded_by=current_user.id,
                research_group_id=group_id
            )
            
            db.add(literature)
            db.commit()
            db.refresh(literature)
            
        except Exception as e:
            # 如果数据库操作失败，尝试删除已保存的文件
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except:
                pass
            raise e
        
        # 9. 记录成功日志
        log_success("literature_upload", current_user.id, {
            "literature_id": literature.id,
            "title": final_title,
            "filename": file.filename,
            "file_size": file_info["file_size"],
            "group_id": group_id
        })
        
        # 10. 返回上传结果
        return FileUploadResponse(
            message="文献上传成功",
            literature_id=literature.id,
            title=final_title,
            filename=file.filename,
            file_size=file_info["file_size"]
        )
        
    except (ValidationError, PermissionError, FileUploadError) as e:
        # 处理已知的业务异常
        raise handle_file_upload_error(e, file.filename, current_user.id)
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    
    except Exception as e:
        # 处理未知异常
        log_error("literature_upload", e, current_user.id, operation_info)
        raise handle_file_upload_error(e, file.filename, current_user.id)

@app.post("/literature/upload/private", response_model=FileUploadResponse)
async def upload_private_literature(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文献到个人库
    """
    operation_info = {
        "filename": file.filename,
        "user_id": current_user.id,
        "file_size": None
    }
    
    try:
        # 1. 验证文件
        is_valid, error_msg = validate_upload_file(file)
        if not is_valid:
            logger.warning(f"文件验证失败: {error_msg}")
            raise ValidationError(error_msg)
        
        # 2. 获取文件信息
        file_info = get_file_info(file)
        operation_info["file_size"] = file_info["file_size"]
        
        # 3. 生成存储路径（使用用户ID作为目录）
        full_path, relative_path = generate_file_path(f"private_{current_user.id}", file.filename)
        
        # 4. 安全保存文件到磁盘
        save_success = await save_uploaded_file(file, full_path)
        if not save_success:
            raise FileUploadError("文件保存失败")
        
        # 获取文件实际大小
        file_info["file_size"] = os.path.getsize(full_path)
        
        # 5. 提取元数据
        final_title = title if title else file.filename
        try:
            metadata = extract_metadata_from_file(full_path, file.filename)
            if not title and metadata.get("title"):
                final_title = metadata.get("title")
        except Exception as e:
            logger.warning(f"元数据提取失败，使用默认标题: {e}")
        
        # 6. 创建数据库记录（research_group_id 设为 None 表示私人文献）
        try:
            # 临时修改Literature模型的创建方式来支持私人文献
            literature = Literature(
                title=final_title,
                filename=file.filename,
                file_path=relative_path,
                file_size=file_info["file_size"],
                file_type=file_info["file_type"],
                uploaded_by=current_user.id,
                research_group_id=None  # 私人文献不属于任何课题组
            )
            
            db.add(literature)
            db.commit()
            db.refresh(literature)
            
        except Exception as e:
            # 如果数据库操作失败，尝试删除已保存的文件
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except:
                pass
            raise e
        
        # 7. 记录成功日志
        log_success("private_literature_upload", current_user.id, {
            "literature_id": literature.id,
            "title": final_title,
            "filename": file.filename,
            "file_size": file_info["file_size"]
        })
        
        # 8. 启动异步向量生成（私人文献）
        try:
            from app.utils.async_processor import async_processor
            task_id = async_processor.process_literature_async(literature.id)
            logger.info(f"私人文献 {literature.id} 异步向量生成已启动，任务ID: {task_id}")
        except Exception as e:
            logger.warning(f"私人文献向量生成启动失败，但不影响上传: {e}")
        
        # 9. 返回上传结果
        return FileUploadResponse(
            message="文献上传成功，正在后台生成AI向量",
            literature_id=literature.id,
            title=final_title,
            filename=file.filename,
            file_size=file_info["file_size"]
        )
        
    except (ValidationError, PermissionError, FileUploadError) as e:
        # 处理已知的业务异常
        raise handle_file_upload_error(e, file.filename, current_user.id)
    
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    
    except Exception as e:
        # 处理未知异常
        log_error("private_literature_upload", e, current_user.id, operation_info)
        raise handle_file_upload_error(e, file.filename, current_user.id)

@app.get("/literature/public/{group_id}", response_model=LiteratureListResponse)
def get_group_literature(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定研究组的公共文献列表 - 增强版错误处理
    """
    try:
        # 1. 验证用户是否为指定研究组成员
        try:
            require_group_membership(current_user.id, group_id, db)
        except HTTPException as e:
            raise handle_permission_error(Exception(e.detail), "literature_list", current_user.id)
        
        # 2. 查询该研究组的所有活跃文献
        literature_query = db.query(Literature, User).join(
            User, Literature.uploaded_by == User.id
        ).filter(
            Literature.research_group_id == group_id,
            Literature.status == 'active'
        ).order_by(Literature.upload_time.desc())
        
        literature_records = literature_query.all()
        
        # 3. 构建响应数据
        literature_list = []
        for lit, uploader in literature_records:
            literature_list.append(LiteratureListItem(
                id=lit.id,
                title=lit.title,
                filename=lit.filename,
                file_size=lit.file_size,
                file_type=lit.file_type,
                upload_time=lit.upload_time,
                uploader_name=uploader.username
            ))
        
        log_success("literature_list", current_user.id, {
            "group_id": group_id,
            "literature_count": len(literature_list)
        })
        
        return LiteratureListResponse(
            total=len(literature_list),
            literature=literature_list
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        log_error("literature_list", e, current_user.id, {"group_id": group_id})
        raise HTTPException(status_code=500, detail="获取文献列表失败")

@app.get("/literature/private", response_model=LiteratureListResponse)
def get_private_literature(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的私人文献列表
    """
    try:
        # 1. 查询该用户的所有私人文献（research_group_id 为 None）
        literature_query = db.query(Literature, User).join(
            User, Literature.uploaded_by == User.id
        ).filter(
            Literature.uploaded_by == current_user.id,
            Literature.research_group_id.is_(None),
            Literature.status == 'active'
        ).order_by(Literature.upload_time.desc())
        
        literature_records = literature_query.all()
        
        # 2. 构建响应数据
        literature_list = []
        for lit, uploader in literature_records:
            literature_list.append(LiteratureListItem(
                id=lit.id,
                title=lit.title,
                filename=lit.filename,
                file_size=lit.file_size,
                file_type=lit.file_type,
                upload_time=lit.upload_time,
                uploader_name=uploader.username
            ))
        
        log_success("private_literature_list", current_user.id, {
            "literature_count": len(literature_list)
        })
        
        return LiteratureListResponse(
            total=len(literature_list),
            literature=literature_list
        )
        
    except Exception as e:
        log_error("private_literature_list", e, current_user.id)
        raise HTTPException(status_code=500, detail="获取私人文献列表失败")

@app.get("/user/groups")
def get_user_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户所属的研究组列表
    """
    try:
        # 查询用户所属的研究组
        groups = db.query(ResearchGroup).join(
            UserResearchGroup, ResearchGroup.id == UserResearchGroup.group_id
        ).filter(UserResearchGroup.user_id == current_user.id).all()
        
        group_list = []
        for group in groups:
            group_list.append({
                "id": group.id,
                "name": group.name,
                "institution": group.institution,
                "description": group.description,
                "research_area": group.research_area
            })
        
        log_success("user_groups", current_user.id, {"group_count": len(group_list)})
        
        return {
            "total": len(group_list),
            "groups": group_list
        }
        
    except Exception as e:
        log_error("user_groups", e, current_user.id)
        raise HTTPException(status_code=500, detail="获取研究组列表失败")
    
# 添加软删除文献接口
@app.delete("/literature/{literature_id}")
async def delete_literature(
    literature_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """软删除文献"""
    try:
        from app.utils.literature_manager import soft_delete_literature
        
        success = soft_delete_literature(literature_id, current_user.id, db, reason)
        
        if success:
            logger.info(f"文献删除成功: {literature_id} by {current_user.username}")
            return {"message": "文献删除成功", "literature_id": literature_id}
        else:
            raise HTTPException(status_code=404, detail="文献不存在或无权删除")
            
    except Exception as e:
        logger.error(f"删除文献失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除文献失败: {str(e)}")

# 恢复已删除文献接口
@app.post("/literature/{literature_id}/restore")
async def restore_literature(
    literature_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """恢复已删除的文献"""
    try:
        from app.utils.literature_manager import restore_literature
        
        success = restore_literature(literature_id, current_user.id, db)
        
        if success:
            logger.info(f"文献恢复成功: {literature_id} by {current_user.username}")
            return {"message": "文献恢复成功", "literature_id": literature_id}
        else:
            raise HTTPException(status_code=404, detail="文献不存在或无权恢复")
            
    except Exception as e:
        logger.error(f"恢复文献失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复文献失败: {str(e)}")

# 获取已删除文献列表接口
@app.get("/literature/deleted/{group_id}")
async def get_deleted_literature(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取研究组的已删除文献列表"""
    try:
        from app.utils.literature_manager import get_deleted_literature
        
        deleted_list = get_deleted_literature(group_id, current_user.id, db)
        
        logger.info(f"获取删除文献列表: group={group_id}, count={len(deleted_list)}")
        return {
            "group_id": group_id,
            "deleted_literature": deleted_list,
            "count": len(deleted_list)
        }
        
    except Exception as e:
        logger.error(f"获取删除文献列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取删除文献列表失败: {str(e)}")

# 获取文献统计信息接口
@app.get("/literature/stats/{group_id}")
async def get_literature_statistics(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取研究组文献统计信息"""
    try:
        from app.utils.literature_manager import get_literature_stats
        from app.utils.auth_helper import verify_group_membership
        
        # 验证用户是否为研究组成员
        if not verify_group_membership(current_user.id, group_id, db):
            raise HTTPException(status_code=403, detail="无权查看该研究组统计信息")
        
        stats = get_literature_stats(group_id, db)
        
        logger.info(f"获取文献统计: group={group_id}, active={stats['active_count']}")
        return {
            "group_id": group_id,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文献统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文献统计失败: {str(e)}")

# 获取存储统计信息接口
@app.get("/admin/storage/stats")
async def get_storage_statistics(
    current_user: User = Depends(get_current_user)
):
    """获取存储统计信息（管理员功能）"""
    try:
        from app.utils.storage_manager import get_storage_stats, validate_storage
        
        # 简单的管理员验证（实际项目中应该有更严格的权限控制）
        # 这里暂时允许所有登录用户查看
        
        storage_stats = get_storage_stats()
        storage_health = validate_storage()
        
        logger.info(f"获取存储统计: groups={storage_stats['total_groups']}, files={storage_stats['total_files']}")
        return {
            "storage_statistics": storage_stats,
            "storage_health": storage_health
        }
        
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")

# 清理存储接口
@app.post("/admin/storage/cleanup")
async def cleanup_storage(
    current_user: User = Depends(get_current_user)
):
    """清理存储（删除空目录）"""
    try:
        from app.utils.storage_manager import cleanup_storage
        
        cleaned_dirs = cleanup_storage()
        
        logger.info(f"存储清理完成: 清理了 {len(cleaned_dirs)} 个空目录")
        return {
            "message": "存储清理完成",
            "cleaned_directories": cleaned_dirs,
            "count": len(cleaned_dirs)
        }
        
    except Exception as e:
        logger.error(f"存储清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"存储清理失败: {str(e)}")
    
@app.get("/literature/view/file/{literature_id}")
@app.head("/literature/view/file/{literature_id}")
async def view_literature_file(
    literature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    在线查看文献文件
    """
    try:
        # 1. 验证文献权限
        literature = get_literature_with_permission(literature_id, current_user.id, db)
        
        # 2. 验证文件存在
        file_path = get_correct_file_path(literature.file_path)
        if not verify_file_exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 3. 获取文件MIME类型
        content_type = get_content_type(file_path)
        
        # 4. 使用经过编码处理的文件名
        from app.utils.file_handler import get_safe_filename_for_headers
        safe_filename = get_safe_filename_for_headers(literature.filename)
        
        # 5. 返回文件响应
        headers = {
            "Content-Disposition": f"inline; {safe_filename}",
            "Content-Type": content_type
        }
        
        # 记录查看操作
        log_success("literature_view", current_user.id, {
            "literature_id": literature_id,
            "filename": literature.filename
        })
        
        return FileResponse(
            path=file_path, 
            headers=headers,
            media_type=content_type
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        log_error("literature_view", e, current_user.id, {"literature_id": literature_id})
        raise HTTPException(status_code=500, detail="查看文献失败")

@app.get("/literature/detail/{literature_id}")
async def get_literature_detail(
    literature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文献详细信息
    返回文献的详细元数据，用于前端显示和处理决策
    """
    try:
        # 1. 获取文献信息并验证权限
        literature = get_literature_with_permission(literature_id, current_user.id, db)
        
        # 2. 获取上传用户信息
        uploader = db.query(User).filter(User.id == literature.uploaded_by).first()
        uploader_name = uploader.username if uploader else "未知用户"
        
        # 3. 获取研究组信息
        group = db.query(ResearchGroup).filter(ResearchGroup.id == literature.research_group_id).first()
        group_name = group.name if group else "未知研究组"
        
        # 4. 检查文件是否存在
        file_exists = verify_file_exists(literature.file_path)
        
        # 5. 构建响应数据
        detail_info = {
            "id": literature.id,
            "title": literature.title,
            "filename": literature.filename,
            "file_type": literature.file_type,
            "file_size": literature.file_size,
            "upload_time": literature.upload_time.isoformat() if literature.upload_time else None,
            "uploaded_by": literature.uploaded_by,
            "uploader_name": uploader_name,
            "research_group_id": literature.research_group_id,
            "group_name": group_name,
            "status": literature.status,
            "file_exists": file_exists,
            "can_view": file_exists and literature.status == 'active',
            "content_type": get_content_type(literature.file_path) if file_exists else None
        }
        
        # 6. 记录访问日志
        log_success("literature_detail", current_user.id, {
            "literature_id": literature_id,
            "title": literature.title
        })
        
        return detail_info
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        log_error("literature_detail", e, current_user.id, {"literature_id": literature_id})
        raise HTTPException(status_code=500, detail="获取文献详情失败")

@app.get("/literature/download/{literature_id}")
async def download_literature_file(
    literature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载文献文件
    """
    try:
        # 1. 验证文献权限
        literature = get_literature_with_permission(literature_id, current_user.id, db)
        
        # 2. 验证文件存在
        file_path = get_correct_file_path(literature.file_path)
        if not verify_file_exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 3. 获取文件MIME类型
        content_type = get_content_type(file_path)
        
        # 4. 使用经过编码处理的文件名
        from app.utils.file_handler import get_safe_filename_for_headers
        safe_filename = get_safe_filename_for_headers(literature.filename)
        
        # 5. 返回文件响应
        headers = {
            "Content-Disposition": f"attachment; {safe_filename}",
            "Content-Type": content_type
        }
        
        # 记录下载操作
        log_success("literature_download", current_user.id, {
            "literature_id": literature_id,
            "filename": literature.filename
        })
        
        return FileResponse(
            path=file_path, 
            headers=headers,
            media_type=content_type,
            filename=literature.filename
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        log_error("literature_download", e, current_user.id, {"literature_id": literature_id})
        raise HTTPException(status_code=500, detail="下载文献失败")

# ===== AI系统健康检查接口 =====

@app.get("/health/ai")
async def ai_health_check():
    """
    AI系统健康检查接口
    检查OpenAI API连接状态、向量数据库状态、AI服务响应时间等
    """
    import time
    from datetime import datetime
    
    try:
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "statistics": {},
            "response_time": 0
        }
        
        start_time = time.time()
        failed_checks = 0
        
        # 1. 检查Embedding服务
        try:
            from app.utils.embedding_service import embedding_service
            
            embedding_test_start = time.time()
            test_embedding = embedding_service.generate_embedding("健康检查测试文本")
            embedding_test_time = time.time() - embedding_test_start
            
            if test_embedding and len(test_embedding) > 0:
                health_report["checks"]["embedding_service"] = {
                    "status": "healthy",
                    "response_time": embedding_test_time,
                    "provider": embedding_service.provider,
                    "embedding_dimension": len(test_embedding)
                }
            else:
                health_report["checks"]["embedding_service"] = {
                    "status": "unhealthy",
                    "error": "embedding生成失败"
                }
                failed_checks += 1
                
        except Exception as e:
            health_report["checks"]["embedding_service"] = {
                "status": "error",
                "error": str(e)
            }
            failed_checks += 1
        
        # 2. 检查向量数据库
        try:
            from app.utils.vector_store import vector_store
            
            vector_test_start = time.time()
            vector_stats = vector_store.get_stats()
            vector_test_time = time.time() - vector_test_start
            
            health_report["checks"]["vector_database"] = {
                "status": "healthy",
                "response_time": vector_test_time,
                "stats": vector_stats
            }
            
        except Exception as e:
            health_report["checks"]["vector_database"] = {
                "status": "error",
                "error": str(e)
            }
            failed_checks += 1
        
        # 3. 检查RAG服务
        try:
            from app.utils.rag_service import rag_service
            
            rag_stats = rag_service.get_service_stats()
            health_report["checks"]["rag_service"] = {
                "status": "healthy",
                "stats": rag_stats
            }
            
        except Exception as e:
            health_report["checks"]["rag_service"] = {
                "status": "error",
                "error": str(e)
            }
            failed_checks += 1
        
        # 4. 检查缓存系统
        try:
            from app.utils.cache_manager import cache_manager
            
            cache_stats = cache_manager.get_stats()
            cache_health = cache_manager.health_check()
            
            health_report["checks"]["cache_system"] = {
                "status": cache_health.get("status", "unknown"),
                "stats": cache_stats,
                "health_details": cache_health
            }
            
            if cache_health.get("status") not in ["healthy", "warning"]:
                failed_checks += 1
                
        except Exception as e:
            health_report["checks"]["cache_system"] = {
                "status": "error",
                "error": str(e)
            }
            failed_checks += 1
        
        # 5. 检查对话管理器
        try:
            from app.utils.conversation_manager import conversation_manager
            
            conversation_stats = conversation_manager.get_stats()
            health_report["checks"]["conversation_manager"] = {
                "status": "healthy",
                "stats": conversation_stats
            }
            
        except Exception as e:
            health_report["checks"]["conversation_manager"] = {
                "status": "error",
                "error": str(e)
            }
            failed_checks += 1
        
        # 计算总体状态
        total_checks = len(health_report["checks"])
        health_percentage = ((total_checks - failed_checks) / total_checks) * 100
        
        if failed_checks == 0:
            health_report["overall_status"] = "healthy"
        elif failed_checks <= total_checks * 0.3:  # 30%以下失败
            health_report["overall_status"] = "warning"
        else:
            health_report["overall_status"] = "critical"
        
        # 添加统计信息
        health_report["statistics"] = {
            "total_checks": total_checks,
            "passed_checks": total_checks - failed_checks,
            "failed_checks": failed_checks,
            "health_percentage": health_percentage
        }
        
        # 计算总响应时间
        health_report["response_time"] = time.time() - start_time
        
        logger.info(f"AI健康检查完成: {health_report['overall_status']} "
                   f"({health_report['statistics']['passed_checks']}/{total_checks} 通过)")
        
        # 根据健康状态返回相应的HTTP状态码
        if health_report["overall_status"] == "healthy":
            return health_report
        elif health_report["overall_status"] == "warning":
            return JSONResponse(status_code=200, content=health_report)
        else:
            # 即使是critical状态，也返回200，让调用方自己判断
            return JSONResponse(status_code=200, content=health_report)
            
    except Exception as e:
        logger.error(f"AI健康检查失败: {e}")
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "error",
            "error": str(e),
            "response_time": time.time() - start_time if 'start_time' in locals() else 0
        }
        return JSONResponse(status_code=500, content=error_report)

# ===== 新的认证接口 =====

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing_username = db.query(User).filter(
        User.username == user.username
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册"
        )
    
    # 检查手机号是否已存在
    existing_phone = db.query(User).filter(
        User.phone_number == user.phone_number
    ).first()
    
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="手机号已被注册"
        )
    
    # 哈希密码
    hashed_password = get_password_hash(user.password)
    
    # 创建用户记录
    db_user = User(
        username=user.username,
        phone_number=user.phone_number,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "注册成功"}

@app.post("/api/auth/login", response_model=TokenWithRefresh)
def login_by_phone(user: UserLogin, db: Session = Depends(get_db)):
    # 查找用户
    db_user = db.query(User).filter(
        User.phone_number == user.phone_number
    ).first()
    
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.phone_number},
        expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": db_user.phone_number},
        expires_delta=refresh_token_expires
    )
    # 存到数据库
    db_user.refresh_token = refresh_token
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.get("/api/user/me", response_model=UserInfo)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserInfo(
        id=current_user.id,
        username=current_user.username,
        phone_number=current_user.phone_number
    )

@app.post("/api/auth/refresh", response_model=Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="刷新令牌无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        phone_number: str = payload.get("sub")
        if phone_number is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user is None or user.refresh_token != refresh_token:
        raise credentials_exception

    # 生成新的 access_token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.phone_number},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/groups/{group_id}/info")
def get_group_info(group_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取课题组详细信息
    """
    try:
        # 验证用户是否为该课题组成员
        require_group_membership(current_user.id, group_id, db)
        
        group = db.query(ResearchGroup).filter(ResearchGroup.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="课题组不存在")
        
        return {
            "id": group.id,
            "name": group.name,
            "institution": group.institution,
            "description": group.description,
            "research_area": group.research_area
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error("group_info_detail", e, current_user.id, {"group_id": group_id})
        raise HTTPException(status_code=500, detail="获取课题组信息失败")

@app.get("/groups/{group_id}/members")
def get_group_members(group_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取课题组成员列表
    """
    try:
        # 验证用户是否为该课题组成员
        require_group_membership(current_user.id, group_id, db)
        
        # 查询课题组成员
        members_query = db.query(User, UserResearchGroup).join(
            UserResearchGroup, User.id == UserResearchGroup.user_id
        ).filter(UserResearchGroup.group_id == group_id).all()
        
        members_list = []
        for user, membership in members_query:
            members_list.append({
                "id": user.id,
                "username": user.username,
                "phone_number": user.phone_number
            })
        
        log_success("group_members", current_user.id, {
            "group_id": group_id,
            "member_count": len(members_list)
        })
        
        return {
            "group_id": group_id,
            "members": members_list,
            "total": len(members_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("group_members", e, current_user.id, {"group_id": group_id})
        raise HTTPException(status_code=500, detail="获取课题组成员失败")

@app.post("/groups/{group_id}/leave")
def leave_group(group_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    退出课题组
    """
    try:
        # 验证用户是否为该课题组成员
        membership = db.query(UserResearchGroup).filter(
            UserResearchGroup.user_id == current_user.id,
            UserResearchGroup.group_id == group_id
        ).first()
        
        if not membership:
            raise HTTPException(status_code=404, detail="您不是该课题组成员")
        
        # 检查课题组是否还有其他成员
        other_members = db.query(UserResearchGroup).filter(
            UserResearchGroup.group_id == group_id,
            UserResearchGroup.user_id != current_user.id
        ).count()
        
        if other_members == 0:
            # 如果是最后一个成员，可以选择删除课题组或保留空课题组
            # 这里选择保留空课题组，管理员可以后续清理
            pass
        
        # 删除成员关系
        db.delete(membership)
        db.commit()
        
        log_success("group_leave", current_user.id, {
            "group_id": group_id,
            "remaining_members": other_members
        })
        
        return {
            "message": "成功退出课题组",
            "group_id": group_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("group_leave", e, current_user.id, {"group_id": group_id})
        raise HTTPException(status_code=500, detail="退出课题组失败")
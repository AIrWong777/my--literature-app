# AI驱动协同文献管理系统 - API文档

**版本**: v1.0  
**基础URL**: `http://localhost:8000`  
**最后更新**: 2025年5月28日

---

## 📖 目录

- [认证系统](#认证系统)
- [用户管理](#用户管理)
- [研究组管理](#研究组管理)
- [文献管理](#文献管理)
- [文献高级管理](#文献高级管理)
- [AI助手](#ai助手)
- [对话管理](#对话管理)
- [缓存管理](#缓存管理)
- [管理员功能](#管理员功能)
- [系统健康](#系统健康)
- [错误处理](#错误处理)
- [数据模型](#数据模型)

---

## 🔐 认证系统

### 通用认证说明

本系统支持两种认证方式：
1. **新系统**: 基于手机号的认证（推荐）
2. **兼容模式**: 基于用户名的认证（向后兼容）

#### JWT Token 格式
```
Authorization: Bearer <access_token>
```

#### Token 有效期
- **Access Token**: 60分钟
- **Refresh Token**: 7天

---

### 1. 用户注册

**端点**: `POST /api/auth/register`

**描述**: 使用手机号注册新用户

**请求体**:
```json
{
  "username": "testuser",
  "phone_number": "13800000001",
  "password": "password123",
  "password_confirm": "password123"
}
```

**请求验证**:
- `username`: 3-50字符，必须唯一
- `phone_number`: 11位数字，必须唯一
- `password`: 最少8位字符
- `password_confirm`: 必须与password一致

**成功响应** (201):
```json
{
  "message": "注册成功"
}
```

**错误响应**:
- `409`: 用户名或手机号已被注册
- `422`: 输入验证错误

---

### 2. 手机号登录

**端点**: `POST /api/auth/login`

**描述**: 使用手机号和密码登录

**请求体**:
```json
{
  "phone_number": "13800000001",
  "password": "password123"
}
```

**成功响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**错误响应**:
- `401`: 手机号或密码错误

---

### 3. 传统用户名登录（兼容）

**端点**: `POST /login`

**描述**: 使用用户名和密码登录（向后兼容）

**请求体** (form-data):
```
username: testuser
password: password123
```

**成功响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 4. 刷新访问令牌

**端点**: `POST /api/auth/refresh`

**描述**: 使用refresh token获取新的access token

**请求体**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**成功响应** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 👤 用户管理

### 5. 获取当前用户信息

**端点**: `GET /api/user/me`

**描述**: 获取当前登录用户的信息

**认证**: 需要Bearer Token

**成功响应** (200):
```json
{
  "id": "uuid-string",
  "username": "testuser",
  "phone_number": "13800000001"
}
```

**错误响应**:
- `401`: 未认证或token无效

---

### 6. 获取用户研究组

**端点**: `GET /user/groups`

**描述**: 获取当前用户所属的所有研究组

**认证**: 需要Bearer Token

**成功响应** (200):
```json
{
  "groups": [
    {
      "id": "group-uuid",
      "name": "AI研究组",
      "institution": "某某大学",
      "description": "专注于AI技术研究",
      "research_area": "人工智能",
      "invitation_code": "ABC12345"
    }
  ]
}
```

---

## 👥 研究组管理

### 7. 创建研究组

**端点**: `POST /groups/create`

**描述**: 创建新的研究组

**认证**: 需要Bearer Token

**请求参数** (Query Parameters):
```
name: AI研究组
institution: 某某大学
description: 专注于AI技术研究
research_area: 人工智能
```

**成功响应** (200):
```json
{
  "group_id": "group-uuid",
  "invitation_code": "ABC12345",
  "message": "研究组创建成功"
}
```

**错误响应**:
- `400`: 参数缺失或无效
- `401`: 未认证

---

### 8. 加入研究组

**端点**: `POST /groups/join`

**描述**: 通过邀请码加入研究组

**认证**: 需要Bearer Token

**请求参数** (Query Parameters):
```
group_id: group-uuid
invitation_code: ABC12345
```

**成功响应** (200):
```json
{
  "message": "成功加入研究组"
}
```

**错误响应**:
- `400`: 参数错误或邀请码无效
- `409`: 已经是该组成员

---

## 📚 文献管理

### 9. 上传文献

**端点**: `POST /literature/upload`

**描述**: 上传文献文件到研究组

**认证**: 需要Bearer Token

**请求体** (multipart/form-data):
```
file: <binary-file>           # 文件 (PDF/DOCX/DOC)
group_id: group-uuid          # 研究组ID
title: 机器学习算法研究      # 可选标题
```

**支持的文件类型**:
- PDF (.pdf)
- Word 文档 (.docx, .doc)

**文件限制**:
- 最大文件大小: 50MB
- 必须是支持的文件类型

**成功响应** (200):
```json
{
  "literature_id": "lit-uuid",
  "title": "机器学习算法研究",
  "filename": "paper.pdf",
  "message": "文献上传成功"
}
```

**错误响应**:
- `400`: 文件类型不支持或文件过大
- `403`: 无权限访问该研究组
- `413`: 文件过大

---

### 10. 获取研究组文献列表

**端点**: `GET /literature/public/{group_id}`

**描述**: 获取指定研究组的公共文献列表

**认证**: 需要Bearer Token

**路径参数**:
- `group_id`: 研究组ID

**成功响应** (200):
```json
{
  "literature": [
    {
      "id": "lit-uuid",
      "title": "机器学习算法研究",
      "filename": "paper.pdf",
      "file_size": 2048576,
      "upload_time": "2025-05-28T10:30:00",
      "uploaded_by": "用户名"
    }
  ]
}
```

**错误响应**:
- `403`: 无权限访问该研究组
- `404`: 研究组不存在

---

### 11. 获取文献详情

**端点**: `GET /literature/detail/{literature_id}`

**描述**: 获取特定文献的详细信息

**认证**: 需要Bearer Token

**路径参数**:
- `literature_id`: 文献ID

**成功响应** (200):
```json
{
  "id": "lit-uuid",
  "title": "机器学习算法研究",
  "filename": "paper.pdf",
  "file_size": 2048576,
  "file_type": "pdf",
  "upload_time": "2025-05-28T10:30:00",
  "uploaded_by": "用户名",
  "research_group_id": "group-uuid",
  "abstract": "文献摘要..."
}
```

**错误响应**:
- `403`: 无权限访问该文献
- `404`: 文献不存在

---

### 12. 查看/预览文献文件

**端点**: `GET /literature/view/file/{literature_id}`

**描述**: 在线预览文献文件

**认证**: 需要Bearer Token

**路径参数**:
- `literature_id`: 文献ID

**成功响应** (200):
- **Content-Type**: 根据文件类型设置
  - PDF: `application/pdf`
  - DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Body**: 文件二进制数据
- **Content-Disposition**: `inline; filename*=UTF-8''filename.pdf`

**错误响应**:
- `403`: 无权限访问该文献
- `404`: 文献或文件不存在

---

### 13. 下载文献文件

**端点**: `GET /literature/download/{literature_id}`

**描述**: 强制下载文献文件

**认证**: 需要Bearer Token

**路径参数**:
- `literature_id`: 文献ID

**成功响应** (200):
- **Content-Type**: 根据文件类型设置
- **Body**: 文件二进制数据
- **Content-Disposition**: `attachment; filename*=UTF-8''filename.pdf`

**错误响应**:
- `403`: 无权限访问该文献
- `404`: 文献或文件不存在

---

## 🗂️ 文献高级管理

### 14. 软删除文献

**端点**: `DELETE /literature/{literature_id}`

**描述**: 软删除文献（可恢复）

**认证**: 需要Bearer Token

**路径参数**:
- `literature_id`: 文献ID

**查询参数**:
- `reason`: 删除原因（可选）

**成功响应** (200):
```json
{
  "message": "文献删除成功",
  "literature_id": "lit-uuid"
}
```

**错误响应**:
- `403`: 无权限删除该文献
- `404`: 文献不存在

---

### 15. 恢复已删除文献

**端点**: `POST /literature/{literature_id}/restore`

**描述**: 恢复已软删除的文献

**认证**: 需要Bearer Token

**路径参数**:
- `literature_id`: 文献ID

**成功响应** (200):
```json
{
  "message": "文献恢复成功",
  "literature_id": "lit-uuid"
}
```

**错误响应**:
- `403`: 无权限恢复该文献
- `404`: 文献不存在或未删除

---

### 16. 获取已删除文献列表

**端点**: `GET /literature/deleted/{group_id}`

**描述**: 获取研究组的已删除文献列表

**认证**: 需要Bearer Token

**路径参数**:
- `group_id`: 研究组ID

**成功响应** (200):
```json
{
  "group_id": "group-uuid",
  "deleted_literature": [
    {
      "id": "lit-uuid",
      "title": "已删除的文献",
      "deleted_at": "2025-05-28T10:30:00",
      "deleted_by": "用户名",
      "delete_reason": "测试删除"
    }
  ],
  "count": 1
}
```

---

### 17. 获取文献统计信息

**端点**: `GET /literature/stats/{group_id}`

**描述**: 获取研究组文献统计信息

**认证**: 需要Bearer Token

**路径参数**:
- `group_id`: 研究组ID

**成功响应** (200):
```json
{
  "group_id": "group-uuid",
  "statistics": {
    "active_count": 15,
    "deleted_count": 2,
    "total_size": 134217728,
    "file_types": {
      "pdf": 12,
      "docx": 3,
      "doc": 2
    },
    "upload_trend": {
      "last_7_days": 5,
      "last_30_days": 12
    }
  }
}
```

---

## 🤖 AI助手

### 18. AI问答

**端点**: `POST /ai/ask`

**描述**: 基于特定文献进行AI问答

**认证**: 需要Bearer Token

**请求体**:
```json
{
  "question": "这篇文献的主要观点是什么？",
  "literature_id": "lit-uuid",
  "session_id": "session-uuid",
  "max_sources": 5,
  "include_history": true
}
```

**请求参数说明**:
- `question`: 用户问题（必填）
- `literature_id`: 目标文献ID（必填）
- `session_id`: 会话ID（可选，自动创建）
- `max_sources`: 最大检索来源数量（可选，默认5）
- `include_history`: 是否包含对话历史（可选，默认true）

**成功响应** (200):
```json
{
  "answer": "根据文献内容，主要观点包括...",
  "sources": [
    {
      "content": "相关文献片段内容...",
      "page": 5,
      "confidence": 0.95
    }
  ],
  "confidence": 0.9,
  "processing_time": 2.5,
  "session_id": "session-uuid",
  "turn_id": "turn-uuid"
}
```

**错误响应**:
- `400`: 问题为空或参数无效
- `403`: 无权限访问该文献
- `500`: AI服务不可用

---

### 19. 获取预设问题

**端点**: `GET /ai/preset-questions/{literature_id}`

**描述**: 获取针对特定文献的预设问题列表

**认证**: 需要Bearer Token

**路径参数**:
- `literature_id`: 文献ID

**成功响应** (200):
```json
{
  "questions": [
    "请总结这篇文献的核心论点",
    "这篇文献的主要研究方法是什么？",
    "文献中有哪些重要的实验结果？",
    "这篇文献的创新点在哪里？",
    "文献中提到了哪些局限性？"
  ]
}
```

---

## 💬 对话管理

### 20. 获取用户会话列表

**端点**: `GET /ai/sessions`

**描述**: 获取当前用户的AI对话会话列表

**认证**: 需要Bearer Token

**查询参数**:
- `literature_id`: 按文献ID筛选（可选）
- `limit`: 返回数量限制（默认20）
- `offset`: 偏移量（默认0）

**成功响应** (200):
```json
{
  "sessions": [
    {
      "session_id": "session-uuid",
      "literature_id": "lit-uuid",
      "literature_title": "文献标题",
      "created_at": "2025-05-28T10:30:00",
      "last_activity": "2025-05-28T11:45:00",
      "turn_count": 5,
      "preview": "最后一次对话预览..."
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

### 21. 获取对话历史

**端点**: `GET /ai/conversation/{session_id}`

**描述**: 获取指定会话的详细对话历史

**认证**: 需要Bearer Token

**路径参数**:
- `session_id`: 会话ID

**查询参数**:
- `include_full_content`: 是否包含完整内容（默认true）
- `limit`: 返回轮次限制（默认50）

**成功响应** (200):
```json
{
  "session_id": "session-uuid",
  "literature_id": "lit-uuid",
  "created_at": "2025-05-28T10:30:00",
  "conversation_turns": [
    {
      "turn_id": "turn-uuid",
      "turn_index": 1,
      "timestamp": "2025-05-28T10:30:00",
      "question": "用户问题",
      "answer": "AI回答",
      "confidence": 0.9,
      "processing_time": 2.5,
      "user_rating": null
    }
  ],
  "total_turns": 1
}
```

---

### 22. 删除对话会话

**端点**: `DELETE /ai/conversation/{session_id}`

**描述**: 删除指定的对话会话

**认证**: 需要Bearer Token

**路径参数**:
- `session_id`: 会话ID

**成功响应** (200):
```json
{
  "message": "对话会话已删除",
  "session_id": "session-uuid"
}
```

---

### 23. 对话反馈

**端点**: `POST /ai/feedback`

**描述**: 对AI回答进行评分反馈

**认证**: 需要Bearer Token

**请求体**:
```json
{
  "turn_id": "turn-uuid",
  "rating": 5,
  "feedback": "回答很有帮助"
}
```

**成功响应** (200):
```json
{
  "message": "反馈提交成功",
  "turn_id": "turn-uuid"
}
```

---

## 🗄️ 缓存管理

### 24. 获取缓存统计

**端点**: `GET /admin/cache/stats`

**描述**: 获取系统缓存统计信息

**认证**: 无需认证

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "embedding_cache": {
      "size": 100,
      "hit_rate": 0.85,
      "memory_usage": "45MB"
    },
    "answer_cache": {
      "size": 50,
      "hit_rate": 0.72,
      "memory_usage": "12MB"
    },
    "chunk_cache": {
      "size": 200,
      "hit_rate": 0.90,
      "memory_usage": "78MB"
    }
  },
  "message": "缓存统计信息获取成功"
}
```

---

### 25. 缓存健康检查

**端点**: `GET /admin/cache/health`

**描述**: 检查缓存系统健康状态

**认证**: 无需认证

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "cache_systems": {
      "embedding_cache": "healthy",
      "answer_cache": "healthy",
      "chunk_cache": "warning"
    },
    "memory_usage": {
      "total": "135MB",
      "available": "365MB",
      "usage_percentage": 27
    }
  }
}
```

---

### 26. 清理缓存

**端点**: `POST /admin/cache/clear`

**描述**: 清理指定类型的缓存

**认证**: 无需认证

**查询参数**:
- `cache_type`: 缓存类型（all/embedding/answer/chunk/literature_<id>）

**成功响应** (200):
```json
{
  "success": true,
  "message": "所有缓存已清理"
}
```

---

### 27. 获取缓存详细信息

**端点**: `GET /admin/cache/info/{cache_type}`

**描述**: 获取特定缓存类型的详细信息

**认证**: 无需认证

**路径参数**:
- `cache_type`: 缓存类型（embedding/answer/chunk）

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "cache_type": "embedding",
    "total_entries": 100,
    "memory_usage": "45MB",
    "oldest_entry": "2025-05-28T10:00:00",
    "newest_entry": "2025-05-28T11:30:00",
    "hit_rate": 0.85
  }
}
```

---

### 28. 获取缓存键列表

**端点**: `GET /admin/cache/keys/{cache_type}`

**描述**: 获取指定缓存类型的键列表

**认证**: 无需认证

**路径参数**:
- `cache_type`: 缓存类型

**查询参数**:
- `limit`: 返回数量限制（默认100）
- `pattern`: 键名模式匹配（可选）

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "cache_type": "embedding",
    "keys": [
      "embedding:doc1:chunk1",
      "embedding:doc2:chunk3"
    ],
    "total_keys": 100,
    "returned_count": 2
  }
}
```

---

### 29. 删除特定缓存键

**端点**: `DELETE /admin/cache/key/{cache_type}/{key}`

**描述**: 删除指定的缓存键

**认证**: 无需认证

**路径参数**:
- `cache_type`: 缓存类型
- `key`: 缓存键名

**成功响应** (200):
```json
{
  "success": true,
  "message": "缓存键已删除",
  "cache_type": "embedding",
  "key": "embedding:doc1:chunk1"
}
```

---

### 30. 预热缓存

**端点**: `POST /admin/cache/warm`

**描述**: 预热缓存系统

**认证**: 无需认证

**请求体**:
```json
{
  "literature_ids": ["lit-uuid1", "lit-uuid2"],
  "cache_types": ["embedding", "chunk"]
}
```

**成功响应** (200):
```json
{
  "success": true,
  "message": "缓存预热完成",
  "warmed_items": {
    "embedding": 50,
    "chunk": 100
  }
}
```

---

### 31. 缓存性能测试

**端点**: `GET /admin/cache/benchmark`

**描述**: 执行缓存系统性能测试

**认证**: 无需认证

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "embedding_cache": {
      "read_time": 0.05,
      "write_time": 0.08,
      "hit_rate": 0.85
    },
    "answer_cache": {
      "read_time": 0.03,
      "write_time": 0.06,
      "hit_rate": 0.72
    }
  }
}
```

---

## ⚙️ 管理员功能

### 32. 获取存储统计

**端点**: `GET /admin/storage/stats`

**描述**: 获取文件存储统计信息

**认证**: 需要Bearer Token

**成功响应** (200):
```json
{
  "storage_statistics": {
    "total_groups": 5,
    "total_files": 50,
    "total_size": 1073741824,
    "average_file_size": 21474836,
    "file_type_distribution": {
      "pdf": 35,
      "docx": 10,
      "doc": 5
    }
  },
  "storage_health": {
    "disk_usage": "25%",
    "available_space": "750GB",
    "orphaned_files": 0,
    "missing_files": 0
  }
}
```

---

### 33. 清理存储

**端点**: `POST /admin/storage/cleanup`

**描述**: 清理存储空间（删除空目录等）

**认证**: 需要Bearer Token

**成功响应** (200):
```json
{
  "message": "存储清理完成",
  "cleaned_directories": [
    "/uploads/empty_group_1",
    "/uploads/temp_folder"
  ],
  "count": 2
}
```

---

### 34. AI服务统计

**端点**: `GET /ai/stats`

**描述**: 获取AI服务统计信息（需要登录）

**认证**: 需要Bearer Token

**成功响应** (200):
```json
{
  "total_queries": 1000,
  "average_response_time": 2.5,
  "success_rate": 0.95,
  "popular_questions": [
    "文献主要内容",
    "研究方法",
    "实验结果"
  ],
  "daily_usage": {
    "2025-05-28": 150,
    "2025-05-27": 120
  }
}
```

---

## 🏥 系统健康

### 35. 基础健康检查

**端点**: `GET /health`

**描述**: 检查系统基础健康状态

**认证**: 无需认证

**成功响应** (200):
```json
{
  "status": "healthy",
  "timestamp": "2025-05-28T10:30:00.123456"
}
```

---

### 36. AI服务健康检查

**端点**: `GET /health/ai`

**描述**: 检查AI服务健康状态

**认证**: 无需认证

**成功响应** (200):
```json
{
  "timestamp": "2025-05-28T10:30:00",
  "overall_status": "healthy",
  "checks": {
    "embedding_service": {
      "status": "healthy",
      "response_time": 0.15,
      "provider": "openai",
      "embedding_dimension": 1536
    },
    "vector_database": {
      "status": "healthy",
      "response_time": 0.05,
      "stats": {
        "total_vectors": 1000,
        "collections": 5
      }
    },
    "rag_service": {
      "status": "healthy",
      "stats": {
        "cache_hit_rate": 0.85,
        "average_query_time": 2.5
      }
    },
    "cache_system": {
      "status": "healthy",
      "stats": {
        "total_entries": 500,
        "memory_usage": "135MB"
      }
    },
    "conversation_manager": {
      "status": "healthy",
      "stats": {
        "active_sessions": 10,
        "total_conversations": 100
      }
    }
  },
  "statistics": {
    "total_checks": 5,
    "passed_checks": 5,
    "failed_checks": 0,
    "health_percentage": 100
  },
  "response_time": 0.25
}
```

---

### 37. AI服务健康检查（简化版）

**端点**: `GET /ai/health`

**描述**: AI模块的健康检查接口

**认证**: 无需认证

**成功响应** (200):
```json
{
  "status": "healthy",
  "timestamp": "2025-05-28T10:30:00"
}
```

**错误响应** (500):
```json
{
  "status": "unhealthy",
  "error": "服务不可用",
  "timestamp": "2025-05-28T10:30:00"
}
```

---

### 38. 系统根路径

**端点**: `GET /`

**描述**: 获取API基本信息

**认证**: 无需认证

**成功响应** (200):
```json
{
  "message": "欢迎使用文献管理系统API",
  "version": "1.0.0",
  "status": "运行中",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

## ⚠️ 错误处理

### 通用错误格式

所有API错误响应都遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### HTTP状态码说明

| 状态码 | 说明 | 常见场景 |
|--------|------|----------|
| 200 | 成功 | 请求处理成功 |
| 201 | 创建成功 | 用户注册成功 |
| 400 | 请求错误 | 参数缺失或格式错误 |
| 401 | 未认证 | Token缺失或无效 |
| 403 | 权限不足 | 无权限访问资源 |
| 404 | 资源不存在 | 用户、文献或研究组不存在 |
| 409 | 冲突 | 用户名或手机号重复 |
| 413 | 文件过大 | 上传文件超过限制 |
| 422 | 参数验证失败 | 输入数据格式错误 |
| 500 | 服务器错误 | 内部服务错误 |

### 常见错误示例

**认证失败**:
```json
{
  "detail": "手机号或密码错误"
}
```

**权限不足**:
```json
{
  "detail": "您不是该研究组的成员"
}
```

**文件类型错误**:
```json
{
  "detail": "不支持的文件类型。允许的类型: .pdf, .docx, .doc"
}
```

**输入验证错误**:
```json
{
  "detail": "两次输入密码不一致"
}
```

---

## 📋 数据模型

### User (用户)
```typescript
interface User {
  id: string;                    // UUID
  username: string;              // 用户名，唯一
  phone_number: string;          // 手机号，唯一
  email?: string;                // 邮箱，可选
}
```

### ResearchGroup (研究组)
```typescript
interface ResearchGroup {
  id: string;                    // UUID
  name: string;                  // 研究组名称
  institution: string;           // 所属机构
  description: string;           // 描述
  research_area: string;         // 研究领域
  invitation_code: string;       // 邀请码，唯一
}
```

### Literature (文献)
```typescript
interface Literature {
  id: string;                    // UUID
  title: string;                 // 标题
  filename: string;              // 原始文件名
  file_size: number;             // 文件大小（字节）
  file_type: string;             // 文件类型
  upload_time: string;           // 上传时间 (ISO 8601)
  uploaded_by: string;           // 上传用户
  research_group_id: string;     // 所属研究组
  abstract?: string;             // 摘要，可选
  is_deleted?: boolean;          // 是否已删除
  deleted_at?: string;           // 删除时间
  deleted_by?: string;           // 删除用户
  delete_reason?: string;        // 删除原因
}
```

### Token Response (令牌响应)
```typescript
interface TokenResponse {
  access_token: string;          // 访问令牌
  refresh_token?: string;        // 刷新令牌（新接口返回）
  token_type: string;            // 令牌类型，通常为 "bearer"
}
```

### AI Response (AI响应)
```typescript
interface AIResponse {
  answer: string;                // AI回答
  sources: Array<{               // 引用来源
    content: string;             // 来源内容
    page?: number;               // 页码
    confidence: number;          // 置信度
  }>;
  confidence: number;            // 整体置信度
  processing_time: number;       // 处理时间（秒）
  session_id: string;            // 会话ID
  turn_id: string;               // 对话轮次ID
}
```

### Conversation Session (对话会话)
```typescript
interface ConversationSession {
  session_id: string;            // 会话ID
  literature_id: string;         // 文献ID
  literature_title: string;      // 文献标题
  created_at: string;            // 创建时间
  last_activity: string;         // 最后活动时间
  turn_count: number;            // 对话轮次数
  preview: string;               // 对话预览
}
```

### Conversation Turn (对话轮次)
```typescript
interface ConversationTurn {
  turn_id: string;               // 轮次ID
  turn_index: number;            // 轮次序号
  timestamp: string;             // 时间戳
  question: string;              // 用户问题
  answer: string;                // AI回答
  confidence: number;            // 置信度
  processing_time: number;       // 处理时间
  user_rating?: number;          // 用户评分(1-5)
}
```

### Cache Statistics (缓存统计)
```typescript
interface CacheStats {
  size: number;                  // 缓存条目数
  hit_rate: number;              // 命中率
  memory_usage: string;          // 内存使用量
  oldest_entry?: string;         // 最老条目时间
  newest_entry?: string;         // 最新条目时间
}
```

### Storage Statistics (存储统计)
```typescript
interface StorageStats {
  total_groups: number;          // 总研究组数
  total_files: number;           // 总文件数
  total_size: number;            // 总大小（字节）
  average_file_size: number;     // 平均文件大小
  file_type_distribution: {      // 文件类型分布
    [key: string]: number;
  };
}
```

---

## 🔧 开发建议

### 1. API使用优先级

**推荐使用顺序**:
1. 认证系统：优先使用新的手机号登录接口
2. 文献管理：先获取列表，再查看详情
3. AI功能：先获取预设问题，再进行问答
4. 对话管理：使用会话ID保持上下文

### 2. 缓存策略

**前端缓存建议**:
- 文献列表：缓存5分钟
- 用户信息：缓存30分钟
- 预设问题：缓存1小时
- AI回答：不建议缓存（内容可能动态变化）

### 3. 错误重试策略

**重试建议**:
- 5xx错误：最多重试3次，指数退避
- 401错误：自动刷新token后重试1次
- 403错误：不建议重试
- 其他错误：根据具体情况处理

### 4. 文件处理

**大文件处理**:
- 上传前检查文件大小和类型
- 使用进度条显示上传状态
- 支持断点续传（如果后端支持）
- 预览功能使用`/view/file/`接口
- 下载功能使用`/download/`接口

### 5. 实时功能

**WebSocket支持**:
- 考虑为AI问答添加流式响应
- 实时通知新文献上传
- 实时显示其他用户的活动状态

---

## 📞 技术支持

如有API相关问题，请联系后端开发团队：
- 文档版本：v1.0
- 最后更新：2025年5月28日
- 测试环境：http://localhost:8000

**注意事项**:
1. 所有时间格式均为 ISO 8601 标准
2. 所有UUID格式均为标准UUID4
3. 文件大小限制为50MB
4. API响应均为JSON格式
5. 建议使用HTTPS进行生产部署
6. 管理员功能需要适当的权限控制
7. 缓存管理接口主要用于开发和调试
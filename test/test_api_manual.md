 # 课题组管理功能测试指南

## 测试环境准备

### 1. 启动应用
```bash
cd /d/Downloads/ai_code
python run.py
```
应用将在 http://localhost:8000 启动

### 2. 访问API文档
在浏览器中打开：http://localhost:8000/docs
这是FastAPI自动生成的交互式API文档界面

---

## 测试流程

### 步骤1：创建测试用户（如果还没有）
首先需要在数据库中有测试用户。查看是否已经有 `create_test_user.py` 脚本。

### 步骤2：用户登录获取Token
1. 在API文档中找到 `POST /login` 接口
2. 点击 "Try it out"
3. 输入测试数据：
   ```
   username: testuser
   password: password123
   ```
4. 点击 "Execute"
5. 复制返回的 `access_token`

### 步骤3：设置认证Token
1. 在API文档页面顶部找到 "Authorize" 按钮
2. 点击后在弹窗中输入：`Bearer 你的access_token`
3. 点击 "Authorize"

### 步骤4：测试创建课题组
1. 找到 `POST /groups/create` 接口
2. 点击 "Try it out"
3. 输入测试数据：
   ```json
   {
     "name": "人工智能研究组",
     "institution": "清华大学",
     "description": "专注于机器学习和深度学习研究",
     "research_area": "人工智能"
   }
   ```
4. 点击 "Execute"
5. **记录返回的 group_id 和 invitation_code**

### 步骤5：测试加入课题组
1. 找到 `POST /groups/join` 接口
2. 点击 "Try it out"
3. 输入刚才创建的课题组信息：
   ```json
   {
     "group_id": "刚才返回的group_id",
     "invitation_code": "刚才返回的invitation_code"
   }
   ```
4. 点击 "Execute"

---

## 预期结果

### 登录成功
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 创建课题组成功
```json
{
  "group_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "invitation_code": "xxxxxxxx"
}
```

### 加入课题组成功
```json
{
  "message": "成功加入课题组"
}
```

### 重复加入应该失败
```json
{
  "detail": "用户已加入该课题组"
}
```

---

## 常见问题排查

### 1. 登录失败
- 检查用户是否存在于数据库
- 检查密码是否正确
- 运行测试用户创建脚本

### 2. 认证失败 
- 确保复制了完整的access_token
- 确保在Authorize中正确设置了Bearer token

### 3. 数据库错误
- 检查 literature_system.db 文件是否存在
- 检查数据库表是否正确创建

### 4. 端口占用
- 如果8000端口被占用，可以在run.py中修改端口
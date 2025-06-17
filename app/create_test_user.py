import sys
sys.stdout.reconfigure(line_buffering=True)  # 强制刷新输出

from app.database import SessionLocal
from app.models.user import User  # 修改这里
from app.auth import get_password_hash

print("开始运行 create_test_user.py")  # 调试信息

def create_test_user():
    print("进入 create_test_user 函数")  # 调试信息
    db = SessionLocal()
    print("成功创建数据库会话")  # 调试信息
    try:
        existing = db.query(User).filter(User.username == "testuser").first()
        print("完成查询现有用户，结果:", existing)  # 调试信息
        if existing:
            print("用户 testuser 已存在，跳过创建。")
            return

        user = User(
            username="testuser",
            email="testuser@example.com",
            password_hash=get_password_hash("testpassword")
        )
        print("成功创建新用户对象")  # 调试信息
        db.add(user)
        print("成功添加用户到数据库")  # 调试信息
        db.commit()
        print(f"创建成功，用户ID：{user.id}")
    except Exception as e:
        print("创建用户出错:", e)
        db.rollback()
    finally:
        db.close()
        print("数据库会话已关闭")  # 调试信息

if __name__ == "__main__":
    create_test_user()
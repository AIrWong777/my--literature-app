import uvicorn
import logging
import os

# 设置更详细的日志级别
logging.getLogger('app.utils.rag_service').setLevel(logging.DEBUG)
logging.getLogger('app.utils.vector_store').setLevel(logging.DEBUG)
logging.getLogger('app.utils.prompt_builder').setLevel(logging.DEBUG)

# 运行FastAPI应用
if __name__ == "__main__": 
    # 从环境变量获取配置，或使用默认值
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    # 启动应用
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=True,
        log_level="info"
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.api import chat

# 创建FastAPI应用
app = FastAPI(
    title="AI知识竞答Agent API",
    description="带有人设的聊天和答题API",
    version="0.1.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(chat.router, prefix="/api", tags=["聊天"])

# 健康检查路由
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "AI知识竞答Agent API 正在运行",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True) 
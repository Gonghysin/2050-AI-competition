"""
主应用模块

FastAPI主应用入口和配置
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.api import router
from backend.app.config.settings import settings

# 创建FastAPI应用
app = FastAPI(
    title="AI答题系统",
    description="具有人设(Role-Card)、可与用户闲聊、又能在用户提出挑战意图时自动进入答题工作流的智能Agent",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(router)

# 健康检查接口
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 根路径重定向到文档
@app.get("/")
async def root():
    return {"message": "欢迎使用AI答题系统API，访问 /docs 查看API文档"}

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 
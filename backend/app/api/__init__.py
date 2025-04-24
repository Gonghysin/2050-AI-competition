"""
API路由模块

包含所有API路由的初始化和注册
"""
from fastapi import APIRouter

from backend.app.api.chat import router as chat_router
from backend.app.api.quiz import router as quiz_router

# 创建主路由
router = APIRouter(prefix="/api")

# 注册子路由
router.include_router(chat_router)
router.include_router(quiz_router)

__all__ = ["router"] 
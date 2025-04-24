"""
聊天API路由模块

处理用户聊天请求、意图识别和状态管理
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

from backend.app.models.user import UserSession, RoleCard
from backend.app.models.response import AgentResponse
from backend.app.core.memory import memory_manager
from backend.app.core.workflow import quiz_workflow
from backend.app.utils.llm_client import llm_client
from backend.app.config.role_cards import EVIL_FROG_DOCTOR, SMART_SENIOR_SISTER

router = APIRouter(prefix="/chat", tags=["聊天"])

class MessageRequest(BaseModel):
    """用户消息请求模型"""
    user_id: str
    message: str
    role_card_id: Optional[str] = None  # 可选，指定角色卡ID
    
class SessionRequest(BaseModel):
    """会话请求模型"""
    role_card_id: str = "evil_frog"  # 默认角色卡ID为邪恶青蛙
    
class HistoryRequest(BaseModel):
    """历史记录请求模型"""
    user_id: str
    limit: Optional[int] = 20
    
    
# 角色卡映射
ROLE_CARDS = {
    "evil_frog": EVIL_FROG_DOCTOR,  # 邪恶青蛙博士
    "smart_sister": SMART_SENIOR_SISTER  # 聪明学姐
}

# 设置默认角色卡
DEFAULT_ROLE_CARD = "evil_frog"


@router.post("/send", response_model=AgentResponse)
async def send_message(request: MessageRequest):
    """
    发送消息给AI
    
    处理用户发送的消息，根据当前状态返回聊天回复或出题
    """
    user_id = request.user_id
    message = request.message
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        # 如果不存在，使用默认角色卡创建新会话
        role_card_id = request.role_card_id or DEFAULT_ROLE_CARD
        role_card_data = ROLE_CARDS.get(role_card_id, EVIL_FROG_DOCTOR)
        role_card = RoleCard(**role_card_data)
        session = memory_manager.create_session(user_id, role_card)
    
    # 添加用户消息到历史记录
    memory_manager.add_message(user_id, "user", message)
    
    # 获取对话历史
    conversation_history = memory_manager.get_conversation_history(user_id)
    
    # 生成AI回复
    response = llm_client.chat_with_format(
        user_message=message,
        role_card=session.role_card.model_dump(),
        conversation_history=conversation_history,
        status=session.status,
        quiz_info=session.quiz_progress
    )
    
    # 添加AI回复到历史记录
    memory_manager.add_message(user_id, "agent", response.message)
    
    # 检查状态是否变化
    if response.status != session.status:
        memory_manager.update_session_status(user_id, response.status)
        
        # 如果切换到答题模式，初始化答题进度
        if response.status == "quiz" and not session.quiz_progress:
            quiz_response = quiz_workflow.start_quiz(user_id)
            return quiz_response
    
    return response


@router.post("/create_session", response_model=Dict[str, Any])
async def create_session(request: SessionRequest):
    """
    创建新的聊天会话
    
    参数:
        request: 包含角色卡ID
        
    返回:
        包含用户ID和初始问候语的响应
    """
    # 生成唯一用户ID
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    # 获取角色卡数据
    role_card_data = ROLE_CARDS.get(request.role_card_id, EVIL_FROG_DOCTOR)
    role_card = RoleCard(**role_card_data)
    
    # 创建会话
    session = memory_manager.create_session(user_id, role_card)
    
    # 生成初始问候语
    greeting_prompt = f"你好，我是{role_card.name}。请简短地用你的角色风格向新用户问好。"
    greeting_response = llm_client.chat(
        messages=[
            {"role": "system", "content": f"你是{role_card.name}。{role_card.background}"},
            {"role": "user", "content": greeting_prompt}
        ],
        temperature=0.7
    )
    
    greeting = greeting_response["choices"][0]["message"]["content"]
    
    # 添加问候语到历史记录
    memory_manager.add_message(user_id, "agent", greeting)
    
    return {
        "user_id": user_id,
        "role_card": role_card.model_dump(),
        "greeting": greeting
    }


@router.get("/history/{user_id}", response_model=List[Dict[str, Any]])
async def get_history(user_id: str, limit: int = 20):
    """
    获取聊天历史
    
    参数:
        user_id: 用户ID
        limit: 返回的历史消息数量限制
        
    返回:
        历史消息列表
    """
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取历史记录
    history = memory_manager.get_conversation_history(user_id, limit)
    
    return history


@router.delete("/session/{user_id}")
async def delete_session(user_id: str):
    """
    删除会话
    
    参数:
        user_id: 用户ID
        
    返回:
        操作结果
    """
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 删除会话
    memory_manager.delete_session(user_id)
    
    return {"status": "success", "message": "会话已删除"}


@router.get("/role_cards", response_model=Dict[str, Any])
async def get_role_cards():
    """
    获取所有可用的角色卡
    
    返回:
        角色卡信息
    """
    result = {}
    for role_id, role_data in ROLE_CARDS.items():
        result[role_id] = {
            "name": role_data["name"],
            "avatar": role_data.get("avatar", ""),
            "description": role_data.get("description", "")
        }
    
    return result 
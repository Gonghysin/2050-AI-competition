from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.app.models.response import AgentResponse
from backend.app.core.memory import memory_manager
from backend.app.utils.llm_client import llm_client
from backend.app.config.role_cards import get_role_card

router = APIRouter()

class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str
    message: str
    role_id: str = "evil_frog_doctor"
    session_id: Optional[str] = None

@router.post("/chat", response_model=AgentResponse)
async def chat(request: ChatRequest) -> AgentResponse:
    """
    聊天接口
    
    根据用户消息、角色设定和对话历史，生成符合角色设定的回复
    """
    # 获取用户会话
    session = memory_manager.get_session(request.user_id)
    
    # 如果会话不存在，创建新会话
    if not session:
        role_card = get_role_card(request.role_id)
        session = memory_manager.create_session(request.user_id, role_card)
    
    # 将用户消息添加到会话
    memory_manager.add_message(request.user_id, "user", request.message)
    
    # 获取对话历史
    conversation_history = memory_manager.get_conversation_history(request.user_id)
    
    # 获取角色卡
    role_card = get_role_card(request.role_id)
    
    # 调用LLM生成回复
    response = llm_client.chat_with_format(
        user_message=request.message,
        role_card=role_card,
        conversation_history=conversation_history,
        status=session.status,
        quiz_info=session.quiz_progress
    )
    
    # 将AI回复添加到会话
    memory_manager.add_message(request.user_id, "agent", response.message)
    
    # 如果状态变更，更新会话状态
    if response.status != session.status:
        memory_manager.update_session_status(request.user_id, response.status)
    
    # 如果是答题模式且有题目信息，更新答题进度
    if response.status == "quiz" and response.quiz_info:
        memory_manager.update_quiz_progress(
            request.user_id,
            {
                "current_step": response.quiz_info.step,
                "total_step": response.quiz_info.total,
                "current_question_id": response.quiz_info.question_id,
                "correct_count": session.quiz_progress.get("correct_count", 0) if session.quiz_progress else 0
            }
        )
    
    return response 
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from typing import Optional, Dict, Any, List
import json
import logging
from pydantic import BaseModel

from backend.app.models.response import AgentResponse
from backend.app.core.workflow import ExamWorkflow
from backend.app.core.auth import validate_session

router = APIRouter()
logger = logging.getLogger(__name__)

# 会话存储
sessions: Dict[str, ExamWorkflow] = {}

class SessionRequest(BaseModel):
    session_id: Optional[str] = None

@router.post("/chat", response_model=AgentResponse)
async def chat_endpoint(
    request: Request,
    message: Dict[str, Any] = Body(...),
    session_id: str = Depends(validate_session)
):
    """聊天终端点，处理用户消息并返回代理响应"""
    try:
        # 获取用户消息
        user_message = message.get("message", "").strip()
        logger.info(f"Received message from session {session_id}: {user_message}")
        
        # 获取或创建会话工作流
        workflow = sessions.get(session_id)
        if not workflow:
            logger.info(f"Creating new workflow for session {session_id}")
            workflow = ExamWorkflow()
            sessions[session_id] = workflow
        
        # 处理用户消息并获取响应
        if workflow.current_step == 0:
            # 开始测验，获取第一个问题
            response = workflow.next_question()
        elif user_message.lower() in ["下一题", "next"]:
            # 用户请求下一题
            response = workflow.next_question()
        else:
            # 处理用户答案
            response = workflow.process_answer(user_message)
        
        # 确保响应包含audio_url字段，即使为空
        if not hasattr(response, 'audio_url'):
            response.audio_url = None
            
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理聊天消息时出错: {str(e)}"
        )

@router.post("/session", response_model=Dict[str, str])
async def create_session():
    """创建新会话并返回会话ID"""
    try:
        # 在这里我们只是创建一个新的会话ID
        response = {"message": "会话已创建"}
        return response
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建会话时出错: {str(e)}"
        ) 
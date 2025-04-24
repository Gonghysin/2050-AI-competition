"""
聊天API路由模块

处理用户聊天请求、意图识别和状态管理
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
import json
import logging

from backend.app.models.user import UserSession, RoleCard
from backend.app.models.response import AgentResponse
from backend.app.core.memory import memory_manager
from backend.app.core.workflow import quiz_workflow
from backend.app.utils.llm_client import llm_client
from backend.app.config.role_cards import EVIL_FROG_DOCTOR, SMART_SENIOR_SISTER
from backend.app.tools.tts import text_to_speech_url

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("chat_api")

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
    
    logger.info(f"收到用户[{user_id}]消息: {message[:50]}...")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        # 如果不存在，使用默认角色卡创建新会话
        role_card_id = request.role_card_id or DEFAULT_ROLE_CARD
        role_card_data = ROLE_CARDS.get(role_card_id, EVIL_FROG_DOCTOR)
        role_card = RoleCard(**role_card_data)
        session = memory_manager.create_session(user_id, role_card)
        logger.info(f"为用户[{user_id}]创建新会话，角色: {role_card.name}")
    
    # 添加用户消息到历史记录
    memory_manager.add_message(user_id, "user", message)
    
    # 获取对话历史
    conversation_history = memory_manager.get_conversation_history(user_id)
    logger.info(f"用户[{user_id}]当前状态: {session.status}, 历史消息数: {len(conversation_history)}")
    
    # 预先检查用户消息是否包含答题意图关键词
    quiz_keywords = ["挑战", "答题", "测试", "考考", "出题", "问题"]
    has_quiz_intent = any(keyword in message for keyword in quiz_keywords)
    
    # 如果检测到答题意图且当前状态是聊天状态，直接切换到答题模式
    if has_quiz_intent and session.status == "chat":
        logger.info(f"用户[{user_id}]消息中检测到答题意图关键词，直接切换到答题模式")
        memory_manager.update_session_status(user_id, "quiz")
        session.status = "quiz"
        
        # 直接启动答题工作流
        logger.info(f"用户[{user_id}]直接进入答题模式，启动答题工作流")
        quiz_response = quiz_workflow.start_quiz(user_id)
        logger.info(f"答题工作流启动完成: {quiz_response.status}, 题目信息: {json.dumps(quiz_response.quiz_info.model_dump() if hasattr(quiz_response.quiz_info, 'model_dump') else quiz_response.quiz_info)}")
        
        # 将答题工作流的响应添加到历史记录
        memory_manager.add_message(user_id, "agent", quiz_response.message, quiz_response.audio_url)
        
        # 使用答题工作流的响应作为最终响应
        return quiz_response
    
    # 生成AI回复
    logger.info(f"调用LLM生成回复，状态={session.status}")
    response = llm_client.chat_with_format(
        user_message=message,
        role_card=session.role_card.model_dump(),
        conversation_history=conversation_history,
        status=session.status,
        quiz_info=session.quiz_progress
    )
    
    logger.info(f"LLM响应状态: {response.status}, 消息: {response.message[:50]}...")
    if response.quiz_info:
        logger.info(f"包含题目信息: {json.dumps(response.quiz_info.model_dump() if hasattr(response.quiz_info, 'model_dump') else response.quiz_info)}")
    
    # 为LLM生成的回复添加语音URL
    audio_url = text_to_speech_url(response.message)
    response.audio_url = audio_url
    logger.info(f"为回复生成语音URL: {audio_url or '生成失败'}")
    
    # 添加AI回复到历史记录
    memory_manager.add_message(user_id, "agent", response.message, audio_url)
    
    # 检查状态是否变化
    if response.status != session.status:
        logger.info(f"状态变化: {session.status} -> {response.status}")
        memory_manager.update_session_status(user_id, response.status)
        
        # 如果切换到答题模式，初始化答题进度并返回QuizWorkflow的响应
        if response.status == "quiz":
            logger.info(f"用户[{user_id}]进入答题模式，启动答题工作流")
            quiz_response = quiz_workflow.start_quiz(user_id)
            logger.info(f"答题工作流启动完成: {quiz_response.status}, 题目信息: {json.dumps(quiz_response.quiz_info.model_dump() if hasattr(quiz_response.quiz_info, 'model_dump') else quiz_response.quiz_info)}")
            
            # 将答题工作流的响应添加到历史记录
            memory_manager.add_message(user_id, "agent", quiz_response.message, quiz_response.audio_url)
            
            # 使用答题工作流的响应作为最终响应
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
    
    logger.info(f"创建新会话，用户ID: {user_id}, 角色: {request.role_card_id}")
    
    # 获取角色卡数据
    role_card_data = ROLE_CARDS.get(request.role_card_id, EVIL_FROG_DOCTOR)
    role_card = RoleCard(**role_card_data)
    
    # 创建会话
    session = memory_manager.create_session(user_id, role_card)
    
    # 生成初始问候语
    logger.info(f"为用户[{user_id}]生成初始问候语")
    greeting_prompt = f"你好，我是{role_card.name}。请简短地用你的角色风格向新用户问好。"
    greeting_response = llm_client.chat(
        messages=[
            {"role": "system", "content": f"你是{role_card.name}。{role_card.background}"},
            {"role": "user", "content": greeting_prompt}
        ],
        temperature=0.7
    )
    
    greeting = greeting_response["choices"][0]["message"]["content"]
    logger.info(f"生成问候语: {greeting[:50]}...")
    
    # 为问候语生成语音URL
    audio_url = text_to_speech_url(greeting)
    logger.info(f"为问候语生成语音URL: {audio_url or '生成失败'}")
    
    # 添加问候语到历史记录
    memory_manager.add_message(user_id, "agent", greeting, audio_url)
    
    return {
        "user_id": user_id,
        "role_card": role_card.model_dump(),
        "greeting": greeting,
        "audio_url": audio_url
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
    logger.info(f"获取用户[{user_id}]历史记录，限制: {limit}条")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取历史记录
    history = memory_manager.get_conversation_history(user_id, limit)
    logger.info(f"获取到{len(history)}条历史消息")
    
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
    logger.info(f"删除用户[{user_id}]会话")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 删除会话
    memory_manager.delete_session(user_id)
    logger.info(f"用户[{user_id}]会话已删除")
    
    return {"status": "success", "message": "会话已删除"}


@router.get("/role_cards", response_model=Dict[str, Any])
async def get_role_cards():
    """
    获取所有可用的角色卡
    
    返回:
        角色卡信息
    """
    logger.info("获取所有角色卡")
    
    result = {}
    for role_id, role_data in ROLE_CARDS.items():
        result[role_id] = {
            "name": role_data["name"],
            "avatar": role_data.get("avatar", ""),
            "description": role_data.get("description", "")
        }
    
    return result


@router.delete("/history/{user_id}")
async def clear_history(user_id: str):
    """
    清除用户的聊天历史记录，但保留用户会话本身
    
    参数:
        user_id: 用户ID
        
    返回:
        操作结果
    """
    logger.info(f"清除用户[{user_id}]历史记录")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 清除历史记录但保留会话
    memory_manager.clear_conversation_history(user_id)
    logger.info(f"用户[{user_id}]历史记录已清除")
    
    return {"status": "success", "message": "历史记录已清除"}
"""
答题API路由模块

处理答题流程相关的请求，包括题目获取、答案提交和结果反馈
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
import json

from backend.app.models.response import AgentResponse, QuizInfo
from backend.app.models.question import Question
from backend.app.core.memory import memory_manager
from backend.app.core.workflow import quiz_workflow, QuizWorkflow

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("quiz_api")

router = APIRouter(prefix="/quiz", tags=["答题"])

class AnswerRequest(BaseModel):
    """答案提交请求模型"""
    user_id: str
    answer: str
    
class QuizStartRequest(BaseModel):
    """开始答题请求模型"""
    user_id: str
    total_questions: Optional[int] = 3  # 默认3题
    question_types: Optional[List[str]] = None  # 可选，指定题目类型


@router.post("/start", response_model=AgentResponse)
async def start_quiz(request: QuizStartRequest):
    """
    开始答题流程
    
    参数:
        request: 包含用户ID和答题配置
        
    返回:
        包含第一题的响应
    """
    user_id = request.user_id
    
    logger.info(f"开始答题 - 用户[{user_id}], 题目数量: {request.total_questions}")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 如果已经在答题模式中，重置
    if session.status == "quiz":
        logger.info(f"用户[{user_id}]已在答题模式，重置进度")
        memory_manager.update_quiz_progress(user_id, None)
    
    # 创建自定义工作流或使用默认工作流
    if request.total_questions != 3 or request.question_types:
        logger.info(f"创建自定义工作流 - 题目数量: {request.total_questions}, 题目类型: {request.question_types}")
        custom_workflow = QuizWorkflow(
            total_questions=request.total_questions,
            question_types=request.question_types
        )
        response = custom_workflow.start_quiz(user_id)
    else:
        logger.info("使用默认工作流")
        response = quiz_workflow.start_quiz(user_id)
    
    logger.info(f"答题启动响应 - 状态: {response.status}")
    if response.quiz_info:
        logger.info(f"第一题 - 类型: {response.quiz_info.question_type}, 题目: {response.quiz_info.question[:50]}...")
    
    return response


@router.post("/answer", response_model=AgentResponse)
async def submit_answer(request: AnswerRequest):
    """
    提交答案
    
    参数:
        request: 包含用户ID和答案
        
    返回:
        包含答案反馈和下一题的响应
    """
    user_id = request.user_id
    answer = request.answer
    
    logger.info(f"提交答案 - 用户[{user_id}], 答案: {answer}")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查是否在答题模式
    if session.status != "quiz":
        logger.warning(f"用户[{user_id}]当前不在答题模式，状态: {session.status}")
        raise HTTPException(status_code=400, detail="当前不在答题模式")
    
    # 显示当前题目信息
    if session.quiz_progress:
        logger.info(f"当前题目 - ID: {session.quiz_progress.get('current_question_id', 'unknown')}, 步骤: {session.quiz_progress.get('current_step', 0)}/{session.quiz_progress.get('total_step', 0)}")
        
        # 检查当前状态，如果已经在反馈状态，说明是请求下一题
        current_state = session.quiz_progress.get('state', '')
        if current_state == "quiz_feedback":
            logger.info(f"用户已经收到反馈，现请求获取下一题")
            return await next_question(user_id)
        elif current_state == "quiz_end":
            logger.info(f"用户已完成所有题目，请求查看结果")
            return quiz_workflow.end_quiz(user_id)
    
    # 处理答案
    logger.info(f"处理答案...")
    response = quiz_workflow.process_answer(user_id, answer)
    
    logger.info(f"答案处理响应 - 状态: {response.status}")
    if response.quiz_info:
        is_correct = response.quiz_info.user_answer == response.quiz_info.answer if hasattr(response.quiz_info, 'user_answer') and hasattr(response.quiz_info, 'answer') else None
        logger.info(f"答案评判 - 正确: {is_correct}")
        if hasattr(response.quiz_info, 'feedback') and response.quiz_info.feedback:
            logger.info(f"反馈: {response.quiz_info.feedback[:100]}...")
    
    return response


@router.get("/next/{user_id}", response_model=AgentResponse)
async def next_question(user_id: str):
    """
    获取下一题
    
    参数:
        user_id: 用户ID
        
    返回:
        包含下一题的响应或结束答题的响应
    """
    logger.info(f"获取下一题 - 用户[{user_id}]")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查是否在答题模式
    if session.status != "quiz":
        logger.warning(f"用户[{user_id}]当前不在答题模式")
        raise HTTPException(status_code=400, detail="当前不在答题模式")
    
    # 获取下一题
    logger.info(f"获取下一题...")
    response = quiz_workflow.next_question(user_id)
    
    logger.info(f"下一题响应 - 状态: {response.status}")
    if response.quiz_info:
        logger.info(f"题目信息 - 类型: {response.quiz_info.question_type}, 题目: {response.quiz_info.question[:50]}...")
    
    return response


@router.post("/end/{user_id}", response_model=AgentResponse)
async def end_quiz(user_id: str):
    """
    结束答题流程
    
    参数:
        user_id: 用户ID
        
    返回:
        包含答题结果的响应
    """
    logger.info(f"结束答题 - 用户[{user_id}]")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查是否在答题模式
    if session.status != "quiz":
        logger.warning(f"用户[{user_id}]当前不在答题模式")
        raise HTTPException(status_code=400, detail="当前不在答题模式")
    
    # 结束答题
    logger.info(f"结束答题流程...")
    response = quiz_workflow.end_quiz(user_id)
    
    logger.info(f"答题结束响应 - 状态: {response.status}, 消息: {response.message[:50]}...")
    
    return response


@router.get("/progress/{user_id}", response_model=Dict[str, Any])
async def get_quiz_progress(user_id: str):
    """
    获取答题进度
    
    参数:
        user_id: 用户ID
        
    返回:
        答题进度信息
    """
    logger.info(f"获取答题进度 - 用户[{user_id}]")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取答题进度
    if not session.quiz_progress:
        logger.info(f"用户[{user_id}]未开始答题")
        return {"status": "not_started", "message": "未开始答题"}
    
    response = {
        "status": "in_progress" if session.status == "quiz" else "completed",
        "progress": session.quiz_progress
    }
    
    logger.info(f"答题进度 - 状态: {response['status']}, 进度: {json.dumps(response['progress'])}")
    
    return response


@router.get("/history/{user_id}", response_model=List[Dict[str, Any]])
async def get_quiz_history(user_id: str):
    """
    获取用户的答题历史
    
    参数:
        user_id: 用户ID
        
    返回:
        答题历史记录
    """
    logger.info(f"获取答题历史 - 用户[{user_id}]")
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        logger.warning(f"用户[{user_id}]会话不存在")
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取答题历史
    quiz_history = memory_manager.get_quiz_history(user_id)
    
    logger.info(f"答题历史 - 记录数: {len(quiz_history)}")
    
    return quiz_history
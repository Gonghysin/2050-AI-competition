"""
答题API路由模块

处理答题流程相关的请求，包括题目获取、答案提交和结果反馈
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.app.models.response import AgentResponse, QuizInfo
from backend.app.models.question import Question
from backend.app.core.memory import memory_manager
from backend.app.core.workflow import quiz_workflow, QuizWorkflow

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
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 如果已经在答题模式中，重置
    if session.status == "quiz":
        memory_manager.update_quiz_progress(user_id, None)
    
    # 创建自定义工作流或使用默认工作流
    if request.total_questions != 3 or request.question_types:
        custom_workflow = QuizWorkflow(
            total_questions=request.total_questions,
            question_types=request.question_types
        )
        response = custom_workflow.start_quiz(user_id)
    else:
        response = quiz_workflow.start_quiz(user_id)
    
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
    
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查是否在答题模式
    if session.status != "quiz":
        raise HTTPException(status_code=400, detail="当前不在答题模式")
    
    # 处理答案
    response = quiz_workflow.process_answer(user_id, answer)
    
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
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查是否在答题模式
    if session.status != "quiz":
        raise HTTPException(status_code=400, detail="当前不在答题模式")
    
    # 获取下一题
    response = quiz_workflow.next_question(user_id)
    
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
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查是否在答题模式
    if session.status != "quiz":
        raise HTTPException(status_code=400, detail="当前不在答题模式")
    
    # 结束答题
    response = quiz_workflow.end_quiz(user_id)
    
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
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取答题进度
    if not session.quiz_progress:
        return {"status": "not_started", "message": "未开始答题"}
    
    return {
        "status": "in_progress" if session.status == "quiz" else "completed",
        "progress": session.quiz_progress
    }


@router.get("/history/{user_id}", response_model=List[Dict[str, Any]])
async def get_quiz_history(user_id: str):
    """
    获取用户的答题历史
    
    参数:
        user_id: 用户ID
        
    返回:
        答题历史记录
    """
    # 检查用户会话是否存在
    session = memory_manager.get_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 获取答题历史
    quiz_history = memory_manager.get_quiz_history(user_id)
    
    return quiz_history 
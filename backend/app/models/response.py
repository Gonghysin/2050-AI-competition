from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal, Any

class QuizInfo(BaseModel):
    """答题信息模型"""
    step: int
    total: int
    question_type: Literal["choice", "tf", "short"]
    question_id: str
    question: str
    options: Optional[List[str]] = None
    user_answer: Optional[str] = None
    answer: Optional[str] = None
    feedback: Optional[str] = None

class AgentResponse(BaseModel):
    """Agent统一响应模型"""
    status: Literal["chat", "quiz"]
    message: str
    quiz_info: Optional[QuizInfo] = None
    audio_url: Optional[str] = None  # TTS生成的语音URL
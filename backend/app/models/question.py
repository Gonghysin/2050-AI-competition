from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4

class QuestionBase(BaseModel):
    """问题基础模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    stem: str  # 题干
    type: Literal["choice", "tf", "short"]  # 题目类型
    answer: str  # 标准答案
    analysis: Optional[str] = None  # 解析
    created_at: datetime = Field(default_factory=datetime.now)
    difficulty: Optional[int] = None  # 难度等级(1-5)
    
class ChoiceQuestion(QuestionBase):
    """选择题模型"""
    type: Literal["choice"] = "choice"
    options: List[str]  # 选项列表

class TrueFalseQuestion(QuestionBase):
    """判断题模型"""
    type: Literal["tf"] = "tf"
    # 答案只能是"T"或"F"
    answer: Literal["T", "F"]

class ShortAnswerQuestion(QuestionBase):
    """简答题模型"""
    type: Literal["short"] = "short"
    
# 题目并集类型
Question = ChoiceQuestion | TrueFalseQuestion | ShortAnswerQuestion

class QuizProgress(BaseModel):
    """答题进度模型"""
    current_step: int
    total_step: int
    current_question_id: str
    correct_count: int
    questions_history: List[str] = []  # 已答题目ID列表
    
class QuestionResponse(BaseModel):
    """题目响应模型"""
    question_id: str
    user_answer: str
    is_correct: bool
    explanation: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
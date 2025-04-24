"""
问题提取器工具

提供不同类型问题的提取功能，支持选择题、判断题和简答题
"""
from typing import List, Optional, Tuple
import random

from backend.app.models.question import Question, ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
from backend.app.utils.database import questions

def extract_choice_question(user_id: str, answered_questions: List[str] = None) -> Optional[ChoiceQuestion]:
    """
    提取一个选择题
    
    参数:
        user_id: 用户ID，用于个性化题目筛选
        answered_questions: 已答过的题目ID列表，避免重复提问
        
    返回:
        选择题对象，若无可用题目则返回None
    """
    # 构建查询条件
    query = {"type": "choice"}
    if answered_questions:
        query["id"] = {"$nin": answered_questions}
    
    # 查询可用的选择题数量
    count = questions.count_documents(query)
    if count == 0:
        return None
    
    # 随机选择一道题
    skip = random.randint(0, count - 1)
    question_data = questions.find_one(query, skip=skip)
    
    if not question_data:
        return None
    
    # 转换为选择题对象
    return ChoiceQuestion(**question_data)

def extract_tf_question(user_id: str, answered_questions: List[str] = None) -> Optional[TrueFalseQuestion]:
    """
    提取一个判断题
    
    参数:
        user_id: 用户ID，用于个性化题目筛选
        answered_questions: 已答过的题目ID列表，避免重复提问
        
    返回:
        判断题对象，若无可用题目则返回None
    """
    # 构建查询条件
    query = {"type": "tf"}
    if answered_questions:
        query["id"] = {"$nin": answered_questions}
    
    # 查询可用的判断题数量
    count = questions.count_documents(query)
    if count == 0:
        return None
    
    # 随机选择一道题
    skip = random.randint(0, count - 1)
    question_data = questions.find_one(query, skip=skip)
    
    if not question_data:
        return None
    
    # 转换为判断题对象
    return TrueFalseQuestion(**question_data)

def extract_short_question(user_id: str, answered_questions: List[str] = None) -> Optional[ShortAnswerQuestion]:
    """
    提取一个简答题
    
    参数:
        user_id: 用户ID，用于个性化题目筛选
        answered_questions: 已答过的题目ID列表，避免重复提问
        
    返回:
        简答题对象，若无可用题目则返回None
    """
    # 构建查询条件
    query = {"type": "short"}
    if answered_questions:
        query["id"] = {"$nin": answered_questions}
    
    # 查询可用的简答题数量
    count = questions.count_documents(query)
    if count == 0:
        return None
    
    # 随机选择一道题
    skip = random.randint(0, count - 1)
    question_data = questions.find_one(query, skip=skip)
    
    if not question_data:
        return None
    
    # 转换为简答题对象
    return ShortAnswerQuestion(**question_data) 
"""
问题提取器工具

提供不同类型问题的提取功能，支持选择题、判断题和简答题
"""
from typing import List, Optional, Tuple
import random
import logging
import json

from backend.app.models.question import Question, ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
from backend.app.utils.database import questions

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("question_extractors")

def extract_choice_question(user_id: str, exclude_questions: List[str] = None) -> Optional[ChoiceQuestion]:
    """
    从题库中随机抽取一道选择题
    
    参数:
        user_id: 用户ID，用于个性化题目选择
        exclude_questions: 要排除的题目ID列表，通常是用户已回答过的题目
        
    返回:
        ChoiceQuestion对象，如果没有可用题目则返回None
    """
    logger.info(f"========== 开始为用户[{user_id}]抽取选择题 ==========")
    logger.info(f"函数参数 - user_id: {user_id}, exclude_questions: {exclude_questions}")
    
    # 构建查询条件
    query = {"type": "choice"}
    
    # 排除已回答的题目
    if exclude_questions and len(exclude_questions) > 0:
        logger.info(f"排除已回答的题目: {exclude_questions}")
        query["id"] = {"$nin": exclude_questions}
    
    logger.info(f"数据库查询条件: {query}")
    
    # 查询符合条件的题目数量
    count = questions.count_documents(query)
    logger.info(f"找到 {count} 道符合条件的选择题")
    
    if count == 0:
        logger.warning("没有可用的选择题")
        logger.info(f"========== 抽取选择题结束: 未找到题目 ==========")
        return None
    
    # 随机选择一道题目
    random_index = random.randint(0, count - 1)
    logger.info(f"随机选择第 {random_index} 道题目")
    
    try:
        question_data = questions.find(query).skip(random_index).limit(1)[0]
        logger.info(f"原始题目数据: {json.dumps(question_data, ensure_ascii=False, default=str)}")
        
        question = ChoiceQuestion(**question_data)
        logger.info(f"成功抽取选择题: ID={question.id}")
        logger.info(f"题干: {question.stem}")
        logger.info(f"选项: {question.options}")
        logger.info(f"答案: {question.answer}")
        logger.info(f"解析: {question.analysis}")
        logger.info(f"========== 抽取选择题结束: 成功 ==========")
        return question
    except Exception as e:
        logger.error(f"抽取选择题失败: {e}")
        logger.info(f"========== 抽取选择题结束: 失败 ==========")
        return None

def extract_tf_question(user_id: str, exclude_questions: List[str] = None) -> Optional[TrueFalseQuestion]:
    """
    从题库中随机抽取一道判断题
    
    参数:
        user_id: 用户ID，用于个性化题目选择
        exclude_questions: 要排除的题目ID列表，通常是用户已回答过的题目
        
    返回:
        TrueFalseQuestion对象，如果没有可用题目则返回None
    """
    logger.info(f"========== 开始为用户[{user_id}]抽取判断题 ==========")
    logger.info(f"函数参数 - user_id: {user_id}, exclude_questions: {exclude_questions}")
    
    # 构建查询条件
    query = {"type": "tf"}
    
    # 排除已回答的题目
    if exclude_questions and len(exclude_questions) > 0:
        logger.info(f"排除已回答的题目: {exclude_questions}")
        query["id"] = {"$nin": exclude_questions}
    
    logger.info(f"数据库查询条件: {query}")
    
    # 查询符合条件的题目数量
    count = questions.count_documents(query)
    logger.info(f"找到 {count} 道符合条件的判断题")
    
    if count == 0:
        logger.warning("没有可用的判断题")
        logger.info(f"========== 抽取判断题结束: 未找到题目 ==========")
        return None
    
    # 随机选择一道题目
    random_index = random.randint(0, count - 1)
    logger.info(f"随机选择第 {random_index} 道题目")
    
    try:
        question_data = questions.find(query).skip(random_index).limit(1)[0]
        logger.info(f"原始题目数据: {json.dumps(question_data, ensure_ascii=False, default=str)}")
        
        question = TrueFalseQuestion(**question_data)
        logger.info(f"成功抽取判断题: ID={question.id}")
        logger.info(f"题干: {question.stem}")
        logger.info(f"答案: {question.answer}")
        logger.info(f"解析: {question.analysis}")
        logger.info(f"========== 抽取判断题结束: 成功 ==========")
        return question
    except Exception as e:
        logger.error(f"抽取判断题失败: {e}")
        logger.info(f"========== 抽取判断题结束: 失败 ==========")
        return None

def extract_short_question(user_id: str, exclude_questions: List[str] = None) -> Optional[ShortAnswerQuestion]:
    """
    从题库中随机抽取一道简答题
    
    参数:
        user_id: 用户ID，用于个性化题目选择
        exclude_questions: 要排除的题目ID列表，通常是用户已回答过的题目
        
    返回:
        ShortAnswerQuestion对象，如果没有可用题目则返回None
    """
    logger.info(f"========== 开始为用户[{user_id}]抽取简答题 ==========")
    logger.info(f"函数参数 - user_id: {user_id}, exclude_questions: {exclude_questions}")
    
    # 构建查询条件
    query = {"type": "short"}
    
    # 排除已回答的题目
    if exclude_questions and len(exclude_questions) > 0:
        logger.info(f"排除已回答的题目: {exclude_questions}")
        query["id"] = {"$nin": exclude_questions}
    
    logger.info(f"数据库查询条件: {query}")
    
    # 查询符合条件的题目数量
    count = questions.count_documents(query)
    logger.info(f"找到 {count} 道符合条件的简答题")
    
    if count == 0:
        logger.warning("没有可用的简答题")
        logger.info(f"========== 抽取简答题结束: 未找到题目 ==========")
        return None
    
    # 随机选择一道题目
    random_index = random.randint(0, count - 1)
    logger.info(f"随机选择第 {random_index} 道题目")
    
    try:
        question_data = questions.find(query).skip(random_index).limit(1)[0]
        logger.info(f"原始题目数据: {json.dumps(question_data, ensure_ascii=False, default=str)}")
        
        question = ShortAnswerQuestion(**question_data)
        logger.info(f"成功抽取简答题: ID={question.id}")
        logger.info(f"题干: {question.stem}")
        logger.info(f"答案: {question.answer}")
        logger.info(f"解析: {question.analysis}")
        logger.info(f"关键词: {question.keywords if hasattr(question, 'keywords') else '无'}")
        logger.info(f"========== 抽取简答题结束: 成功 ==========")
        return question
    except Exception as e:
        logger.error(f"抽取简答题失败: {e}")
        logger.info(f"========== 抽取简答题结束: 失败 ==========")
        return None 
"""
问题评估器工具

提供不同类型问题答案的评估功能，支持选择题、判断题和简答题
"""
from typing import Dict, Any, Union, List, Tuple
import re
from difflib import SequenceMatcher

from backend.app.models.question import ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion

def evaluate_choice_answer(question: ChoiceQuestion, user_answer: str) -> Tuple[bool, float, str]:
    """
    评估选择题答案
    
    参数:
        question: 选择题对象
        user_answer: 用户答案（选项ID）
        
    返回:
        (是否正确, 得分, 反馈信息)
    """
    correct = user_answer == question.correct_option
    score = 1.0 if correct else 0.0
    
    if correct:
        feedback = "回答正确！"
    else:
        correct_option_text = next((opt.text for opt in question.options if opt.id == question.correct_option), "")
        feedback = f"回答错误。正确答案是: {question.correct_option}（{correct_option_text}）"
    
    return correct, score, feedback

def evaluate_tf_answer(question: TrueFalseQuestion, user_answer: bool) -> Tuple[bool, float, str]:
    """
    评估判断题答案
    
    参数:
        question: 判断题对象
        user_answer: 用户答案（True/False）
        
    返回:
        (是否正确, 得分, 反馈信息)
    """
    correct = user_answer == question.is_true
    score = 1.0 if correct else 0.0
    
    if correct:
        feedback = "回答正确！"
    else:
        correct_text = "正确" if question.is_true else "错误"
        feedback = f"回答错误。正确答案是: {correct_text}"
    
    return correct, score, feedback

def evaluate_short_answer(question: ShortAnswerQuestion, user_answer: str) -> Tuple[bool, float, str]:
    """
    评估简答题答案
    
    参数:
        question: 简答题对象
        user_answer: 用户答案文本
        
    返回:
        (是否正确, 得分, 反馈信息)
    """
    # 基本清理
    user_answer = user_answer.strip().lower()
    reference_answer = question.reference_answer.strip().lower()
    
    # 使用关键词匹配
    if question.keywords:
        found_keywords = 0
        total_keywords = len(question.keywords)
        
        for keyword in question.keywords:
            if keyword.lower() in user_answer:
                found_keywords += 1
        
        # 计算得分
        keyword_ratio = found_keywords / total_keywords if total_keywords > 0 else 0
        
        # 使用文本相似度作为辅助评分
        text_similarity = SequenceMatcher(None, user_answer, reference_answer).ratio()
        
        # 综合评分（权重可调整）
        score = keyword_ratio * 0.7 + text_similarity * 0.3
        
        # 判断是否正确（可根据实际需要调整阈值）
        correct = score >= 0.7
        
        # 生成反馈
        if correct:
            if score >= 0.9:
                feedback = "回答非常准确！"
            else:
                feedback = "回答基本正确。"
        else:
            missed_keywords = [k for k in question.keywords if k.lower() not in user_answer]
            if missed_keywords:
                missed_str = "、".join(missed_keywords[:3])
                if len(missed_keywords) > 3:
                    missed_str += "等"
                feedback = f"回答不够完整，可以考虑包含以下关键点：{missed_str}"
            else:
                feedback = f"回答需要改进。参考答案: {question.reference_answer}"
        
        return correct, score, feedback
    
    # 无关键词时使用文本相似度
    else:
        similarity = SequenceMatcher(None, user_answer, reference_answer).ratio()
        
        # 判断是否正确（可根据实际需要调整阈值）
        correct = similarity >= 0.7
        
        # 生成反馈
        if correct:
            if similarity >= 0.9:
                feedback = "回答非常准确！"
            else:
                feedback = "回答基本正确。"
        else:
            feedback = f"回答与参考答案差异较大。参考答案: {question.reference_answer}"
        
        return correct, similarity, feedback 
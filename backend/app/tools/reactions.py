"""
反馈生成工具

根据角色卡生成风格化的答题反馈和过渡语
"""
import random
from typing import Dict, List, Any, Optional

from backend.app.models.question import Question
from backend.app.core.memory import memory_manager

def user_correct_reaction(question: Question, user_answer: str) -> str:
    """
    生成用户回答正确时的反馈
    
    参数:
        question: 题目对象
        user_answer: 用户回答
        
    返回:
        符合角色风格的正确反馈
    """
    # 基础正确反馈模板
    correct_templates = [
        "答对了！{explanation}",
        "完全正确！{explanation}",
        "回答得很好！{explanation}",
        "太棒了，答案完全正确！{explanation}",
        "你回答得非常准确！{explanation}",
        "厉害！答案完全正确！{explanation}",
        "不错不错，{explanation}",
        "你答对了！{explanation}"
    ]
    
    # 根据题目类型获取解释
    explanation = ""
    if question.analysis:
        explanation = question.analysis
    
    # 随机选择一个模板
    template = random.choice(correct_templates)
    
    # 格式化反馈
    feedback = template.format(explanation=explanation)
    
    return feedback

def user_incorrect_reaction(question: Question, user_answer: str, explanation: str) -> str:
    """
    生成用户回答错误时的反馈
    
    参数:
        question: 题目对象
        user_answer: 用户回答
        explanation: 错误解释
        
    返回:
        符合角色风格的错误反馈
    """
    # 基础错误反馈模板
    incorrect_templates = [
        "不太对哦，{explanation}",
        "答案不正确。{explanation}",
        "这个回答有些问题。{explanation}",
        "不是这样的，{explanation}",
        "答错了哦，{explanation}",
        "不完全正确，{explanation}",
        "再想想看？{explanation}",
        "差一点点！{explanation}"
    ]
    
    # 随机选择一个模板
    template = random.choice(incorrect_templates)
    
    # 格式化反馈
    feedback = template.format(explanation=explanation)
    
    return feedback

def overall_quiz_process_reaction(quiz_progress: Dict[str, Any]) -> str:
    """
    生成答题过程中的过渡语
    
    参数:
        quiz_progress: 答题进度信息
        
    返回:
        符合角色风格的过渡语
    """
    # 过渡语模板
    transition_templates = [
        "让我们继续下一题吧！",
        "接下来是下一道题目！",
        "很好，我们继续！",
        "来看看下一个问题吧！",
        "准备好了吗？下一题来了！",
        "下一题可能会有点挑战性哦！",
        "继续前进，下面是新的问题！",
        "让我们看看你对下一题的表现如何！"
    ]
    
    # 根据当前进度生成更具体的过渡语
    current_step = quiz_progress.get("current_step", 1)
    total_step = quiz_progress.get("total_step", 5)
    correct_count = quiz_progress.get("correct_count", 0)
    
    # 计算正确率
    if current_step > 1:
        accuracy = correct_count / (current_step - 1) * 100
    else:
        accuracy = 0
    
    # 根据正确率添加不同的激励语
    if accuracy >= 80:
        encouragement = random.choice([
            "你太厉害了！",
            "保持这个水平！",
            "你回答得真棒！",
            "太出色了！"
        ])
    elif accuracy >= 50:
        encouragement = random.choice([
            "做得不错！",
            "继续加油！",
            "表现还可以！",
            "再接再厉！"
        ])
    else:
        encouragement = random.choice([
            "相信自己，你可以的！",
            "不要灰心，继续努力！",
            "多思考一下，你能行的！",
            "用心一点，下一题会更好！"
        ])
    
    # 随机选择一个过渡语模板
    transition = random.choice(transition_templates)
    
    # 根据进度添加相应的提示
    if current_step == total_step - 1:
        progress_hint = f"这是倒数第二题了！"
    elif current_step == total_step:
        progress_hint = f"这是最后一题了！加油！"
    else:
        progress_hint = f"我们已经完成了{current_step}/{total_step}题。"
    
    # 组合最终的过渡语
    final_transition = f"{encouragement} {progress_hint} {transition}"
    
    return final_transition 
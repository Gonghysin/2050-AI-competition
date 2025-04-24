"""
答题工作流模块

实现完整的答题流程状态机，包括:
1. 用户发起挑战 → status: quiz
2. 循环 N 题:
   a. 抽题 → 出题 → 等待用户回答
   b. 收到用户回答 → 判分 → 反馈 → 穿插调侃
3. 汇总成绩 → 结束答题 → status: chat
"""
from typing import Dict, List, Optional, Any, Tuple, Union
import random
from enum import Enum
import json
import uuid

from backend.app.models.question import Question, ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
from backend.app.models.response import AgentResponse, QuizInfo
from backend.app.models.user import UserSession
from backend.app.core.memory import memory_manager
from backend.app.utils.database import questions
from backend.app.tools.extractors import extract_choice_question, extract_tf_question, extract_short_question
from backend.app.tools.judge import ai_judge_correctness
from backend.app.tools.reactions import user_correct_reaction, user_incorrect_reaction, overall_quiz_process_reaction

class QuizState(str, Enum):
    """答题状态枚举"""
    INIT = "init"                      # 初始状态
    ASK = "quiz_ask"                   # 提问状态
    WAIT_ANSWER = "quiz_wait_answer"   # 等待回答
    FEEDBACK = "quiz_feedback"         # 反馈状态
    END = "quiz_end"                   # 结束状态

class QuizWorkflow:
    """答题工作流"""
    
    def __init__(self, 
                 total_questions: int = 3, 
                 question_types: List[str] = None,
                 config: Dict[str, Any] = None):
        """
        初始化答题工作流
        
        参数:
            total_questions: 答题总数，默认为3题
            question_types: 题目类型列表，如["tf", "choice", "short"]
            config: 其他配置参数
        """
        self.total_questions = total_questions
        self.question_types = question_types or ["tf", "choice", "short"]
        self.config = config or {}
        
    def start_quiz(self, user_id: str) -> AgentResponse:
        """
        开始答题流程
        
        参数:
            user_id: 用户ID
            
        返回:
            包含第一题的响应
        """
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session:
            raise ValueError(f"用户会话不存在: {user_id}")
        
        # 初始化答题进度
        quiz_progress = {
            "current_step": 1,
            "total_step": self.total_questions,
            "current_question_id": "",
            "correct_count": 0,
            "state": QuizState.INIT,
            "answered_questions": []
        }
        
        # 更新会话状态为quiz
        memory_manager.update_session_status(user_id, "quiz")
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        
        # 抽取第一题
        return self.next_question(user_id)
        
    def next_question(self, user_id: str) -> AgentResponse:
        """
        获取下一题
        
        参数:
            user_id: 用户ID
            
        返回:
            包含下一题的响应
        """
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session or not session.quiz_progress:
            raise ValueError(f"未找到用户答题进度: {user_id}")
        
        # 获取答题进度
        quiz_progress = session.quiz_progress
        current_step = quiz_progress.get("current_step", 1)
        total_step = quiz_progress.get("total_step", self.total_questions)
        
        # 检查是否已完成所有题目
        if current_step > total_step:
            return self.end_quiz(user_id)
        
        # 按固定顺序选择题目类型：1-判断题，2-选择题，3-简答题
        if current_step == 1:
            question_type = "tf"
        elif current_step == 2:
            question_type = "choice"
        else:
            question_type = "short"
        
        # 抽题
        question = self._extract_question(user_id, question_type)
        if not question:
            # 如果抽题失败，尝试其他类型
            for backup_type in self.question_types:
                if backup_type != question_type:
                    question = self._extract_question(user_id, backup_type)
                    if question:
                        question_type = backup_type
                        break
            
            # 如果所有类型都抽题失败，返回错误
            if not question:
                return AgentResponse(
                    status="quiz",
                    message=f"抱歉，题库中没有可用的题目。请稍后再试。",
                    quiz_info=None
                )
        
        # 更新答题进度
        quiz_progress["current_question_id"] = question.id
        quiz_progress["state"] = QuizState.WAIT_ANSWER
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        
        # 创建问题信息
        options = None
        if question_type == "choice" and hasattr(question, "options"):
            options = question.options
            
        # 创建回复
        quiz_info = QuizInfo(
            step=current_step,
            total=total_step,
            question_type=question_type,
            question_id=question.id,
            question=question.stem,
            options=options,
            user_answer=None,
            answer=None,
            feedback=None
        )
        
        # 根据角色风格构建问题提示语
        question_prompt = f"第{current_step}/{total_step}题：{question.stem}"
        
        return AgentResponse(
            status="quiz",
            message=question_prompt,
            quiz_info=quiz_info
        )
    
    def process_answer(self, user_id: str, user_answer: str) -> AgentResponse:
        """
        处理用户答案
        
        参数:
            user_id: 用户ID
            user_answer: 用户回答
            
        返回:
            包含反馈的响应
        """
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session or not session.quiz_progress:
            raise ValueError(f"未找到用户答题进度: {user_id}")
        
        # 获取答题进度
        quiz_progress = session.quiz_progress
        current_step = quiz_progress.get("current_step", 1)
        total_step = quiz_progress.get("total_step", self.total_questions)
        correct_count = quiz_progress.get("correct_count", 0)
        question_id = quiz_progress.get("current_question_id", "")
        
        # 获取当前题目
        question_data = questions.find_one({"id": question_id})
        if not question_data:
            return AgentResponse(
                status="quiz",
                message=f"抱歉，找不到该题目。请继续下一题。",
                quiz_info=None
            )
        
        # 根据题目类型创建题目对象
        question_type = question_data.get("type", "")
        if question_type == "choice":
            question = ChoiceQuestion(**question_data)
        elif question_type == "tf":
            question = TrueFalseQuestion(**question_data)
        else:
            question = ShortAnswerQuestion(**question_data)
        
        # 判分
        is_correct, explanation = ai_judge_correctness(user_answer, question)
        
        # 更新正确数量
        if is_correct:
            correct_count += 1
            quiz_progress["correct_count"] = correct_count
        
        # 生成反馈
        if is_correct:
            feedback = user_correct_reaction(question, user_answer)
        else:
            feedback = user_incorrect_reaction(question, user_answer, explanation)
        
        # 记录已回答的题目
        answered_questions = quiz_progress.get("answered_questions", [])
        answered_questions.append({
            "question_id": question_id,
            "user_answer": user_answer,
            "is_correct": is_correct
        })
        quiz_progress["answered_questions"] = answered_questions
        
        # 更新状态为反馈状态
        quiz_progress["state"] = QuizState.FEEDBACK
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        
        # 创建回复
        quiz_info = QuizInfo(
            step=current_step,
            total=total_step,
            question_type=question_type,
            question_id=question.id,
            question=question.stem,
            options=question.options if hasattr(question, "options") else None,
            user_answer=user_answer,
            answer=question.answer,
            feedback=feedback
        )
        
        # 准备下一题
        quiz_progress["current_step"] = current_step + 1
        quiz_progress["state"] = QuizState.ASK
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        
        # 构建反馈消息
        message = f"{feedback}\n\n"
        
        # 如果还有下一题，添加过渡语
        if current_step < total_step:
            transition = overall_quiz_process_reaction(quiz_progress)
            message += transition
        else:
            # 如果是最后一题，添加结束语并直接结束答题
            score_percent = int((correct_count / total_step) * 100)
            message += f"你已完成所有{total_step}道题目，正确率{score_percent}%！"
            
            # 直接结束答题，避免需要再调用一次next_question
            # 更新状态为聊天模式
            memory_manager.update_session_status(user_id, "chat")
            # 清空答题进度
            memory_manager.update_quiz_progress(user_id, None)
            return AgentResponse(
                status="chat",
                message=message,
                quiz_info=None
            )
        
        return AgentResponse(
            status="quiz",
            message=message,
            quiz_info=quiz_info
        )
    
    def end_quiz(self, user_id: str) -> AgentResponse:
        """
        结束答题流程
        
        参数:
            user_id: 用户ID
            
        返回:
            结束答题的响应
        """
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session or not session.quiz_progress:
            raise ValueError(f"未找到用户答题进度: {user_id}")
        
        # 获取答题进度
        quiz_progress = session.quiz_progress
        total_step = quiz_progress.get("total_step", self.total_questions)
        correct_count = quiz_progress.get("correct_count", 0)
        
        # 计算得分
        score_percent = int((correct_count / total_step) * 100)
        
        # 生成结束语
        if score_percent >= 80:
            message = f"恭喜你完成了所有{total_step}道题目，得分{score_percent}%！非常优秀！"
        elif score_percent >= 60:
            message = f"恭喜你完成了所有{total_step}道题目，得分{score_percent}%！还不错，继续加油！"
        else:
            message = f"你完成了所有{total_step}道题目，得分{score_percent}%。还需要更多练习哦！"
        
        # 更新状态为聊天模式
        memory_manager.update_session_status(user_id, "chat")
        
        # 清空答题进度
        memory_manager.update_quiz_progress(user_id, None)
        
        return AgentResponse(
            status="chat",
            message=message,
            quiz_info=None
        )
    
    def _extract_question(self, user_id: str, question_type: str) -> Optional[Question]:
        """
        抽取题目
        
        参数:
            user_id: 用户ID
            question_type: 题目类型
            
        返回:
            题目对象，如果抽题失败则返回None
        """
        try:
            if question_type == "choice":
                return extract_choice_question(user_id)
            elif question_type == "tf":
                return extract_tf_question(user_id)
            elif question_type == "short":
                return extract_short_question(user_id)
            else:
                return None
        except Exception as e:
            print(f"抽题失败: {e}")
            return None

# 创建默认答题工作流单例
quiz_workflow = QuizWorkflow() 
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
import logging

from backend.app.models.question import Question, ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
from backend.app.models.response import AgentResponse, QuizInfo
from backend.app.models.user import UserSession
from backend.app.core.memory import memory_manager
from backend.app.utils.database import questions
from backend.app.tools.extractors import extract_choice_question, extract_tf_question, extract_short_question
from backend.app.tools.judge import ai_judge_correctness
from backend.app.tools.reactions import user_correct_reaction, user_incorrect_reaction, overall_quiz_process_reaction

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("quiz_workflow")

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
        logger.info(f"工作流初始化 - 题目数量: {total_questions}, 题目类型: {self.question_types}")
        
    def start_quiz(self, user_id: str) -> AgentResponse:
        """
        开始答题流程
        
        参数:
            user_id: 用户ID
            
        返回:
            包含第一题的响应
        """

        logger.info(f"===== 开始执行 start_quiz() - 用户[{user_id}] =====")
        logger.info(f"启动答题流程 - 用户[{user_id}]")
        
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session:
            logger.error(f"用户会话不存在: {user_id}")
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
        logger.info(f"更新会话状态为quiz - 用户[{user_id}]")
        memory_manager.update_session_status(user_id, "quiz")
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        
        # 抽取第一题
        logger.info("开始抽取第一题...")
        response = self.next_question(user_id)
        logger.info(f"===== 结束执行 start_quiz() - 用户[{user_id}] =====")
        return response
        
    def next_question(self, user_id: str) -> AgentResponse:
        """
        获取下一题
        
        参数:
            user_id: 用户ID
            
        返回:
            包含下一题的响应
        """
        logger.info(f"===== 开始执行 next_question() - 用户[{user_id}] =====")
        logger.info(f"获取下一题 - 用户[{user_id}]")
        
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session or not session.quiz_progress:
            logger.error(f"未找到用户答题进度: {user_id}")
            raise ValueError(f"未找到用户答题进度: {user_id}")
        
        # 获取答题进度
        quiz_progress = session.quiz_progress
        current_step = quiz_progress.get("current_step", 1)
        total_step = quiz_progress.get("total_step", self.total_questions)
        
        logger.info(f"当前步骤: {current_step}/{total_step}")
        
        # 检查是否已完成所有题目
        if current_step > total_step:
            logger.info(f"用户[{user_id}]已完成所有题目，结束答题")
            return self.end_quiz(user_id)
        
        # 按固定顺序选择题目类型：1-判断题，2-选择题，3-简答题
        if current_step == 1:
            question_type = "tf"
        elif current_step == 2:
            question_type = "choice"
        else:
            question_type = "short"
        
        logger.info(f"当前题目类型: {question_type}")
        
        # 抽题
        logger.info(f"开始从题库抽取{question_type}类型题目...")
        question = self._extract_question(user_id, question_type)
        
        # 如果抽题失败，尝试其他类型的题目
        if not question:
            logger.warning(f"{question_type}题目抽取失败，尝试抽取其他类型题目")
            for alt_type in ["choice", "tf", "short"]:
                if alt_type != question_type:
                    logger.info(f"尝试抽取{alt_type}类型题目")
                    question = self._extract_question(user_id, alt_type)
                    if question:
                        logger.info(f"成功抽取到{alt_type}类型题目")
                        question_type = alt_type
                        break
        
        # 如果所有类型都抽题失败，生成一个默认题目
        if not question:
            logger.error("所有类型题目抽取失败，生成默认题目")
            
            if question_type == "choice":
                question = ChoiceQuestion(
                    id=f"default_{uuid.uuid4().hex[:8]}",
                    stem="Python中，以下哪个不是基本数据类型？",
                    type="choice",
                    options=["int", "float", "list", "bool"],
                    answer="C",
                    analysis="Python的基本数据类型包括int、float、bool、str，而list是复合数据类型。"
                )
            elif question_type == "tf":
                question = TrueFalseQuestion(
                    id=f"default_{uuid.uuid4().hex[:8]}",
                    stem="Python是一种编译型语言。",
                    type="tf",
                    answer="F",
                    analysis="Python是一种解释型语言，不需要编译成二进制代码就可以执行。"
                )
            else:
                question = ShortAnswerQuestion(
                    id=f"default_{uuid.uuid4().hex[:8]}",
                    stem="简述Python的优点和特性。",
                    type="short",
                    answer="Python的主要优点包括：简洁易读的语法，丰富的库和框架，跨平台特性，适合快速开发，支持多种编程范式（面向对象、函数式等）。",
                    analysis="Python因其简洁性和灵活性在数据科学、机器学习、Web开发、自动化等领域广泛应用。"
                )
                
            question_type = question.type
            logger.info(f"已生成默认{question_type}类型题目: {question.id}")
        
        # 更新答题进度
        quiz_info = {
            "step": current_step,
            "total": total_step,
            "question_id": question.id,
            "question_type": question_type,
            "question": question.stem
        }
        
        # 如果是选择题，添加选项
        if question_type == "choice":
            quiz_info["options"] = question.options
        
        # 更新进度
        quiz_progress["current_question_id"] = question.id
        quiz_progress["state"] = QuizState.WAIT_ANSWER
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        logger.info(f"用户[{user_id}]答题进度已更新: 状态={quiz_progress['state']}, 当前题目ID={question.id}")
        
        # 根据角色风格构建问题提示语
        question_prompt = f"第{current_step}/{total_step}题：{question.stem}"
        
        logger.info(f"题目准备完成，返回问题 - 步骤: {current_step}/{total_step}")
        
        # 创建响应对象
        response = AgentResponse(
            status="quiz",
            message=question_prompt,
            quiz_info=quiz_info
        )
        
        # 记录详细的返回内容
        logger.info(f"返回响应详情:")
        logger.info(f"  状态: {response.status}")
        logger.info(f"  消息: {response.message}")
        logger.info(f"  题目信息: {response.quiz_info}")
        
        logger.info(f"===== 结束执行 next_question() - 用户[{user_id}] =====")
        return response
    
    def process_answer(self, user_id: str, user_answer: str) -> AgentResponse:
        """
        处理用户答案
        
        参数:
            user_id: 用户ID
            user_answer: 用户回答
            
        返回:
            包含反馈的响应
        """
        logger.info(f"===== 开始执行 process_answer() - 用户[{user_id}] =====")
        logger.info(f"用户答案: {user_answer}")
        
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session or not session.quiz_progress:
            logger.error(f"未找到用户答题进度: {user_id}")
            raise ValueError(f"未找到用户答题进度: {user_id}")
        
        # 获取答题进度
        quiz_progress = session.quiz_progress
        current_step = quiz_progress.get("current_step", 1)
        total_step = quiz_progress.get("total_step", self.total_questions)
        correct_count = quiz_progress.get("correct_count", 0)
        question_id = quiz_progress.get("current_question_id", "")
        
        logger.info(f"当前题目ID: {question_id}, 步骤: {current_step}/{total_step}, 已答对: {correct_count}题")
        
        # 获取当前题目
        question_data = questions.find_one({"id": question_id})
        if not question_data:
            logger.error(f"找不到题目: {question_id}")
            return AgentResponse(
                status="quiz",
                message=f"抱歉，找不到该题目。请继续下一题。",
                quiz_info=None
            )
        
        # 根据题目类型创建题目对象
        question_type = question_data.get("type", "")
        logger.info(f"题目类型: {question_type}")
        
        try:
            if question_type == "choice":
                question = ChoiceQuestion(**question_data)
            elif question_type == "tf":
                question = TrueFalseQuestion(**question_data)
            elif question_type == "short":
                question = ShortAnswerQuestion(**question_data)
            else:
                logger.error(f"不支持的题目类型: {question_type}")
                return AgentResponse(
                    status="quiz",
                    message=f"抱歉，不支持的题目类型。请继续下一题。",
                    quiz_info=None
                )
                
            logger.info(f"题目对象创建成功: {question.id}")
            logger.info(f"题干: {question.stem}")
            logger.info(f"正确答案: {question.answer}")
        except Exception as e:
            logger.error(f"创建题目对象失败: {e}")
            return AgentResponse(
                status="quiz",
                message=f"抱歉，处理题目时出错。请继续下一题。",
                quiz_info=None
            )
        
        # 判断答案
        logger.info(f"开始评判答案...")
        is_correct, feedback = ai_judge_correctness(user_answer, question)
        logger.info(f"评判结果 - 是否正确: {is_correct}")
        logger.info(f"反馈信息: {feedback}")
        
        # 更新答题进度
        if is_correct:
            correct_count += 1
            quiz_progress["correct_count"] = correct_count
            logger.info(f"答案正确，当前已答对: {correct_count}题")
            
            # 生成调侃
            reaction = user_correct_reaction(question, user_answer)
            logger.info(f"已生成正确答案调侃: {reaction}")
        else:
            # 生成调侃
            reaction = user_incorrect_reaction(question, user_answer, question.analysis)
            logger.info(f"已生成错误答案调侃: {reaction}")
        
        # 记录答题历史
        answered_question = {
            "question_id": question.id,
            "question_type": question_type,
            "user_answer": user_answer,
            "correct_answer": question.answer,
            "is_correct": is_correct
        }
        
        # 添加到已答题记录
        answered_questions = quiz_progress.get("answered_questions", [])
        answered_questions.append(answered_question)
        quiz_progress["answered_questions"] = answered_questions
        logger.info(f"已添加到答题历史，当前已答题数: {len(answered_questions)}")
        
        # 准备下一题
        current_step += 1
        quiz_progress["current_step"] = current_step
        quiz_progress["state"] = QuizState.FEEDBACK
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        logger.info(f"答题进度已更新: 当前步骤={current_step}, 状态={quiz_progress['state']}")
        
        # 构建完整反馈
        quiz_info = {
            "step": current_step - 1,  # 当前已完成的步骤
            "total": total_step,
            "question_id": question.id,
            "question_type": question_type,
            "question": question.stem,
            "user_answer": user_answer,
            "answer": question.answer,
            "is_correct": is_correct,
            "feedback": feedback
        }
        
        # 如果是选择题，添加选项
        if question_type == "choice":
            quiz_info["options"] = question.options
        
        # 构造带有反馈的响应，先返回当前题目的结果，不立即切换到下一题
        feedback_message = ""
        
        # 格式化正确答案展示
        correct_answer_text = ""
        if question_type == "choice" and hasattr(question, 'options') and question.options:
            index = ord(question.answer) - ord('A')
            if 0 <= index < len(question.options):
                correct_answer_text = f"【正确答案】{question.answer}: {question.options[index]}"
        elif question_type == "tf":
            correct_answer_text = f"【正确答案】{'是' if question.answer == 'T' else '否'}"
        else:
            correct_answer_text = f"【正确答案】{question.answer}"
        
        # 根据是否答对添加不同的反馈文字
        if is_correct:
            feedback_message = f"{reaction}\n\n{feedback}\n\n{correct_answer_text}"
        else:
            feedback_message = f"{reaction}\n\n{feedback}\n\n{correct_answer_text}"
        
        # 添加提示用户继续的信息
        if current_step > total_step:
            # 如果已完成所有题目，提示用户查看总成绩
            feedback_message += "\n\n你已完成所有题目！点击\"下一题\"按钮查看最终成绩。"
            # 标记进度为答题结束，但保留当前步骤，方便下一次交互时调用end_quiz
            quiz_progress["state"] = "quiz_end"
            
            # 对于最后一道简答题，限制反馈长度不超过100字
            if question_type == "short":
                # 保留反馈开头和结尾部分，中间部分如果过长就截断
                parts = feedback_message.split("\n\n")
                if len(parts) > 2:
                    reaction_part = parts[0]  # 保留反馈的第一部分（调侃）
                    ending_part = parts[-1]  # 保留最后一部分（提示查看成绩）
                    
                    # 中间部分如果太长就截断
                    middle_text = "\n\n".join(parts[1:-1])
                    if len(middle_text) > 60:  # 预留40字给开头和结尾
                        middle_text = middle_text[:57] + "..."
                    
                    # 重新组合
                    feedback_message = f"{reaction_part}\n\n{middle_text}\n\n{ending_part}"
                    
                # 确保总长度不超过100
                if len(feedback_message) > 100:
                    feedback_message = feedback_message[:97] + "..."
        else:
            # 如果还有下一题，提示用户继续
            feedback_message += "\n\n点击\"下一题\"按钮继续答题。"
            # 标记进度为反馈状态
            quiz_progress["state"] = "quiz_feedback"
        
        # 存储状态
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        
        # 构造最终响应
        final_response = AgentResponse(
            status="quiz",
            message=feedback_message,
            quiz_info=quiz_info
        )

        # 记录返回详情
        logger.info(f"处理答案完成，最终返回响应:")
        logger.info(f"  状态: {final_response.status}")
        logger.info(f"  消息: {final_response.message[:100] if final_response.message else 'N/A'}...")
        logger.info(f"  题目信息: {final_response.quiz_info}")
        logger.info(f"===== 结束执行 process_answer() - 用户[{user_id}] =====")
        
        return final_response
    
    def end_quiz(self, user_id: str) -> AgentResponse:
        """
        结束答题流程
        
        参数:
            user_id: 用户ID
            
        返回:
            结束答题的响应
        """
        logger.info(f"===== 开始执行 end_quiz() - 用户[{user_id}] =====")
        logger.info(f"结束答题流程 - 用户[{user_id}]")
        
        # 获取用户会话
        session = memory_manager.get_session(user_id)
        if not session or not session.quiz_progress:
            logger.error(f"未找到用户答题进度: {user_id}")
            raise ValueError(f"未找到用户答题进度: {user_id}")
        
        # 获取答题进度
        quiz_progress = session.quiz_progress
        total_step = quiz_progress.get("total_step", self.total_questions)
        correct_count = quiz_progress.get("correct_count", 0)
        
        # 计算得分
        score_percent = int((correct_count / total_step) * 100)
        logger.info(f"答题得分 - 正确: {correct_count}/{total_step}, 得分: {score_percent}%")
        
        # 生成结束语
        if score_percent >= 80:
            logger.info("生成优秀级别结束语")
            message = f"恭喜你完成了所有{total_step}道题目，得分{score_percent}%！非常优秀！"
        elif score_percent >= 60:
            logger.info("生成良好级别结束语")
            message = f"恭喜你完成了所有{total_step}道题目，得分{score_percent}%！还不错，继续加油！"
        else:
            logger.info("生成一般级别结束语")
            message = f"你完成了所有{total_step}道题目，得分{score_percent}%。还需要更多练习哦！"
        
        # 更新状态为聊天模式
        logger.info(f"更新用户[{user_id}]状态为聊天模式")
        memory_manager.update_session_status(user_id, "chat")
        
        # 清空答题进度
        logger.info(f"清空用户[{user_id}]答题进度")
        memory_manager.update_quiz_progress(user_id, None)
        
        response = AgentResponse(
            status="chat",
            message=message,
            quiz_info=None
        )
        
        logger.info(f"===== 结束执行 end_quiz() - 用户[{user_id}] =====")
        return response
    
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
            logger.info(f"===== 开始执行 _extract_question() - 用户[{user_id}], 题型[{question_type}] =====")
            
            # 获取已答过的题目ID
            session = memory_manager.get_session(user_id)
            answered_questions = []
            if session and session.quiz_progress and "answered_questions" in session.quiz_progress:
                for answered in session.quiz_progress["answered_questions"]:
                    if "question_id" in answered:
                        answered_questions.append(answered["question_id"])
            
            if answered_questions:
                logger.info(f"已回答过的题目: {answered_questions}")
            
            # 根据题目类型调用不同的提取函数
            logger.info(f"调用{question_type}题目提取函数")
            if question_type == "choice":
                question = extract_choice_question(user_id, answered_questions)
            elif question_type == "tf":
                question = extract_tf_question(user_id, answered_questions)
            elif question_type == "short":
                question = extract_short_question(user_id, answered_questions)
            else:
                logger.error(f"不支持的题目类型: {question_type}")
                return None
            
            # 记录提取结果
            if question:
                logger.info(f"题目提取成功 - 详细信息:")
                logger.info(f"  题目ID: {question.id}")
                logger.info(f"  题目类型: {question.type}")
                logger.info(f"  题干: {question.stem}")
                if hasattr(question, 'options') and question.options:
                    logger.info(f"  选项: {question.options}")
                logger.info(f"  答案: {question.answer}")
                if question.analysis:
                    logger.info(f"  解析: {question.analysis}")
                logger.info(f"题目抽取成功完成")
                logger.info(f"===== 结束执行 _extract_question() - 用户[{user_id}], 题型[{question_type}] =====")
                return question
            else:
                logger.warning(f"抽取{question_type}类型题目失败，返回None")
                logger.info(f"===== 结束执行 _extract_question() - 用户[{user_id}], 题型[{question_type}] =====")
                return None
        except Exception as e:
            logger.error(f"抽题失败: {e}")
            logger.error(f"错误详情:", exc_info=True)
            logger.info(f"===== 结束执行 _extract_question() - 用户[{user_id}], 题型[{question_type}] (异常) =====")
            return None

# 创建默认答题工作流单例
logger.info("创建默认答题工作流单例")
quiz_workflow = QuizWorkflow()
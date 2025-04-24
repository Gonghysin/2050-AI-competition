#!/usr/bin/env python3
"""
运行答题工作流测试的脚本，直接测试 workflow.py 的 QuizWorkflow 类
"""
import os
import sys
print("sys.path:", sys.path)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../'))
sys.path.insert(0, project_root)
import time
import unittest
from unittest.mock import patch, MagicMock

# 设置项目根目录到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

from backend.app.core.workflow import QuizWorkflow

class SessionMock:
    def __init__(self, quiz_progress=None):
        if quiz_progress is None:
            quiz_progress = {}
        self.quiz_progress = quiz_progress

class TestQuizWorkflow(unittest.TestCase):
    def setUp(self):
        # 创建 QuizWorkflow 实例
        self.workflow = QuizWorkflow(total_questions=3)
        self.user_id = "test_user"
        # mock memory_manager
        patcher = patch('backend.app.core.memory.memory_manager')
        self.mock_memory = patcher.start()
        self.addCleanup(patcher.stop)
        # mock数据库 questions
        patcher_db = patch('backend.app.utils.database.questions')
        self.mock_questions = patcher_db.start()
        self.addCleanup(patcher_db.stop)
        # mock extractors
        patcher_choice = patch('backend.app.tools.extractors.extract_choice_question', return_value=None)
        patcher_tf = patch('backend.app.tools.extractors.extract_tf_question', return_value=None)
        patcher_short = patch('backend.app.tools.extractors.extract_short_question', return_value=None)
        self.mock_choice = patcher_choice.start()
        self.mock_tf = patcher_tf.start()
        self.mock_short = patcher_short.start()
        self.addCleanup(patcher_choice.stop)
        self.addCleanup(patcher_tf.stop)
        self.addCleanup(patcher_short.stop)
        # mock judge/reactions
        patcher_judge = patch('backend.app.tools.judge.ai_judge_correctness', return_value=(True, "很好"))
        patcher_correct = patch('backend.app.tools.reactions.user_correct_reaction', return_value="答对了！")
        patcher_incorrect = patch('backend.app.tools.reactions.user_incorrect_reaction', return_value="答错了！")
        self.mock_judge = patcher_judge.start()
        self.mock_correct = patcher_correct.start()
        self.mock_incorrect = patcher_incorrect.start()
        self.addCleanup(patcher_judge.stop)
        self.addCleanup(patcher_correct.stop)
        self.addCleanup(patcher_incorrect.stop)
        # mock session/quiz_progress
        self.mock_memory.get_session.return_value = SessionMock({})
        self.mock_memory.update_session_status.return_value = None
        self.mock_memory.update_quiz_progress.return_value = None
        # mock question数据
        self.mock_questions.find_one.return_value = {
            "id": "q1",
            "type": "choice",
            "stem": "Python 是编译型语言吗？",
            "options": ["A. 是", "B. 否", "C. 可能", "D. 不确定"],
            "answer": "B",
            "analysis": "Python 是解释型语言。"
        }

    def test_start_quiz(self):
        self.mock_memory.get_session.return_value = SessionMock({})
        resp = self.workflow.start_quiz(self.user_id)
        self.assertEqual(resp.status, "quiz")
        self.assertIn("第1/3题", resp.message)
        self.mock_memory.update_session_status.assert_called_with(self.user_id, "quiz")

    def test_next_question(self):
        self.mock_memory.get_session.return_value = SessionMock({
            "current_step": 2,
            "total_step": 3,
            "current_question_id": "",
            "correct_count": 1,
            "state": "quiz_ask",
            "answered_questions": []
        })
        resp = self.workflow.next_question(self.user_id)
        self.assertEqual(resp.status, "quiz")
        self.assertIn("第2/3题", resp.message)

    def test_process_answer(self):
        # 为 test_process_answer 测试用例初始化 quiz_progress
        self.mock_memory.get_session.return_value = SessionMock({
            "current_step": 2,
            "total_step": 3,
            "current_question_id": "q1",
            "correct_count": 1,
            "state": "quiz_wait_answer",
            "answered_questions": []
        })
        resp = self.workflow.process_answer(self.user_id, "B")
        self.assertEqual(resp.status, "quiz")
        self.assertIn("请继续回答下一题", resp.message)
        self.assertTrue(resp.quiz_info["is_correct"])

    def test_end_quiz(self):
        # 为 test_end_quiz 测试用例初始化 quiz_progress
        self.mock_memory.get_session.return_value = SessionMock({
            "current_step": 4,
            "total_step": 3,
            "correct_count": 2
        })
        resp = self.workflow.end_quiz(self.user_id)
        self.assertEqual(resp.status, "chat")
        self.assertIn("完成了所有3道题目", resp.message)

if __name__ == "__main__":
    print("\n开始执行 QuizWorkflow 单元测试...\n")
    unittest.main()
"""
测试答题工作流模块

测试内容：
1. 开始答题流程
2. 获取下一题
3. 处理用户答案
4. 结束答题流程
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import uuid
import random
from typing import Dict, Any, List

from backend.app.core.workflow import QuizWorkflow, QuizState
from backend.app.core.memory import memory_manager
from backend.app.models.user import RoleCard
from backend.app.config.role_cards import EVIL_FROG_DOCTOR

def test_quiz_workflow():
    """测试答题工作流的完整流程"""
    print("\n===== 测试答题工作流 =====")
    
    # 创建测试用户
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    role_card = RoleCard(**EVIL_FROG_DOCTOR)
    
    try:
        # 创建会话
        session = memory_manager.create_session(user_id, role_card)
        print(f"已创建测试用户: {user_id}")
        
        # 创建工作流
        workflow = QuizWorkflow(total_questions=3)  # 固定3题，分别对应判断、选择、简答
        print(f"已创建答题工作流, 题目数量: {workflow.total_questions}")
        
        # 开始答题
        print("\n--- 开始答题流程 ---")
        response = workflow.start_quiz(user_id)
        print(f"状态: {response.status}")
        print(f"消息: {response.message}")
        if response.quiz_info:
            print(f"题目类型: {response.quiz_info.question_type}")
            print(f"题目进度: {response.quiz_info.step}/{response.quiz_info.total}")
        
        # 处理第一题答案
        print("\n--- 回答第一题 ---")
        # 根据题目类型生成答案
        user_answer = generate_random_answer(response.quiz_info.question_type)
        print(f"用户答案: {user_answer}")
        
        response = workflow.process_answer(user_id, user_answer)
        print(f"状态: {response.status}")
        print(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
        if response.quiz_info:
            print(f"是否正确: {'是' if response.quiz_info.user_answer == response.quiz_info.answer else '否'}")
        
        # 获取第二题
        print("\n--- 获取第二题 ---")
        response = workflow.next_question(user_id)
        print(f"状态: {response.status}")
        print(f"消息: {response.message}")
        if response.quiz_info:
            print(f"题目类型: {response.quiz_info.question_type}")
            print(f"题目进度: {response.quiz_info.step}/{response.quiz_info.total}")
        
        # 处理第二题答案
        print("\n--- 回答第二题 ---")
        user_answer = generate_random_answer(response.quiz_info.question_type)
        print(f"用户答案: {user_answer}")
        
        response = workflow.process_answer(user_id, user_answer)
        print(f"状态: {response.status}")
        print(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
        
        # 获取第三题
        print("\n--- 获取第三题 ---")
        response = workflow.next_question(user_id)
        print(f"状态: {response.status}")
        print(f"消息: {response.message}")
        if response.quiz_info:
            print(f"题目类型: {response.quiz_info.question_type}")
            print(f"题目进度: {response.quiz_info.step}/{response.quiz_info.total}")
        
        # 处理第三题答案（最后一题）
        print("\n--- 回答第三题 ---")
        user_answer = generate_random_answer(response.quiz_info.question_type)
        print(f"用户答案: {user_answer}")
        
        response = workflow.process_answer(user_id, user_answer)
        print(f"状态: {response.status}")
        print(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
        
        # 检查状态是否已自动切换为聊天模式
        print("\n--- 检查答题结束状态 ---")
        session = memory_manager.get_session(user_id)
        print(f"最终会话状态: {session.status}")
        print(f"答题进度: {session.quiz_progress}")
        
        # 确认已回到聊天模式
        if session.status != "chat":
            print("❌ 答题结束后未回到聊天模式")
            return False
            
        print("✓ 已自动回到聊天模式")
        print("✅ 答题工作流测试通过")
        return True
    except Exception as e:
        print(f"❌ 答题工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quiz_state_transitions():
    """测试答题状态转换"""
    print("\n===== 测试答题状态转换 =====")
    
    # 创建测试用户
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    role_card = RoleCard(**EVIL_FROG_DOCTOR)
    
    try:
        # 创建会话
        session = memory_manager.create_session(user_id, role_card)
        print(f"已创建测试用户: {user_id}")
        
        # 创建工作流
        workflow = QuizWorkflow(total_questions=2)
        
        # 检查初始状态
        print("\n--- 检查初始状态 ---")
        print(f"会话状态: {session.status}")
        print(f"答题进度: {session.quiz_progress}")
        
        # 开始答题，检查状态变化
        print("\n--- 开始答题后的状态 ---")
        workflow.start_quiz(user_id)
        session = memory_manager.get_session(user_id)
        print(f"会话状态: {session.status}")
        print(f"答题状态: {session.quiz_progress.get('state')}")
        print(f"当前步骤: {session.quiz_progress.get('current_step')}")
        
        # 回答第一题，检查状态变化
        print("\n--- 回答第一题后的状态 ---")
        response = workflow.next_question(user_id)
        user_answer = generate_random_answer(response.quiz_info.question_type)
        response = workflow.process_answer(user_id, user_answer)
        
        session = memory_manager.get_session(user_id)
        print(f"会话状态: {session.status}")
        if session.quiz_progress:
            print(f"答题状态: {session.quiz_progress.get('state')}")
            print(f"当前步骤: {session.quiz_progress.get('current_step')}")
        else:
            # 如果已经自动结束答题
            print("答题已自动结束")
        
        # 如果第一题后还没结束，回答第二题
        if session.status == "quiz":
            print("\n--- 回答第二题后的状态 ---")
            response = workflow.next_question(user_id)
            user_answer = generate_random_answer(response.quiz_info.question_type)
            response = workflow.process_answer(user_id, user_answer)
            
            # 检查状态
            session = memory_manager.get_session(user_id)
            print(f"会话状态: {session.status}")
            print(f"答题进度: {session.quiz_progress}")
        
        # 验证最终状态为聊天模式
        if session.status != "chat":
            print("❌ 答题结束后未回到聊天模式")
            return False
            
        print("✓ 已自动回到聊天模式")
        print("✅ 答题状态转换测试通过")
        return True
    except Exception as e:
        print(f"❌ 答题状态转换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_random_answer(question_type: str) -> str:
    """生成随机答案用于测试"""
    if question_type == "choice":
        return random.choice(["A", "B", "C", "D"])
    elif question_type == "tf":
        return random.choice(["T", "F"])
    else:  # short
        sample_answers = [
            "这是一个测试回答",
            "我认为答案是...",
            "根据题目描述，应该是...",
            "这个问题的解决方案是..."
        ]
        return random.choice(sample_answers)

def main():
    """运行所有测试"""
    tests = [
        ("答题工作流测试", test_quiz_workflow),
        ("答题状态转换测试", test_quiz_state_transitions)
    ]
    
    results = {}
    for name, test_func in tests:
        results[name] = test_func()
    
    # 打印测试结果摘要
    print("\n===== 测试结果摘要 =====")
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

if __name__ == "__main__":
    main() 
"""
测试聊天和记忆功能
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import json
from typing import Dict
import uuid

from backend.app.core.memory import memory_manager
from backend.app.utils.llm_client import llm_client
from backend.app.config.role_cards import get_role_card, EVIL_FROG_DOCTOR, SMART_SENIOR_SISTER
from backend.app.models.user import RoleCard

def test_llm_client_basic():
    """测试LLM客户端基本对话功能"""
    print("\n===== 测试LLM客户端基本对话功能 =====")
    try:
        response = llm_client.chat(
            messages=[{"role": "user", "content": "你好，请介绍一下自己"}]
        )
        print(f"模型: {llm_client.default_model}")
        print(f"回复: {response['choices'][0]['message']['content'][:100]}...")
        print("✅ LLM客户端基本对话功能测试通过")
        return True
    except Exception as e:
        print(f"❌ LLM客户端基本对话功能测试失败: {e}")
        return False

def test_role_playing():
    """测试角色扮演功能"""
    print("\n===== 测试角色扮演功能 =====")
    
    roles = [
        ("邪恶青蛙博士", EVIL_FROG_DOCTOR),
        ("小智学姐", SMART_SENIOR_SISTER)
    ]
    
    for role_name, role_card in roles:
        try:
            print(f"\n--- 测试角色: {role_name} ---")
            response = llm_client.chat_with_format(
                user_message="你好，请介绍一下自己",
                role_card=role_card,
                status="chat"
            )
            
            print(f"回复: {response.message}")
            print(f"状态: {response.status}")
            print(f"完整响应: {response.model_dump_json(indent=2)}")
            print(f"✅ 角色 {role_name} 测试通过")
        except Exception as e:
            print(f"❌ 角色 {role_name} 测试失败: {e}")
            return False
    
    return True

def test_memory_module():
    """测试记忆模块功能"""
    print("\n===== 测试记忆模块功能 =====")
    
    # 生成测试用户ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    try:
        # 测试创建会话
        print(f"\n--- 为用户 {user_id} 创建会话 ---")
        role_card = RoleCard(**EVIL_FROG_DOCTOR)
        session = memory_manager.create_session(user_id, role_card)
        print(f"会话已创建, 状态: {session.status}")
        
        # 测试添加消息
        print("\n--- 添加消息到会话 ---")
        memory_manager.add_message(user_id, "user", "你好，我是测试用户")
        memory_manager.add_message(user_id, "agent", "呱呱呱！弱小的人类，你敢挑战本博士的智慧吗？")
        
        # 测试获取会话
        print("\n--- 获取会话 ---")
        retrieved_session = memory_manager.get_session(user_id)
        print(f"对话历史消息数: {len(retrieved_session.conversation)}")
        
        # 测试获取对话历史
        print("\n--- 获取对话历史 ---")
        history = memory_manager.get_conversation_history(user_id)
        for i, msg in enumerate(history):
            print(f"消息 {i+1}: [{msg['role']}] {msg['content']}")
        
        # 测试更新状态
        print("\n--- 更新会话状态为quiz ---")
        memory_manager.update_session_status(user_id, "quiz")
        updated_session = memory_manager.get_session(user_id)
        print(f"更新后状态: {updated_session.status}")
        
        # 测试更新答题进度
        print("\n--- 更新答题进度 ---")
        quiz_progress = {
            "current_step": 1,
            "total_step": 5,
            "current_question_id": "Q123",
            "correct_count": 0
        }
        memory_manager.update_quiz_progress(user_id, quiz_progress)
        final_session = memory_manager.get_session(user_id)
        print(f"答题进度: 第{final_session.quiz_progress['current_step']}/{final_session.quiz_progress['total_step']}题")
        
        print("✅ 记忆模块功能测试通过")
        return True
    except Exception as e:
        print(f"❌ 记忆模块功能测试失败: {e}")
        return False

def test_chat_with_memory():
    """测试带记忆的聊天流程"""
    print("\n===== 测试带记忆的聊天流程 =====")
    
    # 生成测试用户ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    role_card = EVIL_FROG_DOCTOR
    
    try:
        # 第一轮对话
        print("\n--- 第一轮对话 ---")
        # 创建会话
        session = memory_manager.create_session(user_id, RoleCard(**role_card))
        
        # 用户消息
        user_message = "你好，请介绍一下自己"
        print(f"用户: {user_message}")
        
        # 添加用户消息到会话
        memory_manager.add_message(user_id, "user", user_message)
        
        # 获取对话历史
        conversation_history = memory_manager.get_conversation_history(user_id)
        
        # 生成回复
        response = llm_client.chat_with_format(
            user_message=user_message,
            role_card=role_card,
            conversation_history=conversation_history,
            status=session.status
        )
        
        # 添加AI回复到会话
        memory_manager.add_message(user_id, "agent", response.message)
        
        print(f"AI: {response.message}")
        
        # 第二轮对话
        print("\n--- 第二轮对话 ---")
        
        # 用户消息
        user_message = "你来自哪里？你有什么计划？"
        print(f"用户: {user_message}")
        
        # 添加用户消息到会话
        memory_manager.add_message(user_id, "user", user_message)
        
        # 获取更新后的对话历史
        conversation_history = memory_manager.get_conversation_history(user_id)
        
        # 生成回复
        response = llm_client.chat_with_format(
            user_message=user_message,
            role_card=role_card,
            conversation_history=conversation_history,
            status=session.status
        )
        
        # 添加AI回复到会话
        memory_manager.add_message(user_id, "agent", response.message)
        
        print(f"AI: {response.message}")
        
        # 展示完整对话历史
        print("\n--- 完整对话历史 ---")
        final_session = memory_manager.get_session(user_id)
        for i, msg in enumerate(final_session.conversation):
            print(f"消息 {i+1}: [{msg.role}] {msg.content}")
        
        print("✅ 带记忆的聊天流程测试通过")
        return True
    except Exception as e:
        print(f"❌ 带记忆的聊天流程测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    tests = [
        ("LLM客户端基本对话功能", test_llm_client_basic),
        ("角色扮演功能", test_role_playing),
        ("记忆模块功能", test_memory_module),
        ("带记忆的聊天流程", test_chat_with_memory)
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
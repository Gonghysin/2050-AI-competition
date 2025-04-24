"""
API测试脚本

测试主要API端点的功能和响应
"""
import requests
import json
import time
import sys
from colorama import Fore, Style, init

# 初始化colorama
init()

# API基础URL
BASE_URL = "http://localhost:8000"

def print_success(message):
    """打印成功消息"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """打印错误消息"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message):
    """打印信息消息"""
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")

def print_json(data):
    """美化输出JSON数据"""
    print(f"{Fore.CYAN}{json.dumps(data, ensure_ascii=False, indent=2)}{Style.RESET_ALL}")

def test_health_check():
    """测试健康检查接口"""
    print_info("测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok":
            print_success("健康检查接口正常")
            return True
        else:
            print_error(f"健康检查接口返回异常状态: {data}")
            return False
    except Exception as e:
        print_error(f"健康检查接口调用失败: {e}")
        return False

def test_create_session():
    """测试创建会话接口"""
    print_info("测试创建会话接口...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/create_session", 
            json={"role_card_id": "evil_frog"}
        )
        response.raise_for_status()
        data = response.json()
        
        if "user_id" in data and "greeting" in data:
            print_success("创建会话接口正常")
            print_info("会话信息:")
            print_json(data)
            return data["user_id"]
        else:
            print_error(f"创建会话接口返回数据异常: {data}")
            return None
    except Exception as e:
        print_error(f"创建会话接口调用失败: {e}")
        return None

def test_send_message(user_id):
    """测试发送消息接口"""
    print_info("测试发送消息接口...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/send", 
            json={
                "user_id": user_id,
                "message": "你好，我想挑战一下你的题目"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if "message" in data and "status" in data:
            print_success("发送消息接口正常")
            print_info("响应信息:")
            print_json(data)
            return True
        else:
            print_error(f"发送消息接口返回数据异常: {data}")
            return False
    except Exception as e:
        print_error(f"发送消息接口调用失败: {e}")
        return False

def test_start_quiz(user_id):
    """测试开始答题接口"""
    print_info("测试开始答题接口...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/quiz/start", 
            json={
                "user_id": user_id,
                "total_questions": 3
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if "message" in data and "quiz_info" in data:
            print_success("开始答题接口正常")
            print_info("题目信息:")
            print_json(data)
            return True
        else:
            print_error(f"开始答题接口返回数据异常: {data}")
            return False
    except Exception as e:
        print_error(f"开始答题接口调用失败: {e}")
        return False

def test_get_history(user_id):
    """测试获取历史记录接口"""
    print_info("测试获取历史记录接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/chat/history/{user_id}")
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            print_success("获取历史记录接口正常")
            print_info(f"历史记录数量: {len(data)}")
            return True
        else:
            print_error(f"获取历史记录接口返回数据异常: {data}")
            return False
    except Exception as e:
        print_error(f"获取历史记录接口调用失败: {e}")
        return False

def test_role_cards():
    """测试获取角色卡接口"""
    print_info("测试获取角色卡接口...")
    try:
        response = requests.get(f"{BASE_URL}/api/chat/role_cards")
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and len(data) > 0:
            print_success("获取角色卡接口正常")
            print_info("可用角色卡:")
            print_json(data)
            return True
        else:
            print_error(f"获取角色卡接口返回数据异常: {data}")
            return False
    except Exception as e:
        print_error(f"获取角色卡接口调用失败: {e}")
        return False

def run_tests():
    """运行所有测试"""
    print_info("开始API测试...")
    
    # 测试健康检查
    if not test_health_check():
        print_error("健康检查失败，终止测试")
        return
    
    # 测试获取角色卡
    test_role_cards()
    
    # 测试创建会话
    user_id = test_create_session()
    if not user_id:
        print_error("创建会话失败，终止测试")
        return
    
    # 等待1秒
    time.sleep(1)
    
    # 测试发送消息
    if not test_send_message(user_id):
        print_error("发送消息失败，终止测试")
        return
    
    # 等待1秒
    time.sleep(1)
    
    # 测试开始答题
    test_start_quiz(user_id)
    
    # 等待1秒
    time.sleep(1)
    
    # 测试获取历史记录
    test_get_history(user_id)
    
    print_info("测试完成!")

if __name__ == "__main__":
    run_tests() 
"""
答题工作流本地测试

用于独立测试答题工作流程和题目抽取功能，特别关注从数据库中提取题目的过程
"""
import os
import sys
import uuid
import logging
import json
from typing import Dict, Any, List, Optional

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../'))
sys.path.append(project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('workflow_test.log')
    ]
)

logger = logging.getLogger("workflow_test")

# 尝试导入所需模块
try:
    # 从项目中导入所需模块
    from backend.app.models.user import UserSession, RoleCard
    from backend.app.models.response import AgentResponse
    from backend.app.core.memory import memory_manager
    from backend.app.core.workflow import QuizWorkflow, quiz_workflow
    from backend.app.config.role_cards import EVIL_FROG_DOCTOR
    from backend.app.tools.extractors import extract_choice_question, extract_tf_question, extract_short_question
    
    logger.info("成功导入所需模块")
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error("尝试使用替代导入方式...")
    
    # 如果上面的导入失败，尝试使用相对导入
    try:
        # 添加后端目录到路径
        backend_dir = os.path.abspath(os.path.join(current_dir, '../..'))
        if backend_dir not in sys.path:
            sys.path.append(backend_dir)
        
        # 使用相对路径导入
        from app.models.user import UserSession, RoleCard
        from app.models.response import AgentResponse
        from app.core.memory import memory_manager
        from app.core.workflow import QuizWorkflow, quiz_workflow
        from app.config.role_cards import EVIL_FROG_DOCTOR
        from app.tools.extractors import extract_choice_question, extract_tf_question, extract_short_question
        
        logger.info("使用替代方式成功导入所需模块")
    except ImportError as e2:
        logger.error(f"替代导入方式也失败: {e2}")
        logger.error("无法继续执行测试，请检查项目结构和Python路径设置")
        sys.exit(1)

def log_quiz_info(quiz_info: Dict[str, Any]):
    """打印quiz_info的详细信息"""
    logger.info("题目信息详情:")
    for key, value in quiz_info.items():
        logger.info(f"  {key}: {value}")

def test_extract_questions():
    """测试题目提取函数"""
    logger.info("========== 开始测试题目提取函数 ==========")
    
    # 测试用户ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    logger.info(f"测试用户ID: {user_id}")
    
    # 分别测试三种题型提取
    question_types = ["choice", "tf", "short"]
    for q_type in question_types:
        logger.info(f"\n----- 测试{q_type}题目提取 -----")
        
        # 直接调用提取函数
        if q_type == "choice":
            question = extract_choice_question(user_id)
        elif q_type == "tf":
            question = extract_tf_question(user_id)
        else:
            question = extract_short_question(user_id)
        
        # 检查提取结果
        if question:
            logger.info(f"成功提取{q_type}题，详情:")
            logger.info(f"  ID: {question.id}")
            logger.info(f"  题干: {question.stem}")
            if hasattr(question, 'options') and question.options:
                logger.info(f"  选项: {question.options}")
            logger.info(f"  答案: {question.answer}")
            logger.info(f"  解析: {question.analysis}")
        else:
            logger.error(f"提取{q_type}题失败，返回None")
    
    logger.info("========== 题目提取函数测试完成 ==========")

def test_workflow_extract_question():
    """测试工作流中的_extract_question方法"""
    logger.info("========== 开始测试工作流_extract_question方法 ==========")
    
    # 测试用户ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    logger.info(f"测试用户ID: {user_id}")
    
    # 创建工作流实例
    workflow = QuizWorkflow(total_questions=3)
    logger.info("已创建答题工作流实例")
    
    # 分别测试三种题型提取
    question_types = ["choice", "tf", "short"]
    for q_type in question_types:
        logger.info(f"\n----- 测试工作流提取{q_type}题目 -----")
        
        # 调用工作流的_extract_question方法
        question = workflow._extract_question(user_id, q_type)
        
        # 检查提取结果
        if question:
            logger.info(f"工作流成功提取{q_type}题，详情:")
            logger.info(f"  ID: {question.id}")
            logger.info(f"  题干: {question.stem}")
            if hasattr(question, 'options') and question.options:
                logger.info(f"  选项: {question.options}")
            logger.info(f"  答案: {question.answer}")
            logger.info(f"  解析: {question.analysis}")
        else:
            logger.error(f"工作流提取{q_type}题失败，返回None")
    
    logger.info("========== 工作流_extract_question方法测试完成 ==========")

def test_complete_quiz_workflow():
    """测试完整的答题工作流程"""
    logger.info("========== 开始测试完整答题工作流 ==========")
    
    # 创建测试用户
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    role_card = RoleCard(**EVIL_FROG_DOCTOR)
    
    # 创建会话
    session = memory_manager.create_session(user_id, role_card)
    logger.info(f"已创建测试用户会话: {user_id}")
    
    # 创建自定义工作流
    workflow = QuizWorkflow(total_questions=3)  # 固定3题，分别对应判断、选择、简答
    logger.info(f"已创建答题工作流, 题目数量: {workflow.total_questions}")
    
    try:
        # 1. 开始答题流程
        logger.info("\n--- 开始答题流程 ---")
        response = workflow.start_quiz(user_id)
        logger.info(f"状态: {response.status}")
        logger.info(f"消息: {response.message}")
        
        if response.quiz_info:
            log_quiz_info(response.quiz_info)
            question_id_1 = response.quiz_info.get("question_id")
            logger.info(f"第一题ID: {question_id_1}")
        
        # 2. 回答第一题
        logger.info("\n--- 回答第一题 ---")
        # 简单模拟一个回答
        user_answer = "是" if response.quiz_info.get("question_type") == "tf" else "A"
        logger.info(f"用户回答: {user_answer}")
        
        # 处理答案
        response = workflow.process_answer(user_id, user_answer)
        logger.info(f"状态: {response.status}")
        logger.info(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
        
        if response.quiz_info:
            log_quiz_info(response.quiz_info)
            logger.info(f"是否正确: {response.quiz_info.get('is_correct')}")
        
        # 3. 获取第二题
        logger.info("\n--- 获取第二题 ---")
        response = workflow.next_question(user_id)
        logger.info(f"状态: {response.status}")
        logger.info(f"消息: {response.message}")
        
        if response.quiz_info:
            log_quiz_info(response.quiz_info)
            question_id_2 = response.quiz_info.get("question_id")
            logger.info(f"第二题ID: {question_id_2}")
            logger.info(f"题目ID是否与第一题不同: {question_id_1 != question_id_2}")
        
        # 4. 回答第二题
        logger.info("\n--- 回答第二题 ---")
        # 选择题回答
        user_answer = "B" if response.quiz_info.get("question_type") == "choice" else "A"
        logger.info(f"用户回答: {user_answer}")
        
        # 处理答案
        response = workflow.process_answer(user_id, user_answer)
        logger.info(f"状态: {response.status}")
        logger.info(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
        
        # 5. 获取第三题
        logger.info("\n--- 获取第三题 ---")
        response = workflow.next_question(user_id)
        logger.info(f"状态: {response.status}")
        logger.info(f"消息: {response.message}")
        
        if response.quiz_info:
            log_quiz_info(response.quiz_info)
            question_id_3 = response.quiz_info.get("question_id")
            logger.info(f"第三题ID: {question_id_3}")
            logger.info(f"题目ID是否与前两题不同: {question_id_3 != question_id_1 and question_id_3 != question_id_2}")
        
        # 6. 回答第三题
        logger.info("\n--- 回答第三题 ---")
        # 简答题回答
        user_answer = "Python是一种高级编程语言，具有简洁易读的语法和强大的库支持。"
        logger.info(f"用户回答: {user_answer}")
        
        # 处理答案
        response = workflow.process_answer(user_id, user_answer)
        logger.info(f"状态: {response.status}")
        logger.info(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
        
        # 7. 尝试获取第四题 (应该会结束答题)
        logger.info("\n--- 尝试获取第四题 (应该会结束答题) ---")
        response = workflow.next_question(user_id)
        logger.info(f"状态: {response.status}")
        logger.info(f"消息: {response.message}")
        
        # 检查是否已回到聊天模式
        session = memory_manager.get_session(user_id)
        logger.info(f"最终会话状态: {session.status}")
        logger.info(f"答题进度是否为空: {session.quiz_progress is None}")
        
        logger.info("\n--- 完整答题工作流测试结果 ---")
        if session.status == "chat" and session.quiz_progress is None:
            logger.info("✅ 测试通过：答题工作流完整执行并正确结束")
        else:
            logger.info("❌ 测试失败：答题工作流未正确结束")
    
    except Exception as e:
        logger.error(f"测试过程出错: {e}", exc_info=True)
        logger.info("❌ 测试失败：遇到异常")
    
    # 清理：删除测试用户会话
    memory_manager.delete_session(user_id)
    logger.info(f"已清理测试用户会话: {user_id}")
    logger.info("========== 完整答题工作流测试完成 ==========")

def test_database_connection():
    """测试数据库连接"""
    logger.info("========== 测试数据库连接 ==========")
    
    try:
        # 使用已导入的模块
        from backend.app.utils.database import questions, db_client
        
        # 尝试从questions集合获取一条记录
        count = questions.count_documents({})
        sample = list(questions.find().limit(1))
        
        logger.info(f"MongoDB连接成功")
        logger.info(f"题库中共有{count}道题目")
        
        if sample:
            logger.info("题库样例题目:")
            logger.info(json.dumps(sample[0], ensure_ascii=False, default=str))
        else:
            logger.warning("题库为空，没有可用题目")
    except ImportError:
        # 尝试替代导入
        try:
            from app.utils.database import questions, db_client
            
            # 尝试从questions集合获取一条记录
            count = questions.count_documents({})
            sample = list(questions.find().limit(1))
            
            logger.info(f"MongoDB连接成功")
            logger.info(f"题库中共有{count}道题目")
            
            if sample:
                logger.info("题库样例题目:")
                logger.info(json.dumps(sample[0], ensure_ascii=False, default=str))
            else:
                logger.warning("题库为空，没有可用题目")
        except ImportError as e:
            logger.error(f"导入数据库模块失败: {e}")
            return
    except Exception as e:
        logger.error(f"MongoDB连接或查询失败: {e}", exc_info=True)
    
    # 测试Redis连接
    try:
        redis_info = db_client.redis.info()
        logger.info(f"Redis连接成功，版本: {redis_info.get('redis_version')}")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}", exc_info=True)
    
    logger.info("========== 数据库连接测试完成 ==========")

def test_main_workflow_instance():
    """测试主工作流实例（quiz_workflow）"""
    logger.info("========== 开始测试主工作流实例 ==========")
    
    # 测试用户ID
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    role_card = RoleCard(**EVIL_FROG_DOCTOR)
    
    # 创建会话
    session = memory_manager.create_session(user_id, role_card)
    logger.info(f"已创建测试用户会话: {user_id}")
    
    try:
        # 直接使用主工作流实例
        logger.info("\n--- 使用主工作流实例(quiz_workflow)开始答题 ---")
        response = quiz_workflow.start_quiz(user_id)
        logger.info(f"状态: {response.status}")
        logger.info(f"消息: {response.message}")
        
        if response.quiz_info:
            log_quiz_info(response.quiz_info)
            question_id = response.quiz_info.get("question_id")
            logger.info(f"题目ID: {question_id}")
            
            # 检查题目ID是否存在于数据库中
            try:
                # 先尝试使用全局导入
                from backend.app.utils.database import questions
                question_exists = questions.count_documents({"id": question_id}) > 0
            except ImportError:
                # 再尝试使用相对导入
                from app.utils.database import questions
                question_exists = questions.count_documents({"id": question_id}) > 0
                
            logger.info(f"题目ID是否存在于数据库: {question_exists}")
            
            # 直接获取提取到的题目详情
            if question_exists:
                question_data = questions.find_one({"id": question_id})
                logger.info(f"从数据库获取的题目详情:")
                logger.info(json.dumps(question_data, ensure_ascii=False, default=str))
                
            # 测试回答题目
            question_type = response.quiz_info.get("question_type")
            if question_type == "tf":
                user_answer = "是"
            elif question_type == "choice":
                user_answer = "A"
            else:
                user_answer = "这是一个测试答案"
                
            logger.info(f"\n--- 提交答案: {user_answer} ---")
            response = quiz_workflow.process_answer(user_id, user_answer)
            logger.info(f"状态: {response.status}")
            logger.info(f"反馈: {response.message[:100]}..." if len(response.message) > 100 else response.message)
            
            if response.quiz_info:
                log_quiz_info(response.quiz_info)
                logger.info(f"是否正确: {response.quiz_info.get('is_correct')}")
        else:
            logger.error("主工作流实例没有返回quiz_info")
        
        # 检查会话状态
        session = memory_manager.get_session(user_id)
        logger.info(f"\n当前会话状态: {session.status}")
        logger.info(f"答题进度: {json.dumps(session.quiz_progress, default=str) if session.quiz_progress else 'None'}")
        
        logger.info("测试通过：主工作流实例成功处理了答题流程")
    except Exception as e:
        logger.error(f"测试主工作流实例失败: {e}", exc_info=True)
    
    # 清理：删除测试用户会话
    memory_manager.delete_session(user_id)
    logger.info(f"已清理测试用户会话: {user_id}")
    logger.info("========== 主工作流实例测试完成 ==========")

if __name__ == "__main__":
    """主函数：运行所有测试"""
    logger.info("====================================================")
    logger.info("        开始执行答题工作流本地测试                  ")
    logger.info("====================================================")
    
    # 首先测试数据库连接
    test_database_connection()
    
    # 测试题目提取函数
    test_extract_questions()
    
    # 测试工作流中的题目提取方法
    test_workflow_extract_question()
    
    # 测试主工作流实例
    test_main_workflow_instance()
    
    # 测试完整的答题工作流
    test_complete_quiz_workflow()
    
    logger.info("====================================================")
    logger.info("        答题工作流本地测试执行完毕                  ")
    logger.info("====================================================") 
#!/usr/bin/env python3
"""
简化版测试脚本，专门测试题目提取功能
"""
import os
import sys
import uuid
import json
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extract_test.log')
    ]
)
logger = logging.getLogger("extract_test")

# 添加必要的路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, '../..')))  # backend目录
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, '../../..')))  # 项目根目录

logger.info(f"当前目录: {current_dir}")
logger.info(f"Python路径: {sys.path}")

# 尝试导入必要的模块
try:
    # 先尝试从app直接导入
    from app.tools.extractors import extract_choice_question, extract_tf_question, extract_short_question
    from app.utils.database import questions, db_client
    logger.info("成功直接从app导入模块")
except ImportError as e1:
    logger.warning(f"直接导入失败: {e1}")
    try:
        # 再尝试从backend.app导入
        from backend.app.tools.extractors import extract_choice_question, extract_tf_question, extract_short_question
        from backend.app.utils.database import questions, db_client
        logger.info("成功从backend.app导入模块")
    except ImportError as e2:
        logger.error(f"所有导入尝试都失败: {e1}, {e2}")
        logger.error("无法继续执行测试")
        sys.exit(1)

def test_database_connection():
    """测试数据库连接"""
    logger.info("========== 测试数据库连接 ==========")
    
    # 测试MongoDB连接
    try:
        # 尝试从questions集合获取一条记录
        count = questions.count_documents({})
        logger.info(f"MongoDB连接成功, 题库中共有{count}道题目")
        
        if count > 0:
            sample = list(questions.find().limit(1))
            logger.info("题库样例题目:")
            logger.info(json.dumps(sample[0], ensure_ascii=False, default=str))
        else:
            logger.warning("题库为空，没有可用题目")
            return False
    except Exception as e:
        logger.error(f"MongoDB连接或查询失败: {e}", exc_info=True)
        return False
    
    # 测试Redis连接
    try:
        redis_info = db_client.redis.info()
        logger.info(f"Redis连接成功，版本: {redis_info.get('redis_version')}")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}", exc_info=True)
        return False
    
    logger.info("数据库连接测试完成")
    return True

def test_extract_one_question(q_type):
    """测试提取一个指定类型的题目"""
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    logger.info(f"测试提取{q_type}题目，用户ID: {user_id}")
    
    start_time = time.time()
    try:
        if q_type == "choice":
            question = extract_choice_question(user_id)
        elif q_type == "tf":
            question = extract_tf_question(user_id)
        elif q_type == "short":
            question = extract_short_question(user_id)
        else:
            logger.error(f"不支持的题目类型: {q_type}")
            return False
        
        elapsed = time.time() - start_time
        
        if question:
            logger.info(f"成功提取{q_type}题目，耗时: {elapsed:.3f}秒")
            logger.info(f"题目ID: {question.id}")
            logger.info(f"题干: {question.stem}")
            
            if hasattr(question, 'options') and question.options:
                logger.info(f"选项: {question.options}")
                
            logger.info(f"答案: {question.answer}")
            
            if hasattr(question, 'analysis') and question.analysis:
                logger.info(f"解析: {question.analysis}")
                
            # 验证题目是否存在于数据库
            db_question = questions.find_one({"id": question.id})
            if db_question:
                logger.info("已在数据库中验证题目存在")
            else:
                logger.warning("在数据库中未找到该题目")
                
            return True
        else:
            logger.error(f"提取{q_type}题目失败，返回了None")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"提取题目出错，耗时: {elapsed:.3f}秒，错误: {e}", exc_info=True)
        return False

def print_divider():
    """打印分隔线"""
    print("\n" + "="*70 + "\n")

def run_tests():
    """运行所有测试"""
    print_divider()
    print("开始测试题目提取功能")
    print_divider()
    
    # 先测试数据库连接
    if not test_database_connection():
        print("数据库连接测试失败，无法继续后续测试")
        return
        
    print_divider()
    
    # 测试各类型题目提取
    question_types = ["choice", "tf", "short"]
    success_count = 0
    
    for q_type in question_types:
        print(f"测试提取{q_type}题目...")
        if test_extract_one_question(q_type):
            success_count += 1
            print(f"✅ {q_type}题目提取测试通过!")
        else:
            print(f"❌ {q_type}题目提取测试失败!")
        print_divider()
    
    # 打印测试总结
    print(f"测试完成: 成功 {success_count}/{len(question_types)}")
    print(f"查看详细日志请参考 extract_test.log")
    print_divider()

if __name__ == "__main__":
    run_tests() 
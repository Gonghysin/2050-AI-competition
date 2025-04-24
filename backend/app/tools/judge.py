"""
问题判分工具

用于评估用户答案的正确性，支持不同类型的题目
"""
from typing import Dict, Any, Union, List, Tuple
import re
from difflib import SequenceMatcher

from backend.app.models.question import Question, ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
from backend.app.utils.llm_client import llm_client

def ai_judge_correctness(user_answer: str, question: Question) -> Tuple[bool, str]:
    """
    智能评判答案是否正确
    
    参数:
        user_answer: 用户答案
        question: 题目对象
        
    返回:
        (是否正确, 解释)
    """
    # 根据题目类型调用不同的评判函数
    if question.type == "choice":
        return judge_choice_question(user_answer, question)
    elif question.type == "tf":
        return judge_tf_question(user_answer, question)
    else:  # short
        return judge_short_question(user_answer, question)

def judge_choice_question(user_answer: str, question: ChoiceQuestion) -> Tuple[bool, str]:
    """
    评判选择题
    
    参数:
        user_answer: 用户答案（选项标识，如A、B、C、D或1、2、3、4）
        question: 选择题对象
        
    返回:
        (是否正确, 解释)
    """
    # 清理和标准化用户答案
    user_answer = user_answer.strip().upper()
    
    # 处理常见的答案格式
    # 如果用户输入了数字，转换为对应的字母选项
    if user_answer.isdigit():
        idx = int(user_answer) - 1
        if 0 <= idx < len(question.options):
            user_answer = chr(ord('A') + idx)
    
    # 移除所有非字母数字字符
    user_answer = re.sub(r'[^A-Z0-9]', '', user_answer)
    
    # 取第一个字符作为选择
    if user_answer and (user_answer[0] in "ABCD" or user_answer[0].isdigit()):
        user_choice = user_answer[0]
    else:
        # 尝试从答案文本匹配选项
        for i, option in enumerate(question.options):
            if option.lower() in user_answer.lower():
                user_choice = chr(ord('A') + i)
                break
        else:
            # 无法确定选项
            return False, "无法确定您的选择，请使用选项字母（A、B、C、D）作答。"
    
    # 将数字选项转换为字母
    if user_choice.isdigit():
        idx = int(user_choice) - 1
        if 0 <= idx < 4:
            user_choice = chr(ord('A') + idx)
    
    # 判断答案是否正确
    # 假设标准答案是选项A、B、C、D之一
    correct_answer = question.answer.strip().upper()
    is_correct = user_choice == correct_answer
    
    # 生成解释
    if is_correct:
        explanation = f"答案正确！{correct_answer}：{question.options[ord(correct_answer) - ord('A')]}"
    else:
        explanation = f"答案错误。正确答案是 {correct_answer}：{question.options[ord(correct_answer) - ord('A')]}"
    
    if question.analysis:
        explanation += f"\n\n解析：{question.analysis}"
    
    return is_correct, explanation

def judge_tf_question(user_answer: str, question: TrueFalseQuestion) -> Tuple[bool, str]:
    """
    评判判断题
    
    参数:
        user_answer: 用户答案（T/F、正确/错误、True/False等）
        question: 判断题对象
        
    返回:
        (是否正确, 解释)
    """
    # 清理用户答案
    user_answer = user_answer.strip().lower()
    
    # 判断用户答案表示的是True还是False
    true_patterns = ["t", "true", "正确", "对", "是", "yes", "y", "√"]
    false_patterns = ["f", "false", "错误", "错", "不对", "no", "n", "×"]
    
    user_is_true = False
    user_is_false = False
    
    for pattern in true_patterns:
        if pattern in user_answer:
            user_is_true = True
            break
    
    if not user_is_true:
        for pattern in false_patterns:
            if pattern in user_answer:
                user_is_false = True
                break
    
    # 如果无法确定，按错误处理
    if not user_is_true and not user_is_false:
        return False, "无法确定您的答案是\"正确\"还是\"错误\"，请明确表示。"
    
    # 获取正确答案
    correct_is_true = question.answer == "T"
    
    # 判断是否正确
    is_correct = (user_is_true and correct_is_true) or (user_is_false and not correct_is_true)
    
    # 生成解释
    correct_text = "正确(T)" if correct_is_true else "错误(F)"
    user_text = "正确(T)" if user_is_true else "错误(F)"
    
    if is_correct:
        explanation = f"答案正确！该题的答案是\"{correct_text}\"。"
    else:
        explanation = f"答案错误。您的答案是\"{user_text}\"，但正确答案是\"{correct_text}\"。"
    
    if question.analysis:
        explanation += f"\n\n解析：{question.analysis}"
    
    return is_correct, explanation

def judge_short_question(user_answer: str, question: ShortAnswerQuestion) -> Tuple[bool, str]:
    """
    评判简答题
    
    参数:
        user_answer: 用户答案文本
        question: 简答题对象
        
    返回:
        (是否正确, 解释)
    """
    # 优先使用LLM评判简答题
    # 如果题目有关键词，也考虑使用关键词辅助评判
    if hasattr(question, 'keywords') and question.keywords:
        # 组合LLM和关键词评判
        return hybrid_judge_short_question(user_answer, question)
    else:
        # 完全依赖LLM评判
        return judge_by_llm(user_answer, question)

def hybrid_judge_short_question(user_answer: str, question: ShortAnswerQuestion) -> Tuple[bool, str]:
    """
    使用LLM和关键词结合的方式评判简答题
    
    参数:
        user_answer: 用户答案
        question: 简答题对象
        
    返回:
        (是否正确, 解释)
    """
    # 先进行关键词匹配
    user_answer_lower = user_answer.strip().lower()
    keywords = [k.lower() for k in question.keywords]
    
    # 统计命中的关键词
    hit_keywords = []
    for keyword in keywords:
        if keyword in user_answer_lower:
            hit_keywords.append(keyword)
    
    # 计算命中率
    hit_ratio = len(hit_keywords) / len(keywords) if keywords else 0
    
    # 使用LLM进行评判
    is_correct_llm, explanation_llm = judge_by_llm(user_answer, question)
    
    # 混合评分策略
    # 1. 如果关键词命中率>=80%，基本可以认为是正确的
    # 2. 如果命中率<30%，基本可以认为是错误的
    # 3. 其他情况，以LLM判断为准，但在解释中融合关键词信息
    
    if hit_ratio >= 0.8:
        is_correct = True
    elif hit_ratio < 0.3:
        is_correct = False
    else:
        is_correct = is_correct_llm
    
    # 生成融合解释
    if is_correct:
        # 正确情况下的解释
        if hit_ratio >= 0.8:
            explanation = f"回答正确！包含了大部分关键要点。\n\n{explanation_llm}"
        else:
            explanation = explanation_llm
    else:
        # 错误情况下的解释
        missed = [k for k in keywords if k not in hit_keywords]
        keyword_hint = ""
        if missed:
            missed_str = "、".join(missed[:3])
            if len(missed) > 3:
                missed_str += "等"
            keyword_hint = f"\n\n您可能遗漏了以下关键点：{missed_str}"
        
        explanation = f"{explanation_llm}{keyword_hint}"
    
    return is_correct, explanation

def judge_by_keywords(user_answer: str, question: ShortAnswerQuestion) -> Tuple[bool, str]:
    """基于关键词评判简答题"""
    user_answer = user_answer.strip().lower()
    keywords = [k.lower() for k in question.keywords]
    
    # 统计命中的关键词
    hit_keywords = []
    for keyword in keywords:
        if keyword in user_answer:
            hit_keywords.append(keyword)
    
    # 计算命中率
    hit_ratio = len(hit_keywords) / len(keywords) if keywords else 0
    
    # 判断是否正确（70%的关键词命中视为正确）
    is_correct = hit_ratio >= 0.7
    
    # 生成解释
    if is_correct:
        if hit_ratio == 1.0:
            explanation = "回答非常准确，包含了所有关键点！"
        else:
            explanation = f"回答基本正确，覆盖了主要关键点。"
    else:
        missed = [k for k in keywords if k not in hit_keywords]
        explanation = f"回答不够完整。您还可以考虑以下要点："
        for m in missed[:3]:  # 只展示前3个缺失的关键词
            explanation += f" {m},"
        
        explanation = explanation[:-1]  # 去掉最后的逗号
    
    # 添加参考答案
    explanation += f"\n\n参考答案：{question.answer}"
    
    if question.analysis:
        explanation += f"\n\n解析：{question.analysis}"
    
    return is_correct, explanation

def judge_by_llm(user_answer: str, question: ShortAnswerQuestion) -> Tuple[bool, str]:
    """使用LLM评判简答题"""
    # 构建提示
    prompt = f"""请作为一位公正的评卷老师，根据标准答案和解析，评判学生的回答是否正确。
    
题目: {question.stem}
标准答案: {question.answer}
解析: {question.analysis or '无'}

学生回答: {user_answer}

请判断学生的回答是否正确，并给出评分意见。先给出"正确"或"错误"的判断，然后给出详细解释。请尽量鼓励学生，肯定正确之处，指出不足之处。
"""
    
    # 调用LLM
    response = llm_client.chat(
        messages=[
            {"role": "system", "content": "你是一个专业的教育评估AI，善于分析答案并给出中肯的评价。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3  # 使用较低的温度以获得更确定的答案
    )
    
    result_text = response["choices"][0]["message"]["content"]
    
    # 从结果中提取判断结果
    is_correct = False
    if "正确" in result_text[:50]:  # 在回答开头的部分寻找"正确"
        is_correct = True
    
    return is_correct, result_text

if __name__ == "__main__":
    # 简单测试
    test_question = ChoiceQuestion(
        id="test1",
        stem="下列哪项是Python的基本数据类型？",
        type="choice",
        options=["Oracle", "int", "Java", "HTML"],
        answer="B",
        analysis="Python的基本数据类型包括：int, float, bool, str等。"
    )
    
    result, explanation = ai_judge_correctness("B", test_question)
    print(f"正确: {result}")
    print(f"解释: {explanation}")
    
    result, explanation = ai_judge_correctness("A", test_question)
    print(f"正确: {result}")
    print(f"解释: {explanation}") 
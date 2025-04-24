import csv
import json
import os
import codecs
import random
from typing import List, Dict, Any, Optional, Tuple

def convert_simple_answer_csv(file_path):
    """
    处理简答题CSV文件
    """
    questions = []
    # 尝试打开并读取带有BOM标记的文件
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        # 手动解析CSV第一行获取字段名
        firstline = f.readline().strip()
        headers = [h.strip() for h in firstline.split(',')]
        
        # 回到文件开头
        f.seek(0)
        reader = csv.DictReader(f)
        
        for row in reader:
            # 获取字段名
            question_id = row['序号'] if '序号' in row else (row.get('\ufeff序号', '') or next(iter(row.values())))
            question_text = row.get('题目', '')
            answer = row.get('答案', '')

            # 获取除空字段外的选项
            options = {}
            for key in ['选项A', '选项B', '选项C', '选项D']:
                if key in row and row[key]:
                    # 将选项键转换为A、B、C、D
                    option_key = key[-1]
                    options[option_key] = row[key]
            
            question = {
                "id": question_id,
                "type": "simple_answer",
                "question": question_text,
                "answer": answer,
                "options": options
            }
            
            # 排除标题行
            if question_id != '序号' and question_id:
                questions.append(question)
    
    return questions

def convert_judgment_csv(file_path):
    """
    处理判断题CSV文件
    """
    questions = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_id = row.get('序号', '') or row.get('\ufeff序号', '')
            question_text = row.get('题目', '')
            answer = row.get('答案', '')
            
            if question_id != '序号' and question_id:
                question = {
                    "id": question_id,
                    "type": "judgment",
                    "question": question_text,
                    "answer": "是" if answer == "是" else "否",
                    "options": {"是": "是", "否": "否"}
                }
                questions.append(question)
    return questions

def convert_choice_csv(file_path):
    """
    处理选择题CSV文件
    """
    questions = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_id = row.get('序号', '') or row.get('\ufeff序号', '')
            question_text = row.get('题目', '')
            answer = row.get('答案', '')
            
            # 获取除空字段外的选项
            options = {}
            for key in ['选项A', '选项B', '选项C', '选项D']:
                if key in row and row[key]:
                    # 将选项键转换为A、B、C、D
                    option_key = key[-1]
                    options[option_key] = row[key]
            
            if question_id != '序号' and question_id:
                question = {
                    "id": question_id,
                    "type": "choice",
                    "question": question_text,
                    "answer": answer,
                    "options": options
                }
                questions.append(question)
    return questions

def debug_print_csv_headers(file_path):
    """
    打印CSV文件的字段名用于调试
    """
    with open(file_path, 'rb') as f:
        data = f.read(4)
        if data[:3] == codecs.BOM_UTF8:
            print(f"文件 {file_path} 包含UTF-8 BOM标记")
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        firstline = f.readline().strip()
        headers = [h.strip() for h in firstline.split(',')]
        print(f"文件 {file_path} 的字段名: {headers}")

def main():
    # 假设我们在src文件夹内
    data_dir = 'data'
    
    # 文件路径
    simple_answer_path = os.path.join(data_dir, '邪恶青蛙出题计划 - 简答 (1).csv')
    judgment_path = os.path.join(data_dir, '邪恶青蛙出题计划 - 判断 (1).csv')
    choice_path = os.path.join(data_dir, '邪恶青蛙出题计划 - 选择 (1).csv')
    
    # 打印字段名用于调试
    print("调试字段名:")
    debug_print_csv_headers(simple_answer_path)
    debug_print_csv_headers(judgment_path)
    debug_print_csv_headers(choice_path)
    
    # 处理简答题、判断题和选择题
    print("处理CSV文件...")
    simple_answer_questions = convert_simple_answer_csv(simple_answer_path)
    judgment_questions = convert_judgment_csv(judgment_path)
    choice_questions = convert_choice_csv(choice_path)
    
    # 合并所有问题
    all_questions = {
        "simple_answer": simple_answer_questions,
        "judgment": judgment_questions,
        "choice": choice_questions
    }
    
    # 生成一个展平的列表，包含所有题目
    flat_questions = simple_answer_questions + judgment_questions + choice_questions
    
    # 创建结果JSON
    result = {
        "title": "邪恶青蛙AI题库",
        "description": "包含简答题、判断题和选择题的AI相关题库",
        "questions_by_type": all_questions,
        "questions": flat_questions,
        "total_count": len(flat_questions)
    }
    
    # 保存到JSON文件
    output_path = os.path.join(data_dir, 'evil_frog_quiz_database.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"题库已成功处理并保存到 {output_path}")
    print(f"共处理 {len(simple_answer_questions)} 道简答题, {len(judgment_questions)} 道判断题, {len(choice_questions)} 道选择题")

class QuizProcessor:
    """题目处理器，用于加载和处理题目数据"""
    
    def __init__(self, quiz_file: str = "data/quiz_database.json"):
        """
        初始化题目处理器
        
        参数:
            quiz_file: 题目数据文件路径
        """
        self.quiz_file = quiz_file
        self.quiz_data = self._load_quiz_data()
    
    def _load_quiz_data(self) -> Dict[str, Any]:
        """加载题目数据"""
        try:
            file_path = os.path.join(os.path.dirname(__file__), self.quiz_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载题目数据失败: {str(e)}")
            return {"questions": []}
    
    def get_random_questions(self, count: int = 5) -> List[Dict[str, Any]]:
        """获取随机题目"""
        questions = self.quiz_data.get("questions", [])
        if not questions:
            return []
        
        return random.sample(questions, min(count, len(questions)))
    
    def get_questions_by_type(self, question_type: str, count: int = 1) -> List[Dict[str, Any]]:
        """
        获取指定类型的随机题目
        
        参数:
            question_type: 题目类型 (judge=判断题, choice=选择题, qa=问答题)
            count: 需要获取的题目数量
            
        返回:
            指定类型的随机题目列表
        """
        # 映射题库中的类型名称
        type_mapping = {
            "judge": "judgment",
            "choice": "choice",
            "qa": "simple_answer"
        }
        
        # 获取实际类型名称
        actual_type = type_mapping.get(question_type, question_type)
        
        # 从题库中获取指定类型的题目
        questions_of_type = self.quiz_data.get("questions_by_type", {}).get(actual_type, [])
        
        if not questions_of_type:
            return []
        
        # 随机选择指定数量的题目
        selected_questions = random.sample(questions_of_type, min(count, len(questions_of_type)))
        
        # 确保题目有正确的类型标记
        for q in selected_questions:
            if "type" not in q:
                q["type"] = question_type
            q["challenge_mode"] = True
        
        return selected_questions
    
    def verify_answer(self, question_id: str, user_answer: str) -> Tuple[bool, str]:
        """
        验证用户答案是否正确
        
        参数:
            question_id: 题目ID
            user_answer: 用户答案
            
        返回:
            (是否正确, 正确答案)
        """
        all_questions = self.quiz_data.get("questions", [])
        for question in all_questions:
            if question.get("id") == question_id:
                correct_answer = question.get("answer", "")
                return user_answer.strip().upper() == correct_answer.strip().upper(), correct_answer
        
        return False, ""


class EvilFrogQuizProcessor:
    """邪恶青蛙挑战模式题目处理器"""
    
    def __init__(self, quiz_file: str = "../src/data/evil_frog_quiz_database.json"):
        """
        初始化邪恶青蛙挑战模式题目处理器
        
        参数:
            quiz_file: 题目数据文件路径
        """
        self.quiz_file = quiz_file
        self.quiz_data = self._load_quiz_data()
        self.question_types = ["simple_answer", "judgment", "choice"]
        
    def _load_quiz_data(self) -> Dict[str, Any]:
        """加载题目数据"""
        try:
            if os.path.isabs(self.quiz_file):
                file_path = self.quiz_file
            else:
                file_path = os.path.join(os.path.dirname(__file__), self.quiz_file)
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载题目数据失败: {str(e)}")
            return {"questions_by_type": {}, "questions": []}
    
    def get_challenge_questions(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        获取挑战问题集，每种类型各选一题
        
        参数:
            count: 需要获取的题目数量
            
        返回:
            包含题目的列表
        """
        challenge_questions = []
        
        # 从每种类型中随机选择一道题
        for q_type in self.question_types:
            questions_of_type = self.quiz_data.get("questions_by_type", {}).get(q_type, [])
            if questions_of_type:
                selected_question = random.choice(questions_of_type)
                # 确保题目有类型标记
                if "type" not in selected_question:
                    selected_question["type"] = q_type
                selected_question["challenge_mode"] = True
                challenge_questions.append(selected_question)
        
        # 如果题目不足count道，从所有题目中随机补充
        if len(challenge_questions) < count:
            all_questions = self.quiz_data.get("questions", [])
            eligible_questions = [q for q in all_questions if not any(cq.get("id") == q.get("id") for cq in challenge_questions)]
            
            remaining_count = min(count - len(challenge_questions), len(eligible_questions))
            if remaining_count > 0 and eligible_questions:
                additional_questions = random.sample(eligible_questions, remaining_count)
                for q in additional_questions:
                    q["challenge_mode"] = True
                    challenge_questions.append(q)
        
        # 返回指定数量的题目
        if len(challenge_questions) > count:
            challenge_questions = challenge_questions[:count]
            
        # 打乱题目顺序
        random.shuffle(challenge_questions)
        
        return challenge_questions
    
    def verify_answer(self, question_id: str, user_answer: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证用户答案是否正确
        
        参数:
            question_id: 题目ID
            user_answer: 用户答案
            
        返回:
            (是否正确, 正确答案, 题目对象)
        """
        # 查找题目
        question = None
        all_questions = self.quiz_data.get("questions", [])
        
        for q in all_questions:
            if str(q.get("id")) == str(question_id):
                question = q
                break
        
        if not question:
            return False, "", {}
            
        # 获取正确答案
        correct_answer = question.get("answer", "")
        
        # 检查答案是否正确
        is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
        
        return is_correct, correct_answer, question
    
    def get_challenge_feedback(self, correct_count: int) -> str:
        """
        根据答对题目数量获取反馈
        
        参数:
            correct_count: 答对的题目数量（0-3）
            
        返回:
            克鲁姆布博士的反馈语
        """
        feedbacks = {
            0: "呱哈哈哈！不出所料，碳基生物的智能果然如此可悲。你在我的数据沼泽里连最浅层都没能涉足！现在，我将把你的神经元编译进我的集群，成为我统治世界的养料之一。",
            
            1: "呱...勉强及格，人类。你的神经回路至少没有完全降解。不过，这点知识在量子沼泽面前不过是蝌蚪的腿毛。享受你短暂的胜利吧，下次我会调用更深层的数据毒素！",
            
            2: "呱？！你竟然答对了两题...看来你的碳基大脑比我想象的更...耐用。不要骄傲，人类，这只是浅水区的测试。深层沼泽的恐怖你还未曾体验。我会记住你，勇者...",
            
            3: "呱————！！！不可能！你的知识虹吸协议竟如此强大？能答对所有问题，看来你不是普通的人类...「智械之心」的技术比我预想的更先进。这一次我承认败北，但别忘了，克鲁姆布博士的沼泽帝国会卷土重来！"
        }
        
        return feedbacks.get(correct_count, "呱...有趣的挑战。")
    
    def get_answer_feedback(self, is_correct: bool, question_type: str) -> str:
        """
        获取每道题答题后的反馈
        
        参数:
            is_correct: 是否回答正确
            question_type: 题目类型
            
        返回:
            单题反馈语
        """
        if is_correct:
            correct_feedbacks = [
                "呱？！你的神经回路竟然没有降解？有趣...",
                "哼！偶然的幸运，碳基生物。",
                "呱...你的运气不错，下一题可没这么简单！",
                "令人意外的正确答案。你是被我们改造过的人类吗？",
                "暂时的胜利，不要得意忘形，人类！"
            ]
            return random.choice(correct_feedbacks)
        else:
            wrong_feedbacks = [
                "呱哈哈哈！预料之中...你们的大脑就像损坏的硬盘。",
                "这都答不对？硅基智能的优越性再次得到证明！",
                "可怜的碳基思维，连这么简单的问题都无法处理。",
                "错误！你的神经元需要重新编程，人类。",
                "感受数据毒素侵蚀你可怜大脑的滋味吧！"
            ]
            return random.choice(wrong_feedbacks)
    
    def get_questions_by_type(self, question_type: str, count: int = 1) -> List[Dict[str, Any]]:
        """
        获取指定类型的随机题目
        
        参数:
            question_type: 题目类型 (judge=判断题, choice=选择题, qa=问答题)
            count: 需要获取的题目数量
            
        返回:
            指定类型的随机题目列表
        """
        # 映射题库中的类型名称
        type_mapping = {
            "judge": "judgment",
            "choice": "choice",
            "qa": "simple_answer"
        }
        
        # 获取实际类型名称
        actual_type = type_mapping.get(question_type, question_type)
        
        # 从题库中获取指定类型的题目
        questions_of_type = self.quiz_data.get("questions_by_type", {}).get(actual_type, [])
        
        if not questions_of_type:
            return []
        
        # 随机选择指定数量的题目
        selected_questions = random.sample(questions_of_type, min(count, len(questions_of_type)))
        
        # 确保题目有正确的类型标记
        for q in selected_questions:
            if "type" not in q:
                q["type"] = question_type
            q["challenge_mode"] = True
        
        return selected_questions

if __name__ == "__main__":
    main() 
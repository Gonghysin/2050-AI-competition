import csv
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.app.models.question import ChoiceQuestion, TrueFalseQuestion, ShortAnswerQuestion
from backend.app.utils.database import db_client

def import_choice_questions(file_path):
    """导入选择题"""
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        questions = []
        for row in reader:
            # CSV列名为：序号,题目,答案,选项A,选项B,选项C,选项D,...
            options = [row['选项A'], row['选项B'], row['选项C'], row['选项D']]
            question = ChoiceQuestion(
                stem=row['题目'],
                options=options,
                answer=row['答案'],
                analysis=row.get('来源/参考链接', '')
            )
            questions.append(question.dict())
        
        if questions:
            db_client.mongo.questions.insert_many(questions)
            print(f"成功导入{len(questions)}道选择题")

def import_tf_questions(file_path):
    """导入判断题"""
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        questions = []
        for row in reader:
            # CSV列名为：序号,题目,答案,来源/参考链接,...
            question = TrueFalseQuestion(
                stem=row['题目'],
                answer="T" if row['答案'] == "是" else "F",
                analysis=row.get('来源/参考链接', '')
            )
            questions.append(question.dict())
        
        if questions:
            db_client.mongo.questions.insert_many(questions)
            print(f"成功导入{len(questions)}道判断题")

def import_short_questions(file_path):
    """导入简答题"""
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        questions = []
        for row in reader:
            # CSV列名为：序号,题目,答案,选项A,选项B,选项C,选项D,...
            # 注意：简答题CSV似乎包含了选项，但简答题应该没有选项
            # 这里我们只取题目和答案
            answer = row['答案']
            # 如果答案是A/B/C/D格式，则获取对应选项的值
            if answer in ['A', 'B', 'C', 'D'] and f'选项{answer}' in row:
                answer = row[f'选项{answer}']
            
            question = ShortAnswerQuestion(
                stem=row['题目'],
                answer=answer,
                analysis=""
            )
            questions.append(question.dict())
        
        if questions:
            db_client.mongo.questions.insert_many(questions)
            print(f"成功导入{len(questions)}道简答题")

if __name__ == "__main__":
    # 导入示例
    import_choice_questions("backend/data/邪恶青蛙出题计划 - 选择 (1).csv")
    import_tf_questions("backend/data/邪恶青蛙出题计划 - 判断 (1).csv")
    import_short_questions("backend/data/邪恶青蛙出题计划 - 简答 (1).csv")
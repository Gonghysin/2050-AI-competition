import csv
import json
import os
import codecs

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

if __name__ == "__main__":
    main() 
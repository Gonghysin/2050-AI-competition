import json
import os
import random
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64

# 添加my_code_repository路径到系统路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'my_code_repository'))

# 导入AI助手
from AI_helper.yunwu_helper import YunwuHelper

# 导入TTS助手
from tts_helper import TTSHelper

app = Flask(__name__)
CORS(app)  # 启用跨域请求支持

# 初始化AI助手
ai_helper = YunwuHelper()

# 初始化TTS助手
tts_helper = TTSHelper()

# 加载题目数据库
def load_quiz_database():
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'evil_frog_quiz_database.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 从每种类型中随机选择指定数量的题目
def select_random_questions(questions_by_type, num_simple=1, num_judgment=1, num_choice=1):
    selected = []
    
    # 选择简答题
    if 'simple_answer' in questions_by_type and len(questions_by_type['simple_answer']) >= num_simple:
        selected.extend(random.sample(questions_by_type['simple_answer'], num_simple))
    
    # 选择判断题
    if 'judgment' in questions_by_type and len(questions_by_type['judgment']) >= num_judgment:
        selected.extend(random.sample(questions_by_type['judgment'], num_judgment))
    
    # 选择选择题
    if 'choice' in questions_by_type and len(questions_by_type['choice']) >= num_choice:
        selected.extend(random.sample(questions_by_type['choice'], num_choice))
    
    # 打乱题目顺序
    random.shuffle(selected)
    return selected

# 获取AI对答案的评价
def get_ai_feedback(question, user_answer, correct_answer):
    if question['type'] == 'simple_answer':
        # 对于简答题，让AI来评判答案的正确性
        prompt = f"""
        问题：{question['question']}
        参考答案：{correct_answer}
        用户答案：{user_answer}
        
        请评价用户的答案是否正确，并给出简短的解释。
        即使用户答案与参考答案的表述不完全一致，只要核心概念正确也应该判断为正确。
        如果大致正确，请给予鼓励；如果不正确，请给予温和的纠正和提示。
        评价控制在50字以内。
        
        同时，返回一个"is_correct"字段，值为true或false，表示用户答案是否正确。格式如下：
        {
          "feedback": "你的评价",
          "is_correct": true或false
        }
        """
        response = ai_helper.chat(
            messages=[{"role": "user", "content": prompt}],
            model="deepseek-r1"
        )
        try:
            content = response['choices'][0]['message']['content']
            # 尝试从内容中解析JSON
            import json
            import re
            
            # 尝试找到JSON格式的部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                return {
                    "feedback": result["feedback"],
                    "is_correct": result["is_correct"]
                }
            else:
                # 如果无法解析JSON，则提供默认反馈
                return {
                    "feedback": content,
                    "is_correct": "正确" in content or "不错" in content or "对" in content
                }
        except Exception as e:
            print(f"解析AI反馈时出错: {str(e)}")
            return {
                "feedback": "很抱歉，AI助手暂时无法提供评价。",
                "is_correct": False
            }
    else:
        # 对于选择题和判断题，直接判断是否匹配
        is_correct = str(user_answer).lower() == str(correct_answer).lower()
        feedback = "回答正确！👍" if is_correct else f"回答错误。正确答案是：{correct_answer}"
        return {
            "feedback": feedback,
            "is_correct": is_correct
        }

# 生成题目音频
def generate_question_audio(question_text):
    audio_file = f"question_{hash(question_text)}.mp3"
    audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', audio_file)
    
    # 确保static目录存在
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    
    # 生成音频文件
    try:
        tts_helper.text_to_speech(question_text, audio_path)
        
        # 读取音频文件并转为base64
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            'file_path': f'/static/{audio_file}',
            'audio_base64': audio_base64
        }
    except Exception as e:
        print(f"生成音频失败: {str(e)}")
        return None

# API路由
@app.route('/api/questions', methods=['GET'])
def get_questions():
    """获取3道随机题目"""
    try:
        quiz_db = load_quiz_database()
        selected_questions = select_random_questions(
            quiz_db['questions_by_type'], 
            num_simple=1, 
            num_judgment=1, 
            num_choice=1
        )
        
        # 为每个题目生成音频
        for question in selected_questions:
            audio_info = generate_question_audio(question['question'])
            if audio_info:
                question['audio'] = audio_info
        
        return jsonify({
            'success': True,
            'questions': selected_questions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """检查答案并获取AI反馈"""
    data = request.json
    question_id = data.get('question_id')
    question_type = data.get('question_type')
    user_answer = data.get('answer')
    question_text = data.get('question')
    correct_answer = data.get('correct_answer')
    
    if not all([question_id, question_type, user_answer, question_text, correct_answer]):
        return jsonify({
            'success': False,
            'error': '请提供完整的问题和答案信息'
        }), 400
    
    question = {
        'id': question_id,
        'type': question_type,
        'question': question_text
    }
    
    feedback = get_ai_feedback(question, user_answer, correct_answer)
    
    # 生成反馈音频
    audio_info = generate_question_audio(feedback["feedback"])
    
    return jsonify({
        'success': True,
        'is_correct': feedback["is_correct"],
        'feedback': feedback["feedback"],
        'feedback_audio': audio_info
    })

@app.route('/api/final-score', methods=['POST'])
def final_score():
    """获取最终得分和AI总结"""
    data = request.json
    correct_count = data.get('correct_count', 0)
    total_count = data.get('total_count', 3)
    
    prompt = f"""
    用户刚刚完成了一个AI知识竞答，总共{total_count}道题，答对了{correct_count}道。
    请给出一段幽默且鼓励的评价，同时根据得分给出对用户AI知识水平的评估。
    评价控制在80字以内。
    """
    
    response = ai_helper.chat(
        messages=[{"role": "user", "content": prompt}],
        model="deepseek-r1"
    )
    
    try:
        feedback = response['choices'][0]['message']['content']
    except:
        feedback = f"恭喜你完成竞答！正确率：{correct_count}/{total_count}，继续加油！"
    
    # 生成反馈音频
    audio_info = generate_question_audio(feedback)
    
    return jsonify({
        'success': True,
        'feedback': feedback,
        'feedback_audio': audio_info
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
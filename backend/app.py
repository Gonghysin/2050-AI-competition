import os
import sys
import uuid
import json
import logging
import glob
import re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [app] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('app')

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入AI模块和TTS模块
from my_code_repository.AI_helper.yunwu_helper import YunwuHelper
from src.tts_helper import TTSHelper

app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS支持跨域请求

# 初始化AI助手和TTS助手
logger.info("初始化AI助手和TTS助手")
ai_helper = YunwuHelper(api_key_group="default")
tts_helper = TTSHelper()

# 保存会话历史的字典
sessions = {}

# 全局变量，用于记录已生成的音频文件
audio_files = set()

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    处理聊天请求
    请求体格式: {"session_id": "xxx", "message": "用户消息", "model": "gpt-4o"}
    """
    logger.info("收到普通聊天请求")
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'gpt-4o')  # 默认使用gpt-4o模型
    session_id = data.get('session_id')
    
    logger.debug(f"请求数据: message='{message[:20]}...', model={model}, session_id={session_id}")
    
    # 初始化会话及青蛙人设
    if not session_id or session_id not in sessions:
        session_id = session_id or str(uuid.uuid4())
        sessions[session_id] = []
        sessions[session_id].append({"role": "system", "content": "你是一只邪恶青蛙博士，语气傲慢又幽默，擅长出难题挑战人类。即使在普通对话中也要保持青蛙人设。当你感觉用户想要挑战你时（例如他们直接提到'挑战'、'测试'等词），请在回复的开头加上特定标识语'【呱！挑战模式启动！】'，然后继续你的回复。"})
        logger.debug(f"初始化新会话并添加系统提示，session_id={session_id}")

    # 添加用户消息到历史记录
    sessions[session_id].append({"role": "user", "content": message})
    logger.debug(f"添加用户消息到历史记录, 当前历史记录长度: {len(sessions[session_id])}")

    try:
        # 调用AI助手获取回复
        logger.info(f"调用AI助手获取回复, model={model}")
        response = ai_helper.chat(
            messages=sessions[session_id],
            model=model
        )
        
        # 提取回复内容
        ai_response = response['choices'][0]['message']['content']
        logger.debug(f"AI回复内容: '{ai_response[:50]}...'")
        
        # 检测是否有挑战模式标识
        challenge_pattern = r"【呱！挑战模式启动！】"
        if re.search(challenge_pattern, ai_response):
            logger.info("检测到挑战模式标识，启动挑战流程")
            # 移除标识语句
            ai_response = re.sub(challenge_pattern, "", ai_response).strip()
            # 添加AI初始回复到历史记录
            sessions[session_id].append({"role": "assistant", "content": ai_response})
            
            # 获取挑战模式题目
            from src.quiz_processor import EvilFrogQuizProcessor
            processor = EvilFrogQuizProcessor()
            questions = processor.get_challenge_questions()
            
            # 构建挑战回复
            challenge_text = f"{ai_response}\n\n让我们开始挑战！请回答以下三道题：\n"
            for idx, q in enumerate(questions, 1):
                q_text = q.get('question', '')
                # 如果是选择题，添加选项
                if q.get('type') == 'choice' and 'options' in q:
                    q_text += "\n"
                    for opt_key, opt_val in q.get('options', {}).items():
                        q_text += f"{opt_key}. {opt_val}\n"
                challenge_text += f"{idx}. {q_text}\n"
            
            # 更新历史记录
            sessions[session_id][-1]["content"] = challenge_text
            
            # 生成音频
            audio_filename = f"{session_id}_{uuid.uuid4()}_challenge.mp3"
            audio_path = os.path.join(app.static_folder, audio_filename)
            tts_helper.text_to_speech(text=challenge_text, output_file=audio_path)
            audio_files.add(audio_filename)
            
            # 返回挑战模式响应
            return jsonify({
                "session_id": session_id,
                "message": challenge_text,
                "audio_url": f"/static/{audio_filename}",
                "challenge_mode": True,
                "questions": questions
            })
        
        # 优化文本格式，增加适当换行
        ai_response = optimize_text_format(ai_response)
        
        # 添加AI回复到历史记录
        sessions[session_id].append({"role": "assistant", "content": ai_response})
        logger.debug(f"添加AI回复到历史记录, 当前历史记录长度: {len(sessions[session_id])}")
        
        # 使用TTS将回复转为语音，增加语速为1.5
        audio_filename = f"{session_id}_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.static_folder, audio_filename)
        logger.info(f"使用TTS生成语音, audio_filename={audio_filename}")
        
        tts_helper.text_to_speech(
            text=ai_response,
            output_file=audio_path,
            speed=1.5  # 加快语速
        )
        
        # 记录音频文件
        audio_files.add(audio_filename)
        
        logger.debug(f"返回聊天响应, audio_url=/static/{audio_filename}")
        return jsonify({
            "session_id": session_id,
            "message": ai_response,
            "audio_url": f"/static/{audio_filename}"
        })
        
    except Exception as e:
        logger.error(f"处理聊天请求出错: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e)
        }), 500

def optimize_text_format(text):
    """优化文本格式，增加适当换行，使其显示更美观"""
    # 确保数字列表前有换行
    text = re.sub(r'(\d+[\.\)、])\s*', r'\n\1 ', text)
    
    # 确保题目标题和解答之间有换行
    text = re.sub(r'(问题[:：]|题目[:：]|解[:：]|答[:：])', r'\n\1', text)
    
    # 确保段落标题有换行
    text = re.sub(r'^(第.*?[章节部篇].*?)$', r'\n\1\n', text, flags=re.MULTILINE)
    
    # 给长句子添加合理换行
    text = re.sub(r'([。！？\.!?])\s*', r'\1\n', text)
    
    # 处理特殊的分隔符和标点
    text = re.sub(r'[:：]\s*', r'：\n', text)
    
    # 合并连续的多个换行为最多两个换行
    text = re.sub(r'\n\s*\n\s*\n', r'\n\n', text)
    
    return text.strip()

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取AI状态（示例用，实际状态在前端管理）"""
    logger.info("收到状态请求")
    return jsonify({
        "status": "idle"
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    logger.debug(f"提供静态文件: {filename}")
    return send_from_directory(app.static_folder, filename)

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取特定会话的历史记录"""
    logger.info(f"获取会话历史, session_id={session_id}")
    if session_id not in sessions:
        logger.warning(f"会话不存在, session_id={session_id}")
        return jsonify({"error": "会话不存在"}), 404
    
    logger.debug(f"返回会话历史, 历史长度: {len(sessions[session_id])}")
    return jsonify({
        "session_id": session_id,
        "history": sessions[session_id]
    })

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除特定会话"""
    logger.info(f"删除会话, session_id={session_id}")
    if session_id in sessions:
        del sessions[session_id]
        logger.debug(f"会话已删除, session_id={session_id}")
    
    return jsonify({
        "success": True,
        "message": "会话已删除"
    })

@app.route('/api/cleanup', methods=['POST'])
def cleanup_audio():
    """清理已经使用过的音频文件"""
    logger.info("收到清理音频文件请求")
    data = request.json
    filenames = data.get('filenames', [])
    
    deleted_files = []
    for filename in filenames:
        if filename in audio_files:
            file_path = os.path.join(app.static_folder, filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(filename)
                    audio_files.remove(filename)
                    logger.debug(f"已删除音频文件: {filename}")
                else:
                    logger.warning(f"文件不存在, 无法删除: {filename}")
            except Exception as e:
                logger.error(f"删除文件出错: {str(e)}")
    
    # 也可以清理所有过期文件
    if data.get('clear_all', False):
        try:
            # 获取当前正在使用的文件之外的所有mp3文件
            all_files = glob.glob(os.path.join(app.static_folder, '*.mp3'))
            current_files = set([os.path.join(app.static_folder, f) for f in audio_files])
            old_files = set(all_files) - current_files
            
            for file_path in old_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(os.path.basename(file_path))
                    logger.debug(f"已删除过期音频文件: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"批量删除过期文件出错: {str(e)}")
    
    return jsonify({
        "success": True,
        "deleted_files": deleted_files
    })

if __name__ == '__main__':
    # 确保静态文件夹存在
    os.makedirs(app.static_folder, exist_ok=True)
    logger.info(f"启动普通应用服务器，端口：8000")
    app.run(debug=True, host='0.0.0.0', port=8000) 
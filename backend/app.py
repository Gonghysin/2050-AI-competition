import os
import sys
import uuid
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入AI模块和TTS模块
from my_code_repository.AI_helper.yunwu_helper import YunwuHelper
from src.tts_helper import TTSHelper

app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS支持跨域请求

# 初始化AI助手和TTS助手
ai_helper = YunwuHelper(api_key_group="default")
tts_helper = TTSHelper()

# 保存会话历史的字典
sessions = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    处理聊天请求
    请求体格式: {"session_id": "xxx", "message": "用户消息", "model": "gpt-4o"}
    """
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'gpt-4o')  # 默认使用gpt-4o模型
    session_id = data.get('session_id')
    
    # 如果没有提供session_id，创建一个新的
    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
        
    # 如果提供了session_id但不存在，则创建一个新的历史记录列表
    if session_id not in sessions:
        sessions[session_id] = []
    
    # 添加用户消息到历史记录
    sessions[session_id].append({"role": "user", "content": message})
    
    try:
        # 调用AI助手获取回复
        response = ai_helper.chat(
            messages=sessions[session_id],
            model=model
        )
        
        # 提取回复内容
        ai_response = response['choices'][0]['message']['content']
        
        # 添加AI回复到历史记录
        sessions[session_id].append({"role": "assistant", "content": ai_response})
        
        # 使用TTS将回复转为语音
        audio_filename = f"{session_id}_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.static_folder, audio_filename)
        
        tts_helper.text_to_speech(
            text=ai_response,
            output_file=audio_path
        )
        
        return jsonify({
            "session_id": session_id,
            "message": ai_response,
            "audio_url": f"/static/{audio_filename}"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取AI状态（示例用，实际状态在前端管理）"""
    return jsonify({
        "status": "idle"
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取特定会话的历史记录"""
    if session_id not in sessions:
        return jsonify({"error": "会话不存在"}), 404
    
    return jsonify({
        "session_id": session_id,
        "history": sessions[session_id]
    })

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除特定会话"""
    if session_id in sessions:
        del sessions[session_id]
    
    return jsonify({
        "success": True,
        "message": "会话已删除"
    })

if __name__ == '__main__':
    # 确保静态文件夹存在
    os.makedirs(app.static_folder, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=8000) 
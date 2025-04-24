import os
import sys
import uuid
import json
import logging
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
    
    # 如果没有提供session_id，创建一个新的
    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
        logger.debug(f"创建新会话 session_id={session_id}")
        
    # 如果提供了session_id但不存在，则创建一个新的历史记录列表
    if session_id not in sessions:
        sessions[session_id] = []
        logger.debug(f"为现有session_id创建新的历史记录 session_id={session_id}")
    
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
        
        # 添加AI回复到历史记录
        sessions[session_id].append({"role": "assistant", "content": ai_response})
        logger.debug(f"添加AI回复到历史记录, 当前历史记录长度: {len(sessions[session_id])}")
        
        # 使用TTS将回复转为语音
        audio_filename = f"{session_id}_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.static_folder, audio_filename)
        logger.info(f"使用TTS生成语音, audio_filename={audio_filename}")
        
        tts_helper.text_to_speech(
            text=ai_response,
            output_file=audio_path
        )
        
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

if __name__ == '__main__':
    # 确保静态文件夹存在
    os.makedirs(app.static_folder, exist_ok=True)
    logger.info(f"启动普通应用服务器，端口：8000")
    app.run(debug=True, host='0.0.0.0', port=8000) 
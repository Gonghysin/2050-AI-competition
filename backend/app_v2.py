import os
import sys
import uuid
import json
import logging
import glob
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [app_v2] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('app_v2')

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入FrogAIAgent和TTS模块
from my_code_repository.AI_helper.frog_ai_agent import FrogAIAgent
from src.tts_helper import TTSHelper

app = Flask(__name__, static_folder='static')
CORS(app)  # 启用CORS支持跨域请求

# 初始化青蛙AI代理和TTS助手
logger.info("初始化青蛙AI代理和TTS助手")
frog_agent = FrogAIAgent(model="gpt-4o", api_key_group="default")
tts_helper = TTSHelper()

# 保存会话历史的字典
sessions = {}

# 全局变量，用于记录已生成的音频文件
audio_files = set()

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    处理与青蛙AI的聊天请求
    请求体格式: {"session_id": "xxx", "message": "用户消息", "model": "gpt-4o"}
    """
    logger.info("收到聊天请求")
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'gpt-4o')  # 默认使用gpt-4o模型
    session_id = data.get('session_id')
    
    logger.debug(f"请求数据: message='{message[:20]}...', model={model}, session_id={session_id}")
    
    # 获取或创建会话
    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    elif session_id not in sessions:
        sessions[session_id] = []
    
    # 添加用户消息到历史记录
    sessions[session_id].append({"role": "user", "content": message})
    
    try:
        # 调用青蛙AI代理
        frog_agent.model = model  # 设置模型
        response = frog_agent.chat(messages=sessions[session_id])
        
        # 提取回复内容
        ai_response = response['content']
        
        # 添加AI回复到历史记录
        sessions[session_id].append({"role": "assistant", "content": ai_response})
        
        # 检查是否触发挑战模式
        if response['challenge_mode'] and response['challenge_data']:
            logger.info("检测到挑战模式，生成挑战回复")
            challenge_data = response['challenge_data']
            challenge_text = challenge_data['message']
            
            # 使用TTS生成挑战语音
            audio_filename = f"{session_id}_{uuid.uuid4()}_challenge.mp3"
            audio_path = os.path.join(app.static_folder, audio_filename)
            
            tts_helper.text_to_speech(
                text=challenge_text,
                output_file=audio_path,
                speed=1.5  # 加快语速
            )
            
            # 记录音频文件
            audio_files.add(audio_filename)
            
            # 返回挑战模式回复
            return jsonify({
                "session_id": session_id,
                "message": challenge_text,
                "audio_url": f"/static/{audio_filename}",
                "challenge_mode": True,
                "questions": challenge_data['questions'],
                "challenge_id": challenge_data['challenge_id']
            })
        
        # 普通对话模式，生成TTS
        audio_filename = f"{session_id}_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(app.static_folder, audio_filename)
        
        tts_helper.text_to_speech(
            text=ai_response,
            output_file=audio_path,
            speed=1.5  # 加快语速
        )
        
        # 记录音频文件
        audio_files.add(audio_filename)
        
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

@app.route('/api/chat/stream', methods=['POST', 'GET'])
def chat_stream():
    """
    处理流式聊天请求
    POST: 开始新的流式生成
    GET: 建立SSE连接获取流式响应
    """
    logger.info(f"收到流式请求: {request.method}")
    
    if request.method == 'POST':
        # 处理POST请求，开始生成
        data = request.json
        message = data.get('message', '')
        model = data.get('model', 'gpt-4o')  # 默认使用gpt-4o模型
        session_id = data.get('session_id')
        
        logger.debug(f"请求数据: message='{message[:20]}...', model={model}, session_id={session_id}")
        
        # 获取或创建会话
        if not session_id:
            session_id = str(uuid.uuid4())
            sessions[session_id] = []
        elif session_id not in sessions:
            sessions[session_id] = []
        
        # 添加用户消息到历史记录
        sessions[session_id].append({"role": "user", "content": message})
        
        # 创建请求ID
        request_id = str(uuid.uuid4())
        
        # 创建流式响应生成器
        frog_agent.model = model  # 设置模型
        generator = create_stream_generator(session_id, frog_agent, message)
        
        # 存储生成器
        stream_generators[request_id] = generator
        
        return jsonify({"request_id": request_id})
    
    elif request.method == 'GET':
        # 处理GET请求，建立SSE连接
        request_id = request.args.get('request_id')
        
        if not request_id or request_id not in stream_generators:
            return jsonify({"error": "无效的请求ID"}), 400
        
        # 获取生成器并从字典中移除
        generator = stream_generators.pop(request_id)
        
        # 返回流式响应
        return Response(generator(), mimetype='text/event-stream')

# 存储流式生成器
stream_generators = {}

def create_stream_generator(session_id, agent, message):
    """创建流式响应生成器"""
    def generate():
        try:
            # 用于收集完整响应
            full_response = ""
            # 当前段落文本
            current_segment = ""
            # 已生成的音频段落ID
            audio_segments = []
            # 是否检测到挑战模式
            challenge_detected = False
            
            # 调用流式API
            for text_chunk, metadata in agent.chat_stream(messages=sessions[session_id]):
                # 更新完整响应和当前段落
                full_response += text_chunk
                current_segment += text_chunk
                
                # 检查是否检测到挑战模式
                if metadata.get("challenge_mode_detected"):
                    challenge_detected = True
                
                # 如果挑战模式已激活，处理挑战数据
                if metadata.get("challenge_mode_activated"):
                    # 获取挑战数据
                    challenge_data = metadata.get("challenge_data")
                    challenge_text = challenge_data["message"]
                    
                    # 生成挑战音频
                    challenge_id = str(uuid.uuid4())
                    audio_filename = f"stream_{challenge_id}.mp3"
                    audio_path = os.path.join(app.static_folder, audio_filename)
                    
                    tts_helper.text_to_speech(
                        text=challenge_text,
                        output_file=audio_path,
                        speed=1.5
                    )
                    
                    # 记录音频文件
                    audio_files.add(audio_filename)
                    
                    # 发送挑战数据事件
                    challenge_event = {
                        "type": "challenge",
                        "challenge_text": challenge_text,
                        "audio_url": f"/static/{audio_filename}",
                        "questions": challenge_data["questions"],
                        "challenge_id": challenge_data["challenge_id"]
                    }
                    yield f"data: {json.dumps(challenge_event)}\n\n"
                    
                    # 添加挑战回复到历史记录
                    sessions[session_id].append({"role": "assistant", "content": challenge_text})
                    break
                
                # 检查是否需要为当前段落生成音频
                if len(current_segment) >= 50 and any(char in current_segment for char in "。！？.!?"):
                    # 生成音频
                    segment_id = str(uuid.uuid4())
                    audio_filename = f"stream_{segment_id}.mp3"
                    audio_path = os.path.join(app.static_folder, audio_filename)
                    
                    tts_helper.text_to_speech(
                        text=current_segment,
                        output_file=audio_path,
                        speed=1.5
                    )
                    
                    # 记录音频文件和段落ID
                    audio_files.add(audio_filename)
                    audio_segments.append(segment_id)
                    
                    # 发送段落完成事件
                    segment_event = {
                        "type": "segment",
                        "text": current_segment,
                        "segment_id": segment_id,
                        "audio_url": f"/static/{audio_filename}"
                    }
                    yield f"data: {json.dumps(segment_event)}\n\n"
                    
                    # 重置当前段落
                    current_segment = ""
                
                # 发送文本更新事件
                update_event = {
                    "type": "update",
                    "text": text_chunk
                }
                yield f"data: {json.dumps(update_event)}\n\n"
            
            # 处理最后一个段落
            if current_segment and not challenge_detected:
                # 生成音频
                segment_id = str(uuid.uuid4())
                audio_filename = f"stream_{segment_id}.mp3"
                audio_path = os.path.join(app.static_folder, audio_filename)
                
                tts_helper.text_to_speech(
                    text=current_segment,
                    output_file=audio_path,
                    speed=1.5
                )
                
                # 记录音频文件和段落ID
                audio_files.add(audio_filename)
                audio_segments.append(segment_id)
                
                # 发送段落完成事件
                segment_event = {
                    "type": "segment",
                    "text": current_segment,
                    "segment_id": segment_id,
                    "audio_url": f"/static/{audio_filename}",
                    "is_final": True
                }
                yield f"data: {json.dumps(segment_event)}\n\n"
            
            # 如果没有触发挑战模式，则添加完整回复到历史记录
            if not challenge_detected:
                sessions[session_id].append({"role": "assistant", "content": full_response})
            
            # 发送完成事件
            done_event = {
                "type": "done",
                "full_text": full_response,
                "audio_segments": audio_segments,
                "challenge_detected": challenge_detected
            }
            yield f"data: {json.dumps(done_event)}\n\n"
            
        except Exception as e:
            logger.error(f"流式生成出错: {str(e)}", exc_info=True)
            error_event = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return generate

@app.route('/api/challenge/verify', methods=['POST'])
def verify_challenge_answer():
    """验证挑战答案"""
    logger.info("收到挑战答案验证请求")
    data = request.json
    question_id = data.get('question_id')
    user_answer = data.get('answer', '')
    
    if not question_id:
        return jsonify({"error": "缺少题目ID"}), 400
    
    # 验证答案
    result = frog_agent.verify_answer(question_id, user_answer)
    
    return jsonify(result)

@app.route('/api/challenge/feedback', methods=['POST'])
def get_challenge_feedback():
    """获取挑战总体反馈"""
    logger.info("收到挑战总体反馈请求")
    data = request.json
    correct_count = data.get('correct_count', 0)
    
    # 获取反馈
    feedback = frog_agent.get_final_challenge_feedback(correct_count)
    
    # 生成反馈音频
    audio_filename = f"feedback_{uuid.uuid4()}.mp3"
    audio_path = os.path.join(app.static_folder, audio_filename)
    
    tts_helper.text_to_speech(
        text=feedback,
        output_file=audio_path,
        speed=1.5
    )
    
    # 记录音频文件
    audio_files.add(audio_filename)
    
    return jsonify({
        "feedback": feedback,
        "audio_url": f"/static/{audio_filename}"
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

@app.route('/api/cleanup', methods=['POST'])
def cleanup_audio():
    """清理已使用的音频文件"""
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
            except Exception as e:
                logger.error(f"删除文件出错: {str(e)}")
    
    return jsonify({
        "success": True,
        "deleted_files": deleted_files
    })

if __name__ == '__main__':
    # 确保静态文件夹存在
    os.makedirs(app.static_folder, exist_ok=True)
    logger.info(f"启动青蛙AI应用服务器，端口：8000")
    app.run(debug=True, host='0.0.0.0', port=8000) 
import os
import sys
import asyncio
import uuid
import json
import re
import logging
import glob
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [stream_app] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('stream_app')

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

# 句子和段落分隔符正则表达式
SEGMENT_PATTERN = re.compile(r'(?<=[。！？\.!?])\s*')

# 保存全局响应生成器
streaming_generators = {}

# 全局变量，用于记录已生成的音频文件
audio_files = set()

def split_text_into_segments(text, min_segment_length=30):
    """
    将文本分割成自然段落或句子
    
    参数:
        text: 要分割的文本
        min_segment_length: 最小段落长度，小于这个长度的段落将与下一段合并
        
    返回:
        段落列表
    """
    # 先按换行符分割成段落
    paragraphs = text.split('\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    # 如果段落已经按换行符分割得很好，直接返回
    if len(paragraphs) > 1:
        # 检查段落长度，太短的合并
        result = []
        current_paragraph = ""
        
        for p in paragraphs:
            if not current_paragraph:
                current_paragraph = p
            elif len(current_paragraph) < min_segment_length:
                current_paragraph += "\n" + p
            else:
                result.append(current_paragraph)
                current_paragraph = p
        
        # 添加最后一个段落
        if current_paragraph:
            result.append(current_paragraph)
        
        return result
    
    # 如果没有换行符，则按句子分隔符分割
    segments = SEGMENT_PATTERN.split(text)
    
    # 初始化结果列表和当前段落
    result = []
    current_segment = ""
    
    for segment in segments:
        # 忽略空段落
        if not segment.strip():
            continue
        
        # 如果当前段落为空或长度小于最小值，添加到当前段落
        if not current_segment or len(current_segment) < min_segment_length:
            current_segment += segment
        else:
            # 否则添加到结果并重置当前段落
            result.append(current_segment)
            current_segment = segment
    
    # 添加最后一个段落
    if current_segment:
        result.append(current_segment)
    
    return result

@app.route('/api/chat/stream', methods=['POST', 'GET'])
def chat_stream():
    """
    处理流式聊天请求，支持分段TTS生成
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
        
        # 如果没有提供session_id，创建一个新的
        if not session_id:
            session_id = str(uuid.uuid4())
            sessions[session_id] = []
            # 添加系统提示，维护邪恶青蛙博士人设
            sessions[session_id].append({"role": "system", "content": "你是一只邪恶青蛙博士，语气傲慢又幽默，擅长出难题挑战人类。即使在普通对话中也要保持青蛙人设。当你感觉用户想要挑战你时（例如他们直接提到'挑战'、'测试'等词），请在回复的开头加上特定标识语'【呱！挑战模式启动！】'，然后继续你的回复。"})
            logger.debug(f"创建新会话并添加系统提示 session_id={session_id}")
        
        # 如果提供了session_id但不存在，则创建一个新的历史记录列表
        if session_id not in sessions:
            sessions[session_id] = []
            # 添加系统提示，维护邪恶青蛙博士人设
            sessions[session_id].append({"role": "system", "content": "你是一只邪恶青蛙博士，语气傲慢又幽默，擅长出难题挑战人类。即使在普通对话中也要保持青蛙人设。当你感觉用户想要挑战你时（例如他们直接提到'挑战'、'测试'等词），请在回复的开头加上特定标识语'【呱！挑战模式启动！】'，然后继续你的回复。"})
            logger.debug(f"为现有session_id创建新的历史记录并添加系统提示 session_id={session_id}")
        
        # 添加用户消息到历史记录
        sessions[session_id].append({"role": "user", "content": message})
        logger.debug(f"添加用户消息到历史记录, 当前历史记录长度: {len(sessions[session_id])}")
        
        # 创建请求ID用于跟踪此次请求
        request_id = str(uuid.uuid4())
        
        # 创建并保存生成器
        streaming_generators[request_id] = create_generator(session_id, message, model)
        
        logger.debug(f"创建生成器完成, request_id={request_id}")
        return jsonify({"request_id": request_id})
    
    elif request.method == 'GET':
        # 处理GET请求，建立SSE连接
        request_id = request.args.get('request_id')
        logger.debug(f"GET请求，建立SSE连接, request_id={request_id}")
        
        if not request_id or request_id not in streaming_generators:
            logger.error(f"无效的request_id: {request_id}")
            return jsonify({"error": "无效的请求ID"}), 400
        
        # 获取生成器并从字典中移除
        generator = streaming_generators.pop(request_id)
        
        logger.debug(f"返回流式响应, request_id={request_id}")
        return Response(generator(), mimetype='text/event-stream')

def create_generator(session_id, message, model):
    """创建响应生成器"""
    def generate():
        try:
            # 用于收集完整的AI回复
            full_response = ""
            # 用于收集当前段落的文本
            current_segment = ""
            # 用于记录已处理的段落
            processed_segments = []
            # 用于存储已生成TTS的段落ID列表
            tts_segment_ids = []
            # 标记是否已检测到挑战模式
            challenge_mode_detected = False
            # 挑战模式标识
            challenge_pattern = r"【呱！挑战模式启动！】"
            
            logger.info("开始流式生成回复")
            
            # 调用AI助手获取流式回复
            for text_chunk in ai_helper.chat_stream(
                messages=sessions[session_id],
                model=model
            ):
                full_response += text_chunk
                current_segment += text_chunk
                
                # 检查是否包含挑战模式标识
                if not challenge_mode_detected and re.search(challenge_pattern, full_response):
                    logger.info("检测到挑战模式标识，将在完成流式生成后启动挑战")
                    challenge_mode_detected = True
                
                logger.debug(f"收到文本块: '{text_chunk}'")
                
                # 检查是否有句子结束
                segments = split_text_into_segments(current_segment)
                
                # 如果有多个段落，处理除最后一个以外的所有段落
                if len(segments) > 1:
                    logger.debug(f"发现多个段落, 数量: {len(segments)}")
                    for i in range(len(segments) - 1):
                        segment = segments[i]
                        logger.debug(f"处理段落 {i+1}/{len(segments)-1}: '{segment}'")
                        # 添加到已处理段落
                        processed_segments.append(segment)
                        
                        # 为这个完整段落生成TTS，使用更快的语速
                        segment_id = str(uuid.uuid4())
                        audio_filename = generate_audio_for_segment(segment_id, segment)
                        tts_segment_ids.append(segment_id)
                        logger.debug(f"发送段落完成事件, audio_url=/static/{audio_filename}")
                        yield f"data: {json.dumps({'text': segment, 'done': False, 'segment_done': True, 'segment_id': segment_id, 'segment_text': segment, 'audio_url': f'/static/{audio_filename}'})}\n\n"
                    
                    # 更新当前段落为最后一个未完成的段落
                    current_segment = segments[-1]
                    logger.debug(f"更新当前段落为: '{current_segment}'")
                
                # 发送文本块
                logger.debug("发送文本块更新事件")
                yield f"data: {json.dumps({'text': text_chunk, 'done': False})}\n\n"
            
            # 生成最后一个音频段落
            if current_segment:
                # 添加到已处理段落
                processed_segments.append(current_segment)
                logger.debug(f"处理最后一个段落: '{current_segment}'")
                
                # 生成音频并发送
                segment_id = str(uuid.uuid4())
                audio_filename = generate_audio_for_segment(segment_id, current_segment)
                tts_segment_ids.append(segment_id)
                
                data = {
                    "type": "segment",
                    "text": current_segment,
                    "segment_id": segment_id,
                    "audio_url": f"/static/{audio_filename}",
                    "is_final": True
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # 完成后，添加AI回复到历史记录
            sessions[session_id].append({"role": "assistant", "content": full_response})
            logger.debug(f"添加AI回复到历史记录, 当前历史记录长度: {len(sessions[session_id])}")
            
            # 如果检测到挑战模式，立即生成挑战题目并发送
            if challenge_mode_detected:
                logger.info("流式生成完成，启动挑战模式")
                
                # 移除挑战模式标识
                clean_response = re.sub(challenge_pattern, "", full_response).strip()
                
                # 从已添加的回复中移除标识
                sessions[session_id][-1]["content"] = clean_response
                
                # 生成挑战题目
                from src.quiz_processor import EvilFrogQuizProcessor
                processor = EvilFrogQuizProcessor()
                questions = processor.get_challenge_questions()
                
                # 构建挑战回复
                challenge_text = f"\n\n让我们开始挑战！请回答以下三道题：\n"
                for idx, q in enumerate(questions, 1):
                    q_text = q.get('question', '')
                    # 如果是选择题，添加选项
                    if q.get('type') == 'choice' and 'options' in q:
                        q_text += "\n"
                        for opt_key, opt_val in q.get('options', {}).items():
                            q_text += f"{opt_key}. {opt_val}\n"
                    challenge_text += f"{idx}. {q_text}\n"
                
                # 生成挑战音频
                challenge_id = str(uuid.uuid4())
                audio_filename = generate_audio_for_segment(challenge_id, challenge_text)
                
                # 发送挑战数据
                challenge_data = {
                    "type": "challenge",
                    "text": challenge_text,
                    "segment_id": challenge_id,
                    "audio_url": f"/static/{audio_filename}",
                    "questions": questions
                }
                yield f"data: {json.dumps(challenge_data)}\n\n"
                
                # 添加挑战消息到历史记录
                sessions[session_id].append({"role": "assistant", "content": challenge_text})
            
            # 发送完成事件
            data = {
                "type": "done",
                "full_text": full_response,
                "tts_segments": tts_segment_ids
            }
            yield f"data: {json.dumps(data)}\n\n"
            
        except Exception as e:
            logger.error(f"生成响应出错: {str(e)}", exc_info=True)
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return generate

def generate_audio_for_segment(segment_id, text):
    """为文本段落生成音频文件"""
    audio_filename = f"stream_{segment_id}.mp3"
    audio_path = os.path.join(app.static_folder, audio_filename)
    
    # 使用TTS生成音频文件
    tts_helper.text_to_speech(
        text=text,
        output_file=audio_path,
        speed=1.5  # 加快语速
    )
    
    # 记录音频文件
    audio_files.add(audio_filename)
    
    return audio_filename

@app.route('/api/stream_status', methods=['GET'])
def get_stream_status():
    """获取流式AI状态（示例用）"""
    logger.info("收到流式状态请求")
    return jsonify({
        "status": "streaming_supported"
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    logger.debug(f"提供静态文件: {filename}")
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

@app.route('/api/stream/cleanup', methods=['POST'])
def cleanup_stream_audio():
    """清理已经使用过的流式音频文件"""
    logger.info("收到清理流式音频文件请求")
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
                    logger.debug(f"已删除流式音频文件: {filename}")
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
                    logger.debug(f"已删除过期流式音频文件: {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"批量删除过期文件出错: {str(e)}")
    
    return jsonify({
        "success": True,
        "deleted_files": deleted_files
    })

if __name__ == '__main__':
    # 确保静态文件夹存在
    os.makedirs(app.static_folder, exist_ok=True)
    logger.info(f"启动流式应用服务器，端口：8001")
    app.run(debug=True, host='0.0.0.0', port=8001) 
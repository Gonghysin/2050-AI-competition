import os
import sys
import asyncio
import uuid
import json
import re
from flask import Flask, request, jsonify, Response, send_from_directory
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

# 句子和段落分隔符正则表达式
SEGMENT_PATTERN = re.compile(r'(?<=[。！？.!?])\s*')

def split_text_into_segments(text, min_segment_length=20):
    """
    将文本分割成自然段落或句子
    
    参数:
        text: 要分割的文本
        min_segment_length: 最小段落长度，小于这个长度的段落将与下一段合并
        
    返回:
        段落列表
    """
    # 按句子分隔符分割
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

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    处理流式聊天请求，支持分段TTS生成
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
            
            # 调用AI助手获取流式回复
            for text_chunk in ai_helper.chat_stream(
                messages=sessions[session_id],
                model=model
            ):
                full_response += text_chunk
                current_segment += text_chunk
                
                # 检查是否有句子结束
                segments = split_text_into_segments(current_segment)
                
                # 如果有多个段落，处理除最后一个以外的所有段落
                if len(segments) > 1:
                    for i in range(len(segments) - 1):
                        segment = segments[i]
                        # 添加到已处理段落
                        processed_segments.append(segment)
                        
                        # 为这个完整段落生成TTS
                        segment_id = str(uuid.uuid4())
                        audio_filename = f"{session_id}_{segment_id}.mp3"
                        audio_path = os.path.join(app.static_folder, audio_filename)
                        
                        tts_helper.text_to_speech(
                            text=segment,
                            output_file=audio_path
                        )
                        
                        # 发送段落完成信号和音频URL
                        tts_segment_ids.append(segment_id)
                        yield f"data: {json.dumps({
                            'text': text_chunk, 
                            'done': False, 
                            'segment_done': True,
                            'segment_id': segment_id,
                            'segment_text': segment,
                            'audio_url': f'/static/{audio_filename}'
                        })}\n\n"
                    
                    # 更新当前段落为最后一个未完成的段落
                    current_segment = segments[-1]
                
                # 发送文本块
                yield f"data: {json.dumps({'text': text_chunk, 'done': False})}\n\n"
            
            # 处理最后一个段落
            if current_segment:
                segment_id = str(uuid.uuid4())
                audio_filename = f"{session_id}_{segment_id}.mp3"
                audio_path = os.path.join(app.static_folder, audio_filename)
                
                tts_helper.text_to_speech(
                    text=current_segment,
                    output_file=audio_path
                )
                
                tts_segment_ids.append(segment_id)
                yield f"data: {json.dumps({
                    'text': '', 
                    'done': False, 
                    'segment_done': True,
                    'segment_id': segment_id,
                    'segment_text': current_segment,
                    'audio_url': f'/static/{audio_filename}'
                })}\n\n"
            
            # 添加AI回复到历史记录
            sessions[session_id].append({"role": "assistant", "content": full_response})
            
            # 发送所有段落完成信号
            yield f"data: {json.dumps({
                'text': '', 
                'done': True, 
                'session_id': session_id, 
                'segment_ids': tts_segment_ids,
                'full_response': full_response
            })}\n\n"
            
        except Exception as e:
            # 发送错误信息
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/stream_status', methods=['GET'])
def get_stream_status():
    """获取流式AI状态（示例用）"""
    return jsonify({
        "status": "streaming_supported"
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
    app.run(debug=True, host='0.0.0.0', port=8001) 
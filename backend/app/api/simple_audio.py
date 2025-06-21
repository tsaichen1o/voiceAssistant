from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import base64
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/simple-audio",
    tags=["simple-audio"],
)

class AudioData(BaseModel):
    audio_base64: str
    audio_type: str
    size: int

class AudioResponse(BaseModel):
    success: bool
    message: str
    received_size: int
    audio_type: str
    ai_response: Optional[str] = None

@router.post("/upload", response_model=AudioResponse)
async def upload_audio(audio_data: AudioData):
    """
    简单的音频上传端点 - 只接收和确认数据
    """
    try:
        logger.info(f"接收到音频数据: 类型={audio_data.audio_type}, 大小={audio_data.size}")
        
        # 验证base64数据
        try:
            decoded_data = base64.b64decode(audio_data.audio_base64)
            actual_size = len(decoded_data)
            logger.info(f"Base64解码成功: 实际大小={actual_size}")
        except Exception as e:
            logger.error(f"Base64解码失败: {e}")
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")
        
        # 简单验证音频类型
        valid_types = ['audio/wav', 'audio/webm', 'audio/mp4', 'audio/ogg']
        if audio_data.audio_type not in valid_types:
            logger.warning(f"未知音频类型: {audio_data.audio_type}")
        
        # 简单的AI模拟响应
        mock_responses = [
            "你好！我收到了你的语音消息。",
            "感谢你的录音，我正在学习如何更好地理解语音。",
            "这是一个模拟的AI响应。你的音频质量很好！",
            "我听到了你的声音，虽然我现在只能返回文本回复。",
            "语音功能测试成功！这是一个自动生成的回复。"
        ]
        
        # 根据音频大小选择不同的响应（简单的模拟逻辑）
        response_index = (actual_size // 1000) % len(mock_responses)
        ai_response = mock_responses[response_index]
        
        logger.info(f"生成AI模拟响应: {ai_response}")
        
        return AudioResponse(
            success=True,
            message="音频数据接收成功并生成AI响应",
            received_size=actual_size,
            audio_type=audio_data.audio_type,
            ai_response=ai_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"音频处理错误: {e}")
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "Simple audio API is running"} 
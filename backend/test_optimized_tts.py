import asyncio
from app.services.opensource_voice_service import OpenSourceVoiceService

async def test_optimized_tts():
    service = OpenSourceVoiceService()
    print('🧪 Testing optimized TTS with long text...')
    
    long_text = '''Hello! Welcome to TUM. The Technical University of Munich is one of Europe's leading research universities. We offer excellent programs in engineering, natural sciences, life sciences, medicine, and other fields. Our campus provides state-of-the-art facilities and a vibrant academic community. Students can enjoy world-class education while being part of cutting-edge research projects.'''
    
    print(f'📝 Original text length: {len(long_text)} chars')
    
    chunk_count = 0
    async for chunk in service._generate_tts_audio(long_text):
        chunk_count += 1
        chunk_type = chunk.get("type", "unknown")
        data_length = len(str(chunk.get("data", ""))) if chunk.get("data") else 0
        print(f'📤 Chunk {chunk_count}: type={chunk_type}, data_length={data_length}')
        
        if chunk_type == "text":
            print(f'   📄 Message: {chunk.get("data", "")}')

if __name__ == "__main__":
    asyncio.run(test_optimized_tts()) 
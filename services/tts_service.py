import asyncio
import hashlib
import os
from typing import Optional

import edge_tts

class TTSService:
    # Microsoft Edge TTS voices for Traditional Chinese
    VOICES = {
        'zh-TW-HsiaoChenNeural': 'Female, warm tone',
        'zh-TW-YunJheNeural': 'Male, professional',
        'zh-TW-HsiaoYuNeural': 'Female, young'
    }
    DEFAULT_VOICE = 'zh-TW-HsiaoChenNeural'

    def __init__(self, cache_dir: str = 'static/audio/cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_filename(self, text: str, voice: str) -> str:
        hash_key = hashlib.md5(f"{text}_{voice}".encode('utf-8')).hexdigest()
        return f"{hash_key}.mp3"

    def _get_cache_path(self, text: str, voice: str) -> str:
        filename = self._get_cache_filename(text, voice)
        return os.path.join(self.cache_dir, filename)

    def _get_url_path(self, text: str, voice: str) -> str:
        filename = self._get_cache_filename(text, voice)
        return f"/static/audio/cache/{filename}"

    def is_cached(self, text: str, voice: str = None) -> bool:
        voice = voice or self.DEFAULT_VOICE
        cache_path = self._get_cache_path(text, voice)
        return os.path.exists(cache_path)

    async def _generate_async(self, text: str, voice: str) -> str:
        cache_path = self._get_cache_path(text, voice)

        if os.path.exists(cache_path):
            return self._get_url_path(text, voice)

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(cache_path)

        return self._get_url_path(text, voice)

    def generate(self, text: str, voice: str = None) -> Optional[str]:
        if not text:
            return None

        voice = voice or self.DEFAULT_VOICE
        if voice not in self.VOICES:
            voice = self.DEFAULT_VOICE

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._generate_async(text, voice))
            loop.close()
            return result
        except Exception as e:
            print(f"TTS generation error: {e}")
            return None

    def generate_for_question(self, question: dict) -> Optional[str]:
        audio_text = question.get('question', {}).get('audio_text')
        if not audio_text:
            return None

        return self.generate(audio_text)

    def pregenerate_listening_audio(self, questions: list):
        for q in questions:
            if q.get('type') == 'listening':
                audio_text = q.get('question', {}).get('audio_text')
                if audio_text and not self.is_cached(audio_text):
                    url = self.generate(audio_text)
                    if url:
                        q['audio_url'] = url

    def clear_cache(self):
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.mp3'):
                os.remove(os.path.join(self.cache_dir, filename))

    def get_available_voices(self) -> dict:
        return self.VOICES.copy()

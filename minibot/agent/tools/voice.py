import asyncio
import logging
import wave
from typing import Optional, Dict, Any

import pyaudio
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play

logger = logging.getLogger(__name__)

class VoiceInputTool:
    """语音输入工具，支持麦克风输入并转换为文本"""
    
    name = "voice_input"
    description = "使用麦克风录制语音并转换为文本"
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
    
    async def run(self, duration: int = 5) -> str:
        """录制指定时长的语音并转换为文本
        
        Args:
            duration: 录制时长（秒）
            
        Returns:
            识别后的文本
        """
        try:
            logger.info(f"开始录制语音，时长: {duration}秒")
            
            # 录制语音
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=duration)
            
            # 识别语音
            text = self.recognizer.recognize_google(audio, language="zh-CN")
            logger.info(f"语音识别结果: {text}")
            return f"语音识别成功: {text}"
        except sr.WaitTimeoutError:
            return "错误: 录制超时，请重试"
        except sr.UnknownValueError:
            return "错误: 无法识别语音，请重试"
        except sr.RequestError as e:
            return f"错误: 语音识别服务异常: {str(e)}"
        except Exception as e:
            return f"错误: {str(e)}"

class VoiceOutputTool:
    """语音输出工具，将文本转换为语音并播放"""
    
    name = "voice_output"
    description = "将文本转换为语音并播放"
    
    async def run(self, text: str, language: str = "zh-CN") -> str:
        """将文本转换为语音并播放
        
        Args:
            text: 要转换的文本
            language: 语言代码，默认为中文
            
        Returns:
            操作结果
        """
        try:
            logger.info(f"开始文本转语音: {text[:50]}...")
            
            # 转换文本为语音
            tts = gTTS(text=text, lang=language, slow=False)
            temp_file = "temp_voice.mp3"
            tts.save(temp_file)
            
            # 播放语音
            audio = AudioSegment.from_mp3(temp_file)
            play(audio)
            
            logger.info("语音播放完成")
            return "语音播放成功"
        except Exception as e:
            return f"错误: {str(e)}"

class WhisperRecognitionTool:
    """使用Whisper模型进行语音识别"""
    
    name = "whisper_recognition"
    description = "使用Whisper模型进行高质量语音识别"
    
    def __init__(self):
        try:
            import whisper
            self.model = whisper.load_model("base")
        except ImportError:
            self.model = None
    
    async def run(self, audio_file: str = None, duration: int = 10) -> str:
        """使用Whisper模型识别语音
        
        Args:
            audio_file: 音频文件路径，如果为None则录制新音频
            duration: 录制时长（秒），仅当audio_file为None时有效
            
        Returns:
            识别后的文本
        """
        try:
            if self.model is None:
                return "错误: 未安装whisper库，请运行 'pip install whisper'"
            
            if audio_file is None:
                # 录制音频
                audio_file = "temp_audio.wav"
                self._record_audio(audio_file, duration)
            
            # 使用Whisper识别
            result = self.model.transcribe(audio_file)
            text = result["text"]
            
            logger.info(f"Whisper识别结果: {text}")
            return f"Whisper识别成功: {text}"
        except Exception as e:
            return f"错误: {str(e)}"
    
    def _record_audio(self, filename: str, duration: int):
        """录制音频到文件"""
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

class TTSTool:
    """文本转语音工具，支持多种TTS引擎"""
    
    name = "tts"
    description = "将文本转换为语音，支持多种TTS引擎"
    
    async def run(self, text: str, engine: str = "gtts", language: str = "zh-CN") -> str:
        """将文本转换为语音
        
        Args:
            text: 要转换的文本
            engine: TTS引擎，支持 'gtts' 或 'pyttsx3'
            language: 语言代码
            
        Returns:
            操作结果
        """
        try:
            logger.info(f"使用{engine}引擎进行TTS: {text[:50]}...")
            
            if engine == "pyttsx3":
                return await self._pyttsx3_tts(text, language)
            else:
                return await self._gtts_tts(text, language)
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _gtts_tts(self, text: str, language: str) -> str:
        """使用gTTS进行文本转语音"""
        tts = gTTS(text=text, lang=language, slow=False)
        temp_file = "temp_tts.mp3"
        tts.save(temp_file)
        
        audio = AudioSegment.from_mp3(temp_file)
        play(audio)
        
        return "gTTS语音播放成功"
    
    async def _pyttsx3_tts(self, text: str, language: str) -> str:
        """使用pyttsx3进行文本转语音"""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            return "pyttsx3语音播放成功"
        except ImportError:
            return "错误: 未安装pyttsx3库，请运行 'pip install pyttsx3'"

# 注册工具
def register_voice_tools(tool_registry):
    """注册语音相关工具"""
    tool_registry.register(VoiceInputTool())
    tool_registry.register(VoiceOutputTool())
    tool_registry.register(WhisperRecognitionTool())
    tool_registry.register(TTSTool())

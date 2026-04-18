import logging
from typing import Optional, Dict, Any

from googletrans import Translator, LANGUAGES
from langdetect import detect, detect_langs
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

class TranslationTool:
    """实时翻译工具，支持多语言之间的翻译"""
    
    name = "translation"
    description = "支持多语言之间的实时翻译"
    
    def __init__(self):
        self.translator = Translator()
    
    async def run(self, text: str, target_lang: str = "en", source_lang: str = "auto") -> str:
        """翻译文本
        
        Args:
            text: 要翻译的文本
            target_lang: 目标语言代码
            source_lang: 源语言代码，默认为自动检测
            
        Returns:
            翻译结果
        """
        try:
            logger.info(f"翻译文本: {text[:50]}... 从 {source_lang} 到 {target_lang}")
            
            # 执行翻译
            result = self.translator.translate(text, dest=target_lang, src=source_lang)
            
            # 获取语言名称
            source_name = LANGUAGES.get(result.src, result.src)
            target_name = LANGUAGES.get(target_lang, target_lang)
            
            logger.info(f"翻译完成: {result.text[:50]}...")
            return f"翻译结果 ({source_name} → {target_name}):\n{result.text}"
        except Exception as e:
            return f"错误: {str(e)}"

class LanguageDetectionTool:
    """语言检测工具，自动检测输入语言"""
    
    name = "language_detection"
    description = "自动检测文本的语言"
    
    async def run(self, text: str) -> str:
        """检测文本语言
        
        Args:
            text: 要检测的文本
            
        Returns:
            语言检测结果
        """
        try:
            logger.info(f"检测语言: {text[:50]}...")
            
            # 检测主要语言
            lang = detect(text)
            lang_name = LANGUAGES.get(lang, lang)
            
            # 检测多种可能的语言
            langs = detect_langs(text)
            
            result = f"检测到的语言: {lang_name} ({lang})\n"
            result += "可能的语言列表:\n"
            for l in langs:
                l_name = LANGUAGES.get(l.lang, l.lang)
                result += f"- {l_name} ({l.lang}): {l.prob:.2f}\n"
            
            logger.info(f"语言检测完成: {lang_name}")
            return result
        except Exception as e:
            return f"错误: {str(e)}"

class MultilingualModelTool:
    """多语言模型工具，支持不同语言的专用模型"""
    
    name = "multilingual_model"
    description = "使用多语言模型处理不同语言的文本"
    
    def __init__(self):
        try:
            # 加载多语言翻译模型
            self.tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-mul-en")
            self.model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-mul-en")
        except Exception as e:
            logger.warning(f"初始化多语言模型失败: {e}")
            self.tokenizer = None
            self.model = None
    
    async def run(self, text: str, task: str = "translate", target_lang: str = "en") -> str:
        """使用多语言模型处理文本
        
        Args:
            text: 输入文本
            task: 任务类型，支持 'translate' 或 'summarize'
            target_lang: 目标语言
            
        Returns:
            处理结果
        """
        try:
            if self.model is None:
                return "错误: 未初始化多语言模型"
            
            logger.info(f"使用多语言模型处理: {text[:50]}...")
            
            if task == "translate":
                # 翻译
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
                outputs = self.model.generate(**inputs)
                result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                logger.info(f"翻译完成: {result[:50]}...")
                return f"多语言模型翻译结果:\n{result}"
            elif task == "summarize":
                # 摘要（使用翻译模型进行摘要）
                inputs = self.tokenizer(f"summarize: {text}", return_tensors="pt", truncation=True, padding=True)
                outputs = self.model.generate(**inputs, max_length=150, min_length=30, length_penalty=2.0, num_beams=4)
                result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                logger.info(f"摘要完成: {result[:50]}...")
                return f"多语言模型摘要结果:\n{result}"
            else:
                return "错误: 不支持的任务类型"
        except Exception as e:
            return f"错误: {str(e)}"

class LocalizationTool:
    """本地化工具，支持不同地区的文化和习惯"""
    
    name = "localization"
    description = "根据地区和文化习惯提供本地化内容"
    
    # 本地化数据
    LOCALIZATION_DATA = {
        "greetings": {
            "en": ["Hello!", "Hi there!", "Good day!"],
            "zh": ["你好！", "嗨！", "早上好！"],
            "es": ["¡Hola!", "¡Buenos días!", "¡Hey!"],
            "fr": ["Bonjour!", "Salut!", "Bonsoir!"],
            "de": ["Hallo!", "Guten Tag!", "Moin!"],
        },
        "time_formats": {
            "en": "%Y-%m-%d %H:%M:%S",
            "zh": "%Y年%m月%d日 %H:%M:%S",
            "es": "%d/%m/%Y %H:%M:%S",
            "fr": "%d/%m/%Y %H:%M:%S",
            "de": "%d.%m.%Y %H:%M:%S",
        },
        "date_formats": {
            "en": "%B %d, %Y",
            "zh": "%Y年%m月%d日",
            "es": "%d de %B de %Y",
            "fr": "%d %B %Y",
            "de": "%d. %B %Y",
        },
    }
    
    async def run(self, text: str, locale: str = "zh", task: str = "translate") -> str:
        """提供本地化内容
        
        Args:
            text: 输入文本
            locale: 地区代码
            task: 任务类型，支持 'translate', 'greeting', 'format_time', 'format_date'
            
        Returns:
            本地化结果
        """
        try:
            logger.info(f"本地化处理: {text[:50]}... 地区: {locale}")
            
            if task == "greeting":
                # 生成问候语
                if locale in self.LOCALIZATION_DATA["greetings"]:
                    greetings = self.LOCALIZATION_DATA["greetings"][locale]
                    import random
                    greeting = random.choice(greetings)
                    return f"{greeting}"
                else:
                    return "错误: 不支持的地区"
            
            elif task == "format_time":
                # 格式化时间
                if locale in self.LOCALIZATION_DATA["time_formats"]:
                    import datetime
                    now = datetime.datetime.now()
                    time_format = self.LOCALIZATION_DATA["time_formats"][locale]
                    formatted_time = now.strftime(time_format)
                    return f"当前时间: {formatted_time}"
                else:
                    return "错误: 不支持的地区"
            
            elif task == "format_date":
                # 格式化日期
                if locale in self.LOCALIZATION_DATA["date_formats"]:
                    import datetime
                    now = datetime.datetime.now()
                    date_format = self.LOCALIZATION_DATA["date_formats"][locale]
                    formatted_date = now.strftime(date_format)
                    return f"当前日期: {formatted_date}"
                else:
                    return "错误: 不支持的地区"
            
            elif task == "translate":
                # 翻译到指定语言
                translator = Translator()
                result = translator.translate(text, dest=locale)
                lang_name = LANGUAGES.get(locale, locale)
                return f"本地化翻译 ({lang_name}):\n{result.text}"
            
            else:
                return "错误: 不支持的任务类型"
        except Exception as e:
            return f"错误: {str(e)}"

# 注册工具
def register_language_tools(tool_registry):
    """注册语言相关工具"""
    tool_registry.register(TranslationTool())
    tool_registry.register(LanguageDetectionTool())
    tool_registry.register(MultilingualModelTool())
    tool_registry.register(LocalizationTool())

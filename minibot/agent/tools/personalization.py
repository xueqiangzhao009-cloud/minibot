import logging
import os
import json
from typing import Optional, List, Dict, Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class UserProfileTool:
    """用户画像工具，构建用户兴趣和习惯画像"""
    
    name = "user_profile"
    description = "构建和管理用户兴趣和习惯画像"
    
    def __init__(self):
        self.user_profiles = {}
        self.profile_file = "user_profiles.json"
        self._load_profiles()
    
    def _load_profiles(self):
        """加载用户画像"""
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
            except Exception as e:
                logger.warning(f"加载用户画像失败: {e}")
    
    def _save_profiles(self):
        """保存用户画像"""
        try:
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profiles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存用户画像失败: {e}")
    
    async def run(self, action: str, user_id: str, data: Dict[str, Any] = None) -> str:
        """操作用户画像
        
        Args:
            action: 操作类型，支持 'create', 'update', 'get', 'analyze'
            user_id: 用户ID
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "create":
                return await self._create_profile(user_id, data)
            elif action == "update":
                return await self._update_profile(user_id, data)
            elif action == "get":
                return await self._get_profile(user_id)
            elif action == "analyze":
                return await self._analyze_profile(user_id)
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _create_profile(self, user_id: str, data: Dict[str, Any]) -> str:
        """创建用户画像"""
        if user_id in self.user_profiles:
            return "错误: 用户画像已存在"
        
        self.user_profiles[user_id] = {
            "interests": data.get("interests", []),
            "preferences": data.get("preferences", {}),
            "history": data.get("history", []),
            "demographics": data.get("demographics", {})
        }
        
        self._save_profiles()
        return f"成功创建用户画像: {user_id}"
    
    async def _update_profile(self, user_id: str, data: Dict[str, Any]) -> str:
        """更新用户画像"""
        if user_id not in self.user_profiles:
            return "错误: 用户画像不存在"
        
        profile = self.user_profiles[user_id]
        
        # 更新兴趣
        if "interests" in data:
            profile["interests"] = data["interests"]
        
        # 更新偏好
        if "preferences" in data:
            profile["preferences"].update(data["preferences"])
        
        # 更新历史
        if "history" in data:
            profile["history"].extend(data["history"])
        
        # 更新人口统计信息
        if "demographics" in data:
            profile["demographics"].update(data["demographics"])
        
        self._save_profiles()
        return f"成功更新用户画像: {user_id}"
    
    async def _get_profile(self, user_id: str) -> str:
        """获取用户画像"""
        if user_id not in self.user_profiles:
            return "错误: 用户画像不存在"
        
        profile = self.user_profiles[user_id]
        return f"用户画像: {json.dumps(profile, ensure_ascii=False, indent=2)}"
    
    async def _analyze_profile(self, user_id: str) -> str:
        """分析用户画像"""
        if user_id not in self.user_profiles:
            return "错误: 用户画像不存在"
        
        profile = self.user_profiles[user_id]
        
        # 分析兴趣
        interests = profile.get("interests", [])
        interest_count = len(interests)
        
        # 分析历史
        history = profile.get("history", [])
        history_count = len(history)
        
        # 分析偏好
        preferences = profile.get("preferences", {})
        preference_count = len(preferences)
        
        result = f"用户画像分析:\n"
        result += f"用户: {user_id}\n"
        result += f"兴趣数量: {interest_count}\n"
        result += f"历史记录数量: {history_count}\n"
        result += f"偏好设置数量: {preference_count}\n"
        
        if interests:
            result += f"主要兴趣: {', '.join(interests[:3])}\n"
        
        return result

class RecommendationTool:
    """个性化推荐工具，根据用户偏好提供个性化内容"""
    
    name = "recommendation"
    description = "根据用户偏好提供个性化内容推荐"
    
    def __init__(self):
        self.content_items = []
        self.user_profiles = {}
    
    async def run(self, action: str, user_id: str, data: Dict[str, Any] = None) -> str:
        """操作推荐
        
        Args:
            action: 操作类型，支持 'add_content', 'recommend', 'update_preferences'
            user_id: 用户ID
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "add_content":
                return await self._add_content(data)
            elif action == "recommend":
                return await self._recommend(user_id, data)
            elif action == "update_preferences":
                return await self._update_preferences(user_id, data)
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _add_content(self, data: Dict[str, Any]) -> str:
        """添加内容项"""
        if not data or "title" not in data:
            return "错误: 缺少内容标题"
        
        self.content_items.append({
            "id": len(self.content_items) + 1,
            "title": data["title"],
            "description": data.get("description", ""),
            "tags": data.get("tags", []),
            "category": data.get("category", "")
        })
        
        return f"成功添加内容: {data['title']}"
    
    async def _recommend(self, user_id: str, data: Dict[str, Any] = None) -> str:
        """推荐内容"""
        if not self.content_items:
            return "错误: 没有内容可推荐"
        
        # 简单的基于标签的推荐
        user_tags = self.user_profiles.get(user_id, {}).get("interests", [])
        
        if not user_tags:
            # 没有用户兴趣，返回热门内容
            recommendations = self.content_items[:3]
        else:
            # 基于标签匹配推荐
            scores = []
            for item in self.content_items:
                item_tags = item.get("tags", [])
                score = len(set(user_tags) & set(item_tags))
                scores.append((score, item))
            
            # 按分数排序
            scores.sort(reverse=True)
            recommendations = [item for _, item in scores[:3]]
        
        result = "推荐内容:\n"
        for i, item in enumerate(recommendations):
            result += f"{i+1}. {item['title']}\n"
            if item['description']:
                result += f"   {item['description']}\n"
            if item['tags']:
                result += f"   标签: {', '.join(item['tags'])}\n"
            result += "\n"
        
        return result
    
    async def _update_preferences(self, user_id: str, data: Dict[str, Any]) -> str:
        """更新用户偏好"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        
        self.user_profiles[user_id]["interests"] = data.get("interests", [])
        self.user_profiles[user_id]["preferences"] = data.get("preferences", {})
        
        return f"成功更新用户偏好: {user_id}"

class ContinuousLearningTool:
    """持续学习工具，从用户交互中学习和改进"""
    
    name = "continuous_learning"
    description = "从用户交互中学习和改进"
    
    def __init__(self):
        self.interaction_history = []
        self.learning_file = "learning_history.json"
        self._load_history()
    
    def _load_history(self):
        """加载学习历史"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    self.interaction_history = json.load(f)
            except Exception as e:
                logger.warning(f"加载学习历史失败: {e}")
    
    def _save_history(self):
        """保存学习历史"""
        try:
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.interaction_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存学习历史失败: {e}")
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作持续学习
        
        Args:
            action: 操作类型，支持 'record', 'learn', 'analyze'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "record":
                return await self._record_interaction(data)
            elif action == "learn":
                return await self._learn_from_history()
            elif action == "analyze":
                return await self._analyze_history()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _record_interaction(self, data: Dict[str, Any]) -> str:
        """记录用户交互"""
        if not data or "user_input" not in data or "response" not in data:
            return "错误: 缺少用户输入或响应"
        
        interaction = {
            "user_input": data["user_input"],
            "response": data["response"],
            "timestamp": data.get("timestamp", ""),
            "feedback": data.get("feedback", 0)
        }
        
        self.interaction_history.append(interaction)
        self._save_history()
        
        return "成功记录交互"
    
    async def _learn_from_history(self) -> str:
        """从历史中学习"""
        if not self.interaction_history:
            return "错误: 没有交互历史"
        
        # 简单的学习逻辑
        # 分析用户输入和响应的模式
        input_texts = [item["user_input"] for item in self.interaction_history]
        
        # 使用TF-IDF分析关键词
        if input_texts:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(input_texts)
            
            # 获取关键词
            feature_names = vectorizer.get_feature_names_out()
            sum_tfidf = tfidf_matrix.sum(axis=0)
            word_scores = [(word, sum_tfidf[0, idx]) for word, idx in vectorizer.vocabulary_.items()]
            word_scores.sort(key=lambda x: x[1], reverse=True)
            
            top_keywords = [word for word, score in word_scores[:10]]
            
            return f"学习结果: 识别到的关键词: {', '.join(top_keywords)}"
        else:
            return "错误: 没有输入文本"
    
    async def _analyze_history(self) -> str:
        """分析历史交互"""
        if not self.interaction_history:
            return "错误: 没有交互历史"
        
        total_interactions = len(self.interaction_history)
        positive_feedback = sum(1 for item in self.interaction_history if item.get("feedback", 0) > 0)
        
        result = f"交互历史分析:\n"
        result += f"总交互次数: {total_interactions}\n"
        result += f"正面反馈: {positive_feedback}\n"
        result += f"负面反馈: {total_interactions - positive_feedback}\n"
        
        return result

class AdaptiveDialogueTool:
    """自适应对话工具，根据用户风格调整对话方式"""
    
    name = "adaptive_dialogue"
    description = "根据用户风格调整对话方式"
    
    def __init__(self):
        self.user_styles = {}
    
    async def run(self, action: str, user_id: str, data: Dict[str, Any] = None) -> str:
        """操作自适应对话
        
        Args:
            action: 操作类型，支持 'analyze', 'adjust', 'get_style'
            user_id: 用户ID
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "analyze":
                return await self._analyze_style(user_id, data)
            elif action == "adjust":
                return await self._adjust_dialogue(user_id, data)
            elif action == "get_style":
                return await self._get_style(user_id)
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _analyze_style(self, user_id: str, data: Dict[str, Any]) -> str:
        """分析用户风格"""
        if not data or "text" not in data:
            return "错误: 缺少文本"
        
        text = data["text"]
        
        # 简单的风格分析
        style = {
            "formality": self._analyze_formality(text),
            "sentiment": self._analyze_sentiment(text),
            "length": len(text.split()),
            "complexity": self._analyze_complexity(text)
        }
        
        self.user_styles[user_id] = style
        
        return f"用户风格分析:\n{json.dumps(style, ensure_ascii=False, indent=2)}"
    
    async def _adjust_dialogue(self, user_id: str, data: Dict[str, Any]) -> str:
        """调整对话方式"""
        if user_id not in self.user_styles:
            return "错误: 未分析用户风格"
        
        if not data or "message" not in data:
            return "错误: 缺少消息"
        
        style = self.user_styles[user_id]
        message = data["message"]
        
        # 根据用户风格调整消息
        adjusted_message = message
        
        if style["formality"] > 0.7:
            # 正式风格
            adjusted_message = adjusted_message.replace("you", "you").capitalize()
        elif style["formality"] < 0.3:
            # 非正式风格
            adjusted_message = adjusted_message.lower()
        
        if style["length"] < 10:
            # 简短风格
            adjusted_message = " ".join(adjusted_message.split()[:10])
        
        return f"调整后的消息:\n{adjusted_message}"
    
    async def _get_style(self, user_id: str) -> str:
        """获取用户风格"""
        if user_id not in self.user_styles:
            return "错误: 未分析用户风格"
        
        style = self.user_styles[user_id]
        return f"用户风格:\n{json.dumps(style, ensure_ascii=False, indent=2)}"
    
    def _analyze_formality(self, text: str) -> float:
        """分析文本正式程度"""
        formal_words = ["please", "thank you", "regards", "sincerely", "appreciate"]
        informal_words = ["lol", "omg", "btw", "u", "ur"]
        
        formal_count = sum(1 for word in formal_words if word in text.lower())
        informal_count = sum(1 for word in informal_words if word in text.lower())
        
        total = formal_count + informal_count
        if total == 0:
            return 0.5
        return formal_count / total
    
    def _analyze_sentiment(self, text: str) -> float:
        """分析文本情感"""
        positive_words = ["good", "great", "excellent", "happy", "love"]
        negative_words = ["bad", "terrible", "awful", "sad", "hate"]
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        total = positive_count + negative_count
        if total == 0:
            return 0.5
        return positive_count / total
    
    def _analyze_complexity(self, text: str) -> float:
        """分析文本复杂度"""
        words = text.split()
        if not words:
            return 0
        
        # 计算平均词长
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # 归一化到0-1
        return min(1, avg_word_length / 10)

# 注册工具
def register_personalization_tools(tool_registry):
    """注册个性化与学习相关工具"""
    tool_registry.register(UserProfileTool())
    tool_registry.register(RecommendationTool())
    tool_registry.register(ContinuousLearningTool())
    tool_registry.register(AdaptiveDialogueTool())

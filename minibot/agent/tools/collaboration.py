import logging
import os
import json
import time
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class MultiUserCollaborationTool:
    """多用户协作工具，支持多用户同时使用"""
    
    name = "multi_user_collaboration"
    description = "支持多用户同时使用和协作"
    
    def __init__(self):
        self.users = {}
        self.active_sessions = {}
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作多用户协作
        
        Args:
            action: 操作类型，支持 'register', 'login', 'logout', 'list_users'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "register":
                return await self._register_user(data)
            elif action == "login":
                return await self._login_user(data)
            elif action == "logout":
                return await self._logout_user(data)
            elif action == "list_users":
                return await self._list_users()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _register_user(self, data: Dict[str, Any]) -> str:
        """注册用户"""
        if not data or "username" not in data:
            return "错误: 缺少用户名"
        
        username = data["username"]
        if username in self.users:
            return "错误: 用户已存在"
        
        self.users[username] = {
            "username": username,
            "joined_at": time.time(),
            "last_active": time.time(),
            "status": "offline"
        }
        
        return f"成功注册用户: {username}"
    
    async def _login_user(self, data: Dict[str, Any]) -> str:
        """用户登录"""
        if not data or "username" not in data:
            return "错误: 缺少用户名"
        
        username = data["username"]
        if username not in self.users:
            return "错误: 用户不存在"
        
        self.users[username]["status"] = "online"
        self.users[username]["last_active"] = time.time()
        
        # 创建会话
        session_id = f"session_{username}_{int(time.time())}"
        self.active_sessions[session_id] = {
            "session_id": session_id,
            "username": username,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        
        return f"用户 {username} 登录成功，会话ID: {session_id}"
    
    async def _logout_user(self, data: Dict[str, Any]) -> str:
        """用户登出"""
        if not data or "username" not in data:
            return "错误: 缺少用户名"
        
        username = data["username"]
        if username not in self.users:
            return "错误: 用户不存在"
        
        self.users[username]["status"] = "offline"
        self.users[username]["last_active"] = time.time()
        
        # 清理会话
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if session["username"] == username:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        return f"用户 {username} 登出成功"
    
    async def _list_users(self) -> str:
        """列出所有用户"""
        if not self.users:
            return "没有用户"
        
        result = "用户列表:\n"
        for username, user in self.users.items():
            result += f"- {username} (状态: {user['status']})\n"
        
        return result

class SharedSessionTool:
    """共享会话工具，分享对话历史和结果"""
    
    name = "shared_session"
    description = "分享对话历史和结果"
    
    def __init__(self):
        self.shared_sessions = {}
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作共享会话
        
        Args:
            action: 操作类型，支持 'create', 'share', 'join', 'list'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "create":
                return await self._create_shared_session(data)
            elif action == "share":
                return await self._share_session(data)
            elif action == "join":
                return await self._join_session(data)
            elif action == "list":
                return await self._list_sessions()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _create_shared_session(self, data: Dict[str, Any]) -> str:
        """创建共享会话"""
        if not data or "name" not in data:
            return "错误: 缺少会话名称"
        
        session_id = f"shared_{int(time.time())}"
        self.shared_sessions[session_id] = {
            "session_id": session_id,
            "name": data["name"],
            "created_at": time.time(),
            "owner": data.get("owner", "system"),
            "participants": [data.get("owner", "system")],
            "messages": []
        }
        
        return f"成功创建共享会话: {data['name']} (ID: {session_id})"
    
    async def _share_session(self, data: Dict[str, Any]) -> str:
        """分享会话"""
        if not data or "session_id" not in data or "user" not in data:
            return "错误: 缺少会话ID或用户"
        
        session_id = data["session_id"]
        user = data["user"]
        
        if session_id not in self.shared_sessions:
            return "错误: 会话不存在"
        
        session = self.shared_sessions[session_id]
        if user not in session["participants"]:
            session["participants"].append(user)
        
        return f"成功分享会话 {session['name']} 给用户 {user}"
    
    async def _join_session(self, data: Dict[str, Any]) -> str:
        """加入会话"""
        if not data or "session_id" not in data or "user" not in data:
            return "错误: 缺少会话ID或用户"
        
        session_id = data["session_id"]
        user = data["user"]
        
        if session_id not in self.shared_sessions:
            return "错误: 会话不存在"
        
        session = self.shared_sessions[session_id]
        if user not in session["participants"]:
            session["participants"].append(user)
        
        return f"用户 {user} 成功加入会话 {session['name']}"
    
    async def _list_sessions(self) -> str:
        """列出所有共享会话"""
        if not self.shared_sessions:
            return "没有共享会话"
        
        result = "共享会话列表:\n"
        for session_id, session in self.shared_sessions.items():
            result += f"- {session['name']} (ID: {session_id}, 参与者: {len(session['participants'])})\n"
        
        return result

class TeamTaskTool:
    """团队任务工具，分配和跟踪团队任务"""
    
    name = "team_task"
    description = "分配和跟踪团队任务"
    
    def __init__(self):
        self.tasks = {}
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作团队任务
        
        Args:
            action: 操作类型，支持 'create', 'assign', 'update', 'list'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "create":
                return await self._create_task(data)
            elif action == "assign":
                return await self._assign_task(data)
            elif action == "update":
                return await self._update_task(data)
            elif action == "list":
                return await self._list_tasks(data)
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _create_task(self, data: Dict[str, Any]) -> str:
        """创建任务"""
        if not data or "title" not in data:
            return "错误: 缺少任务标题"
        
        task_id = f"task_{int(time.time())}"
        self.tasks[task_id] = {
            "task_id": task_id,
            "title": data["title"],
            "description": data.get("description", ""),
            "status": "pending",
            "assignee": data.get("assignee", ""),
            "priority": data.get("priority", "medium"),
            "due_date": data.get("due_date", ""),
            "created_at": time.time()
        }
        
        return f"成功创建任务: {data['title']} (ID: {task_id})"
    
    async def _assign_task(self, data: Dict[str, Any]) -> str:
        """分配任务"""
        if not data or "task_id" not in data or "assignee" not in data:
            return "错误: 缺少任务ID或负责人"
        
        task_id = data["task_id"]
        if task_id not in self.tasks:
            return "错误: 任务不存在"
        
        self.tasks[task_id]["assignee"] = data["assignee"]
        return f"成功分配任务 {self.tasks[task_id]['title']} 给 {data['assignee']}"
    
    async def _update_task(self, data: Dict[str, Any]) -> str:
        """更新任务"""
        if not data or "task_id" not in data:
            return "错误: 缺少任务ID"
        
        task_id = data["task_id"]
        if task_id not in self.tasks:
            return "错误: 任务不存在"
        
        task = self.tasks[task_id]
        
        if "status" in data:
            task["status"] = data["status"]
        if "description" in data:
            task["description"] = data["description"]
        if "priority" in data:
            task["priority"] = data["priority"]
        if "due_date" in data:
            task["due_date"] = data["due_date"]
        
        return f"成功更新任务: {task['title']}"
    
    async def _list_tasks(self, data: Dict[str, Any] = None) -> str:
        """列出任务"""
        if not self.tasks:
            return "没有任务"
        
        result = "任务列表:\n"
        for task_id, task in self.tasks.items():
            if data and "assignee" in data and task["assignee"] != data["assignee"]:
                continue
            if data and "status" in data and task["status"] != data["status"]:
                continue
            
            result += f"- {task['title']} (ID: {task_id})\n"
            result += f"   状态: {task['status']}\n"
            result += f"   负责人: {task['assignee'] or '未分配'}\n"
            result += f"   优先级: {task['priority']}\n"
            if task['due_date']:
                result += f"   截止日期: {task['due_date']}\n"
            result += "\n"
        
        return result

class CollaborativeEditingTool:
    """协作编辑工具，多人同时编辑文档"""
    
    name = "collaborative_editing"
    description = "多人同时编辑文档"
    
    def __init__(self):
        self.documents = {}
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作协作编辑
        
        Args:
            action: 操作类型，支持 'create', 'edit', 'share', 'list'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "create":
                return await self._create_document(data)
            elif action == "edit":
                return await self._edit_document(data)
            elif action == "share":
                return await self._share_document(data)
            elif action == "list":
                return await self._list_documents()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _create_document(self, data: Dict[str, Any]) -> str:
        """创建文档"""
        if not data or "title" not in data:
            return "错误: 缺少文档标题"
        
        doc_id = f"doc_{int(time.time())}"
        self.documents[doc_id] = {
            "doc_id": doc_id,
            "title": data["title"],
            "content": data.get("content", ""),
            "owner": data.get("owner", "system"),
            "collaborators": [data.get("owner", "system")],
            "last_updated": time.time(),
            "version": 1
        }
        
        return f"成功创建文档: {data['title']} (ID: {doc_id})"
    
    async def _edit_document(self, data: Dict[str, Any]) -> str:
        """编辑文档"""
        if not data or "doc_id" not in data or "content" not in data:
            return "错误: 缺少文档ID或内容"
        
        doc_id = data["doc_id"]
        if doc_id not in self.documents:
            return "错误: 文档不存在"
        
        document = self.documents[doc_id]
        document["content"] = data["content"]
        document["last_updated"] = time.time()
        document["version"] += 1
        
        return f"成功编辑文档: {document['title']} (版本: {document['version']})"
    
    async def _share_document(self, data: Dict[str, Any]) -> str:
        """分享文档"""
        if not data or "doc_id" not in data or "user" not in data:
            return "错误: 缺少文档ID或用户"
        
        doc_id = data["doc_id"]
        user = data["user"]
        
        if doc_id not in self.documents:
            return "错误: 文档不存在"
        
        document = self.documents[doc_id]
        if user not in document["collaborators"]:
            document["collaborators"].append(user)
        
        return f"成功分享文档 {document['title']} 给用户 {user}"
    
    async def _list_documents(self) -> str:
        """列出所有文档"""
        if not self.documents:
            return "没有文档"
        
        result = "文档列表:\n"
        for doc_id, document in self.documents.items():
            result += f"- {document['title']} (ID: {doc_id})\n"
            result += f"   协作者: {len(document['collaborators'])}\n"
            result += f"   版本: {document['version']}\n"
            result += f"   最后更新: {time.ctime(document['last_updated'])}\n"
        
        return result

# 注册工具
def register_collaboration_tools(tool_registry):
    """注册协作功能相关工具"""
    tool_registry.register(MultiUserCollaborationTool())
    tool_registry.register(SharedSessionTool())
    tool_registry.register(TeamTaskTool())
    tool_registry.register(CollaborativeEditingTool())

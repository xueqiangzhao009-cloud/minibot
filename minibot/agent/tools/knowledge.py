import logging
import os
import json
from typing import Optional, List, Dict, Any

import networkx as nx
from py2neo import Graph, Node, Relationship
from langchain.document_loaders import TextLoader, PyPDFLoader, DocxLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from transformers import pipeline

logger = logging.getLogger(__name__)

class KnowledgeGraphTool:
    """知识图谱工具，构建和使用知识图谱存储信息"""
    
    name = "knowledge_graph"
    description = "构建和使用知识图谱存储和查询信息"
    
    def __init__(self):
        try:
            # 初始化Neo4j连接
            self.graph = Graph("bolt://localhost:7687", auth=('neo4j', 'password'))
        except Exception as e:
            logger.warning(f"初始化知识图谱失败: {e}")
            self.graph = None
            # 使用内存中的图作为后备
            self.memory_graph = nx.DiGraph()
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作知识图谱
        
        Args:
            action: 操作类型，支持 'add', 'query', 'visualize'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "add":
                return await self._add_to_graph(data)
            elif action == "query":
                return await self._query_graph(data)
            elif action == "visualize":
                return await self._visualize_graph()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _add_to_graph(self, data: Dict[str, Any]) -> str:
        """添加数据到知识图谱"""
        if not data:
            return "错误: 缺少数据"
        
        if self.graph:
            # 使用Neo4j
            try:
                for node in data.get("nodes", []):
                    self.graph.create(Node(node["type"], name=node["name"], **node.get("properties", {})))
                
                for relationship in data.get("relationships", []):
                    start_node = self.graph.nodes.match(relationship["start_type"], name=relationship["start"]).first()
                    end_node = self.graph.nodes.match(relationship["end_type"], name=relationship["end"]).first()
                    if start_node and end_node:
                        self.graph.create(Relationship(start_node, relationship["type"], end_node, **relationship.get("properties", {})))
                
                return "成功添加到知识图谱"
            except Exception:
                # 回退到内存图
                pass
        
        # 使用内存图
        for node in data.get("nodes", []):
            self.memory_graph.add_node(node["name"], type=node["type"], **node.get("properties", {}))
        
        for relationship in data.get("relationships", []):
            self.memory_graph.add_edge(relationship["start"], relationship["end"], type=relationship["type"], **relationship.get("properties", {}))
        
        return "成功添加到内存知识图谱"
    
    async def _query_graph(self, data: Dict[str, Any]) -> str:
        """查询知识图谱"""
        if not data:
            return "错误: 缺少查询数据"
        
        if self.graph:
            # 使用Neo4j查询
            try:
                query = data.get("query", "")
                result = self.graph.run(query)
                return f"查询结果:\n{list(result)}"
            except Exception:
                # 回退到内存图
                pass
        
        # 使用内存图查询
        node = data.get("node")
        if node:
            neighbors = list(self.memory_graph.neighbors(node))
            return f"节点 {node} 的邻居: {neighbors}"
        
        return "错误: 查询参数不完整"
    
    async def _visualize_graph(self) -> str:
        """可视化知识图谱"""
        if self.graph:
            # 使用Neo4j可视化
            try:
                node_count = self.graph.nodes.match().count()
                rel_count = self.graph.relationships.match().count()
                return f"知识图谱包含 {node_count} 个节点和 {rel_count} 个关系"
            except Exception:
                pass
        
        # 使用内存图
        node_count = self.memory_graph.number_of_nodes()
        rel_count = self.memory_graph.number_of_edges()
        return f"内存知识图谱包含 {node_count} 个节点和 {rel_count} 个关系"

class DocumentManagementTool:
    """文档管理工具，支持文档上传、索引和检索"""
    
    name = "document_management"
    description = "支持文档上传、索引和检索"
    
    def __init__(self):
        self.documents = {}
        self.vector_store = None
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作文档
        
        Args:
            action: 操作类型，支持 'upload', 'search', 'list'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "upload":
                return await self._upload_document(data)
            elif action == "search":
                return await self._search_documents(data)
            elif action == "list":
                return await self._list_documents()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _upload_document(self, data: Dict[str, Any]) -> str:
        """上传文档"""
        if not data or "file_path" not in data:
            return "错误: 缺少文件路径"
        
        file_path = data["file_path"]
        if not os.path.exists(file_path):
            return "错误: 文件不存在"
        
        # 加载文档
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt":
            loader = TextLoader(file_path)
        elif ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = DocxLoader(file_path)
        else:
            return "错误: 不支持的文件格式"
        
        documents = loader.load()
        
        # 分割文档
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)
        
        # 存储文档
        self.documents[os.path.basename(file_path)] = split_docs
        
        # 构建向量存储
        try:
            embeddings = OpenAIEmbeddings()
            if self.vector_store:
                self.vector_store.add_documents(split_docs)
            else:
                self.vector_store = FAISS.from_documents(split_docs, embeddings)
            
            return f"成功上传文档: {os.path.basename(file_path)}"
        except Exception:
            return f"成功上传文档但未索引: {os.path.basename(file_path)}"
    
    async def _search_documents(self, data: Dict[str, Any]) -> str:
        """搜索文档"""
        if not data or "query" not in data:
            return "错误: 缺少查询内容"
        
        if not self.vector_store:
            return "错误: 未索引任何文档"
        
        query = data["query"]
        results = self.vector_store.similarity_search(query, k=data.get("k", 3))
        
        result = f"搜索结果 (共 {len(results)} 个):\n"
        for i, doc in enumerate(results):
            result += f"{i+1}. {doc.metadata.get('source', 'Unknown')}\n"
            result += f"   {doc.page_content[:100]}...\n\n"
        
        return result
    
    async def _list_documents(self) -> str:
        """列出所有文档"""
        if not self.documents:
            return "没有上传任何文档"
        
        result = "已上传的文档:\n"
        for doc_name, docs in self.documents.items():
            result += f"- {doc_name} ( {len(docs)} 个片段)\n"
        
        return result

class KnowledgeBaseTool:
    """知识库工具，创建和管理专业知识库"""
    
    name = "knowledge_base"
    description = "创建和管理专业知识库"
    
    def __init__(self):
        self.knowledge_bases = {}
    
    async def run(self, action: str, data: Dict[str, Any] = None) -> str:
        """操作知识库
        
        Args:
            action: 操作类型，支持 'create', 'add', 'query', 'list'
            data: 操作数据
            
        Returns:
            操作结果
        """
        try:
            if action == "create":
                return await self._create_knowledge_base(data)
            elif action == "add":
                return await self._add_to_knowledge_base(data)
            elif action == "query":
                return await self._query_knowledge_base(data)
            elif action == "list":
                return await self._list_knowledge_bases()
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _create_knowledge_base(self, data: Dict[str, Any]) -> str:
        """创建知识库"""
        if not data or "name" not in data:
            return "错误: 缺少知识库名称"
        
        name = data["name"]
        self.knowledge_bases[name] = []
        return f"成功创建知识库: {name}"
    
    async def _add_to_knowledge_base(self, data: Dict[str, Any]) -> str:
        """向知识库添加内容"""
        if not data or "name" not in data or "content" not in data:
            return "错误: 缺少知识库名称或内容"
        
        name = data["name"]
        if name not in self.knowledge_bases:
            return "错误: 知识库不存在"
        
        self.knowledge_bases[name].append(data["content"])
        return f"成功添加内容到知识库: {name}"
    
    async def _query_knowledge_base(self, data: Dict[str, Any]) -> str:
        """查询知识库"""
        if not data or "name" not in data or "query" not in data:
            return "错误: 缺少知识库名称或查询内容"
        
        name = data["name"]
        if name not in self.knowledge_bases:
            return "错误: 知识库不存在"
        
        query = data["query"]
        knowledge_base = self.knowledge_bases[name]
        
        # 简单的关键词匹配
        results = []
        for content in knowledge_base:
            if query.lower() in content.lower():
                results.append(content)
        
        result = f"知识库 {name} 查询结果 (共 {len(results)} 个):\n"
        for i, content in enumerate(results[:3]):  # 只返回前3个结果
            result += f"{i+1}. {content[:100]}...\n\n"
        
        return result
    
    async def _list_knowledge_bases(self) -> str:
        """列出所有知识库"""
        if not self.knowledge_bases:
            return "没有创建任何知识库"
        
        result = "已创建的知识库:\n"
        for name, contents in self.knowledge_bases.items():
            result += f"- {name} ( {len(contents)} 条内容)\n"
        
        return result

class InformationExtractionTool:
    """信息提取工具，从文本中提取结构化信息"""
    
    name = "information_extraction"
    description = "从文本中提取结构化信息"
    
    def __init__(self):
        try:
            self.extractor = pipeline("token-classification", model="dslim/bert-base-NER")
        except Exception as e:
            logger.warning(f"初始化信息提取模型失败: {e}")
            self.extractor = None
    
    async def run(self, text: str, extraction_type: str = "ner") -> str:
        """提取信息
        
        Args:
            text: 输入文本
            extraction_type: 提取类型，支持 'ner'（命名实体识别）
            
        Returns:
            提取结果
        """
        try:
            if extraction_type == "ner":
                return await self._extract_ner(text)
            else:
                return "错误: 不支持的提取类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _extract_ner(self, text: str) -> str:
        """提取命名实体"""
        if self.extractor:
            results = self.extractor(text)
            
            # 整理结果
            entities = {}
            for entity in results:
                entity_type = entity["entity"]
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].append(entity["word"])
            
            result = "命名实体提取结果:\n"
            for entity_type, words in entities.items():
                result += f"{entity_type}: {', '.join(words)}\n"
            
            return result
        else:
            # 简单的关键词提取作为后备
            import re
            
            # 提取邮箱
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            # 提取电话号码
            phones = re.findall(r'\b\d{11}\b', text)
            # 提取URL
            urls = re.findall(r'https?://\S+', text)
            
            result = "信息提取结果:\n"
            if emails:
                result += f"邮箱: {', '.join(emails)}\n"
            if phones:
                result += f"电话: {', '.join(phones)}\n"
            if urls:
                result += f"URL: {', '.join(urls)}\n"
            
            return result

# 注册工具
def register_knowledge_tools(tool_registry):
    """注册知识管理相关工具"""
    tool_registry.register(KnowledgeGraphTool())
    tool_registry.register(DocumentManagementTool())
    tool_registry.register(KnowledgeBaseTool())
    tool_registry.register(InformationExtractionTool())

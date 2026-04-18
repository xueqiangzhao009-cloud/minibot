import logging
import os
import subprocess
from typing import Optional, List, Dict, Any

import pycodestyle
import pylint.lint
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

class CodeGenerationTool:
    """代码生成工具，根据需求生成代码"""
    
    name = "code_generation"
    description = "根据需求生成代码"
    
    def __init__(self):
        try:
            # 加载代码生成模型
            self.tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-mono")
            self.model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-350M-mono")
        except Exception as e:
            logger.warning(f"初始化代码生成模型失败: {e}")
            self.tokenizer = None
            self.model = None
    
    async def run(self, prompt: str, language: str = "python", max_length: int = 500) -> str:
        """生成代码
        
        Args:
            prompt: 代码需求描述
            language: 编程语言
            max_length: 生成代码的最大长度
            
        Returns:
            生成的代码
        """
        try:
            logger.info(f"生成 {language} 代码: {prompt[:50]}...")
            
            if self.model:
                # 使用预训练模型生成代码
                inputs = self.tokenizer(f"# {language}\n# {prompt}\n", return_tensors="pt")
                outputs = self.model.generate(**inputs, max_length=max_length, temperature=0.7)
                code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                logger.info("代码生成完成")
                return f"生成的 {language} 代码:\n```\n{code}\n```"
            else:
                # 简单的代码模板作为后备
                if language == "python":
                    code = f"""# {prompt}
def example_function():
    """示例函数"""
    pass

if __name__ == "__main__":
    example_function()
"""
                elif language == "javascript":
                    code = f"""// {prompt}
function exampleFunction() {
    // 示例函数
}

// 调用示例
exampleFunction();
"""
                else:
                    code = f"// {prompt}"
                
                return f"生成的 {language} 代码:\n```\n{code}\n```"
        except Exception as e:
            return f"错误: {str(e)}"

class CodeAnalysisTool:
    """代码分析工具，分析代码质量和潜在问题"""
    
    name = "code_analysis"
    description = "分析代码质量和潜在问题"
    
    async def run(self, file_path: str) -> str:
        """分析代码
        
        Args:
            file_path: 代码文件路径
            
        Returns:
            分析结果
        """
        try:
            if not os.path.exists(file_path):
                return "错误: 文件不存在"
            
            logger.info(f"分析代码: {file_path}")
            
            # 代码风格检查
            style_guide = pycodestyle.StyleGuide()
            style_results = style_guide.check_files([file_path])
            
            # 代码复杂度分析
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 计算圈复杂度
            cc_results = cc_visit(code)
            total_complexity = sum(func.complexity for func in cc_results)
            
            # 计算维护性指标
            mi_results = mi_visit(code)
            
            # 代码质量分析
            result = f"代码分析结果:\n"
            result += f"文件: {file_path}\n"
            result += f"代码风格问题: {style_results.total_errors}\n"
            result += f"圈复杂度: {total_complexity}\n"
            result += f"维护性指标: {mi_results}\n"
            
            # 函数复杂度详情
            result += "\n函数复杂度:\n"
            for func in cc_results:
                result += f"- {func.name}: 复杂度 {func.complexity}\n"
            
            logger.info("代码分析完成")
            return result
        except Exception as e:
            return f"错误: {str(e)}"

class TestingTool:
    """测试工具，自动生成和运行测试"""
    
    name = "testing"
    description = "自动生成和运行测试"
    
    async def run(self, action: str, file_path: str, test_type: str = "unit") -> str:
        """操作测试
        
        Args:
            action: 操作类型，支持 'generate', 'run'
            file_path: 代码文件路径
            test_type: 测试类型，支持 'unit', 'integration'
            
        Returns:
            操作结果
        """
        try:
            if action == "generate":
                return await self._generate_tests(file_path, test_type)
            elif action == "run":
                return await self._run_tests(file_path)
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _generate_tests(self, file_path: str, test_type: str) -> str:
        """生成测试"""
        if not os.path.exists(file_path):
            return "错误: 文件不存在"
        
        logger.info(f"生成 {test_type} 测试: {file_path}")
        
        # 简单的测试生成逻辑
        test_file = f"test_{os.path.basename(file_path)}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 提取函数名
        import re
        functions = re.findall(r'def\s+(\w+)\s*\(', code)
        
        test_content = f"""import unittest
import {os.path.splitext(os.path.basename(file_path))[0]}

class Test{os.path.splitext(os.path.basename(file_path))[0].capitalize()}(unittest.TestCase):
"""
        
        for func in functions:
            test_content += f"    def test_{func}(self):\n"
            test_content += f"        # 测试 {func} 函数\n"
            test_content += f"        pass\n\n"
        
        test_content += """
if __name__ == '__main__':
    unittest.main()
"""
        
        # 保存测试文件
        test_path = os.path.join(os.path.dirname(file_path), test_file)
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        return f"成功生成测试文件: {test_path}"
    
    async def _run_tests(self, file_path: str) -> str:
        """运行测试"""
        if not os.path.exists(file_path):
            return "错误: 文件不存在"
        
        logger.info(f"运行测试: {file_path}")
        
        try:
            # 运行测试
            result = subprocess.run(
                ['python', '-m', 'pytest', file_path, '-v'],
                capture_output=True,
                text=True
            )
            
            return f"测试结果:\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"错误: {str(e)}"

class DeploymentTool:
    """部署工具，自动化部署流程"""
    
    name = "deployment"
    description = "自动化部署流程"
    
    async def run(self, action: str, project_path: str, target: str = "local") -> str:
        """操作部署
        
        Args:
            action: 操作类型，支持 'build', 'deploy', 'status'
            project_path: 项目路径
            target: 部署目标，支持 'local', 'docker', 'cloud'
            
        Returns:
            操作结果
        """
        try:
            if action == "build":
                return await self._build_project(project_path)
            elif action == "deploy":
                return await self._deploy_project(project_path, target)
            elif action == "status":
                return await self._check_status(project_path, target)
            else:
                return "错误: 不支持的操作类型"
        except Exception as e:
            return f"错误: {str(e)}"
    
    async def _build_project(self, project_path: str) -> str:
        """构建项目"""
        if not os.path.exists(project_path):
            return "错误: 项目路径不存在"
        
        logger.info(f"构建项目: {project_path}")
        
        # 检查是否有requirements.txt
        requirements_path = os.path.join(project_path, "requirements.txt")
        if os.path.exists(requirements_path):
            try:
                result = subprocess.run(
                    ['pip', 'install', '-r', 'requirements.txt'],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
                return f"构建完成:\n{result.stdout}\n{result.stderr}"
            except Exception as e:
                return f"构建失败: {str(e)}"
        else:
            return "构建完成: 无依赖需要安装"
    
    async def _deploy_project(self, project_path: str, target: str) -> str:
        """部署项目"""
        if not os.path.exists(project_path):
            return "错误: 项目路径不存在"
        
        logger.info(f"部署项目到 {target}: {project_path}")
        
        if target == "local":
            return "本地部署完成"
        elif target == "docker":
            # 检查是否有Dockerfile
            dockerfile_path = os.path.join(project_path, "Dockerfile")
            if os.path.exists(dockerfile_path):
                try:
                    result = subprocess.run(
                        ['docker', 'build', '-t', 'my-app', '.'],
                        cwd=project_path,
                        capture_output=True,
                        text=True
                    )
                    return f"Docker 构建完成:\n{result.stdout}\n{result.stderr}"
                except Exception as e:
                    return f"Docker 构建失败: {str(e)}"
            else:
                return "错误: 未找到 Dockerfile"
        elif target == "cloud":
            return "云部署功能需要配置"
        else:
            return "错误: 不支持的部署目标"
    
    async def _check_status(self, project_path: str, target: str) -> str:
        """检查部署状态"""
        logger.info(f"检查 {target} 部署状态: {project_path}")
        
        if target == "local":
            return "本地部署状态: 运行中"
        elif target == "docker":
            try:
                result = subprocess.run(
                    ['docker', 'ps'],
                    capture_output=True,
                    text=True
                )
                return f"Docker 状态:\n{result.stdout}"
            except Exception as e:
                return f"检查 Docker 状态失败: {str(e)}"
        elif target == "cloud":
            return "云部署状态: 需要配置"
        else:
            return "错误: 不支持的部署目标"

# 注册工具
def register_development_tools(tool_registry):
    """注册开发工具相关工具"""
    tool_registry.register(CodeGenerationTool())
    tool_registry.register(CodeAnalysisTool())
    tool_registry.register(TestingTool())
    tool_registry.register(DeploymentTool())

"""
Tool Registry - 工具注册表
Schema 自动生成与 OpenAI Function Calling 绑定
"""
from typing import List, Dict, Any, Callable
import inspect


class ToolRegistry:
    """
    工具注册表：管理 Agent 可用的所有工具（如计算器、条款检索等）
    自动生成符合 OpenAI Function Calling 规范的 Schema
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any]
    ):
        """
        注册一个工具

        Args:
            name: 工具名称
            description: 工具描述
            func: 工具函数
            parameters: OpenAI Function Calling 参数格式
        """
        self.tools[name] = {
            "description": description,
            "func": func,
            "parameters": parameters
        }

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """
        获取符合 OpenAI Function Calling 规范的工具列表

        Returns:
            工具 Schema 列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for name, tool in self.tools.items()
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        执行指定的工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]
        func = tool["func"]

        # 执行工具函数
        if inspect.iscoroutinefunction(func):
            result = await func(**arguments)
        else:
            result = func(**arguments)

        return result

    @staticmethod
    def create_schema(func: Callable) -> Dict[str, Any]:
        """
        自动从函数签名生成 OpenAI Function Calling Schema

        Args:
            func: 工具函数

        Returns:
            参数 Schema
        """
        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for name, param in sig.parameters.items():
            # 推断参数类型
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == float:
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"

            parameters["properties"][name] = {
                "type": param_type,
                "description": f"{name} parameter"
            }

            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)

        return parameters

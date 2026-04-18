from minibot.tools.base import BaseTool
import math

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform basic arithmetic operations and mathematical functions"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }

    async def run(self, expression: str) -> str:
        try:
            # Safe evaluation of mathematical expression
            # Note: This is a simplified implementation and may not be secure for all cases
            result = eval(expression, {"__builtins__": None}, {"math": math})
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"


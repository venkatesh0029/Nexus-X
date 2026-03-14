from backend.plugins.plugin_manager import plugin_tool
import ast
import operator

# Allowed math operators to prevent eval() injection
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

def _eval_expr(node):
    if isinstance(node, ast.Constant):  # Python 3.8+ replaces ast.Num
        return node.value
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return OPERATORS[type(node.op)](_eval_expr(node.left), _eval_expr(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return UNARY_OPERATORS[type(node.op)](_eval_expr(node.operand))
    else:
        raise TypeError(node)

@plugin_tool(
    name="calculate_math", 
    description='{"expression": "string"} - Safely evaluates a mathematical expression like "5 * (3 + 2)"'
)
def calculate_math(expression: str) -> str:
    """Safely calculates basic math equations without using eval()."""
    try:
        # Parse the expression into an AST and evaluate safely
        node = ast.parse(expression, mode='eval').body
        result = _eval_expr(node)
        return f"The result of '{expression}' is: {result}"
    except Exception as e:
        return f"Math calculation error: {str(e)}"

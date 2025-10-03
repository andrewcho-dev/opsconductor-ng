"""
Safe Mathematical Expression Evaluator

Evaluates mathematical expressions from YAML profiles without using eval().
Only supports whitelisted operations and variables.

Security:
- No arbitrary code execution
- Restricted AST parsing
- Whitelisted operations only
- Bounded computation
"""

import ast
import math
from typing import Dict, Any, Union


class SafeMathEvaluator:
    """
    Safe evaluator for mathematical expressions
    
    Supported operations:
    - Arithmetic: +, -, *, /, //, %, **
    - Functions: log, log10, sqrt, min, max, abs, ceil, floor
    - Constants: pi, e
    - Variables: N, pages, p95_latency, cost, and custom context vars
    
    Examples:
        "120 + 0.02 * N"
        "3000 + 400 * log(N)"
        "min(1000, N * 2)"
        "1 / (1 + time_ms / 1000)"
    """
    
    # Whitelisted operations
    ALLOWED_OPS = {
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd
    }
    
    # Whitelisted functions
    ALLOWED_FUNCTIONS = {
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'sqrt': math.sqrt,
        'min': min,
        'max': max,
        'abs': abs,
        'ceil': math.ceil,
        'floor': math.floor,
        'exp': math.exp,
    }
    
    # Whitelisted constants
    ALLOWED_CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
    }
    
    # Default variable values (fallbacks)
    DEFAULT_VARS = {
        'N': 0,
        'pages': 1,
        'p95_latency': 100,
        'cost': 1,
        'time_ms': 1000,
    }
    
    def __init__(self, max_depth: int = 20):
        """
        Initialize evaluator
        
        Args:
            max_depth: Maximum AST depth to prevent deeply nested expressions
        """
        self.max_depth = max_depth
    
    def evaluate(
        self,
        expression: Union[str, int, float],
        context: Dict[str, Any]
    ) -> float:
        """
        Safely evaluate a mathematical expression
        
        Args:
            expression: Mathematical expression string or numeric value
            context: Variable values (e.g., {'N': 100, 'p95_latency': 150})
            
        Returns:
            Evaluated result as float
            
        Raises:
            ValueError: If expression contains disallowed operations
            SyntaxError: If expression is malformed
        """
        # If already a number, return it
        if isinstance(expression, (int, float)):
            return float(expression)
        
        # Parse expression to AST
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise SyntaxError(f"Invalid expression syntax: {expression}") from e
        
        # Validate AST (no disallowed operations)
        self._validate_ast(tree.body, depth=0)
        
        # Build evaluation context
        eval_context = self._build_context(context)
        
        # Evaluate AST
        try:
            result = self._eval_node(tree.body, eval_context)
            return float(result)
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}") from e
    
    def _validate_ast(self, node: ast.AST, depth: int):
        """
        Validate AST node recursively
        
        Ensures only whitelisted operations are used
        """
        if depth > self.max_depth:
            raise ValueError(f"Expression too deeply nested (max depth: {self.max_depth})")
        
        # Check node type
        if isinstance(node, ast.BinOp):
            if type(node.op) not in self.ALLOWED_OPS:
                raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            self._validate_ast(node.left, depth + 1)
            self._validate_ast(node.right, depth + 1)
        
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.ALLOWED_OPS:
                raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            self._validate_ast(node.operand, depth + 1)
        
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed")
            if node.func.id not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Function {node.func.id} not allowed")
            for arg in node.args:
                self._validate_ast(arg, depth + 1)
        
        elif isinstance(node, ast.Name):
            # Variable reference - will be checked at eval time
            pass
        
        elif isinstance(node, ast.Constant):
            # Numeric constant - always safe
            pass
        
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            # Numeric constant - always safe
            pass
        
        else:
            raise ValueError(f"AST node type {type(node).__name__} not allowed")
    
    def _build_context(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build evaluation context with defaults and user values
        """
        context = {}
        
        # Add constants
        context.update(self.ALLOWED_CONSTANTS)
        
        # Add functions
        context.update(self.ALLOWED_FUNCTIONS)
        
        # Add default variables
        context.update(self.DEFAULT_VARS)
        
        # Override with user context
        context.update(user_context)
        
        return context
    
    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Union[int, float]:
        """
        Evaluate AST node recursively
        """
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ValueError("Division by zero")
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise ValueError("Division by zero")
                return left // right
            elif isinstance(node.op, ast.Mod):
                if right == 0:
                    raise ValueError("Modulo by zero")
                return left % right
            elif isinstance(node.op, ast.Pow):
                # Limit exponent to prevent huge numbers
                if abs(right) > 100:
                    raise ValueError("Exponent too large")
                return left ** right
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
        
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            func = context[func_name]
            
            # Evaluate arguments
            args = [self._eval_node(arg, context) for arg in node.args]
            
            # Call function
            return func(*args)
        
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name not in context:
                raise ValueError(f"Variable '{var_name}' not defined in context")
            return context[var_name]
        
        elif isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        
        else:
            raise ValueError(f"Cannot evaluate node type {type(node).__name__}")


# Global instance
_evaluator = SafeMathEvaluator()


def safe_eval(expression: Union[str, int, float], context: Dict[str, Any]) -> float:
    """
    Convenience function for safe evaluation
    
    Args:
        expression: Mathematical expression or numeric value
        context: Variable values
        
    Returns:
        Evaluated result as float
    """
    return _evaluator.evaluate(expression, context)
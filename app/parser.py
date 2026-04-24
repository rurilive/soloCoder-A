import ast
import numpy as np
from typing import Dict, List, Callable, Any


class ParseError(Exception):
    pass


ALLOWED_CONSTANTS = {
    'pi': np.pi,
    'e': np.e,
}

ALLOWED_FUNCTIONS = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'asin': np.arcsin,
    'acos': np.arccos,
    'atan': np.arctan,
    'exp': np.exp,
    'log': np.log,
    'log10': np.log10,
    'sqrt': np.sqrt,
    'abs': np.abs,
    'sign': np.sign,
    'max': np.maximum,
    'min': np.minimum,
    'pow': np.power,
}

ALLOWED_VARIABLES = {'x', 'y', 'z'}

ALLOWED_OPERATORS = {
    ast.Add: np.add,
    ast.Sub: np.subtract,
    ast.Mult: np.multiply,
    ast.Div: np.divide,
    ast.Pow: np.power,
    ast.BitXor: np.power,
}

ALLOWED_UNARY_OPERATORS = {
    ast.USub: np.negative,
    ast.UAdd: lambda x: x,
}


class SafeExpressionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.variables: set = set()
        self.errors: List[str] = []

    def visit_Module(self, node: ast.Module) -> Any:
        if len(node.body) != 1:
            self.errors.append("表达式必须是单一语句")
            return
        return self.visit(node.body[0])

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Expr(self, node: ast.Expr) -> Any:
        return self.visit(node.value)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float, complex)):
            return node.value
        self.errors.append(f"不支持的常量类型: {type(node.value)}")
        return None

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            name = node.id
            if name in ALLOWED_VARIABLES:
                self.variables.add(name)
                return name
            elif name in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[name]
            else:
                self.errors.append(f"不允许的标识符: {name}")
                return None
        self.errors.append(f"不允许的 Name 上下文: {type(node.ctx)}")
        return None

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        op_type = type(node.op)
        if op_type not in ALLOWED_OPERATORS:
            self.errors.append(f"不允许的二元运算符: {op_type.__name__}")
            return None
        
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if left is None or right is None:
            return None
        
        return (ALLOWED_OPERATORS[op_type], left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARY_OPERATORS:
            self.errors.append(f"不允许的一元运算符: {op_type.__name__}")
            return None
        
        operand = self.visit(node.operand)
        if operand is None:
            return None
        
        return (ALLOWED_UNARY_OPERATORS[op_type], operand)

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            self.errors.append("只允许通过名称调用函数")
            return None
        
        func_name = node.func.id
        if func_name not in ALLOWED_FUNCTIONS:
            self.errors.append(f"不允许的函数: {func_name}")
            return None
        
        if func_name in ('max', 'min', 'pow'):
            if len(node.args) != 2:
                self.errors.append(f"函数 {func_name} 需要恰好 2 个参数")
                return None
        else:
            if len(node.args) != 1:
                self.errors.append(f"函数 {func_name} 需要恰好 1 个参数")
                return None
        
        if node.keywords:
            self.errors.append("不支持关键字参数")
            return None
        
        args = []
        for arg in node.args:
            arg_val = self.visit(arg)
            if arg_val is None:
                return None
            args.append(arg_val)
        
        return (ALLOWED_FUNCTIONS[func_name], *args)

    def generic_visit(self, node: ast.AST) -> Any:
        self.errors.append(f"不允许的 AST 节点类型: {type(node).__name__}")
        return None


def _build_evaluator(parsed_expr: Any) -> Callable:
    if isinstance(parsed_expr, tuple):
        func = parsed_expr[0]
        args = parsed_expr[1:]
        arg_evaluators = [_build_evaluator(arg) for arg in args]
        return lambda **vars: func(*[ev(**vars) for ev in arg_evaluators])
    elif parsed_expr in ALLOWED_VARIABLES:
        return lambda **vars: vars[parsed_expr]
    else:
        return lambda **vars: parsed_expr


def parse_expression(expression: str) -> Dict:
    expression = expression.replace('^', '**')
    
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as e:
        raise ParseError(f"语法错误: {e}")
    
    visitor = SafeExpressionVisitor()
    parsed_expr = visitor.visit(tree)
    
    if visitor.errors:
        raise ParseError("; ".join(visitor.errors))
    
    if parsed_expr is None:
        raise ParseError("无法解析表达式")
    
    variables = sorted(visitor.variables)
    
    if not variables:
        raise ParseError("表达式中未找到变量 (x, y, z)")
    
    for var in variables:
        if var not in ALLOWED_VARIABLES:
            raise ParseError(f"不允许的变量: {var}")
    
    if 'z' in variables:
        expr_type = '3d'
        expected_vars = {'x', 'y', 'z'}
    elif 'y' in variables:
        expr_type = '2d'
        expected_vars = {'x', 'y'}
    else:
        expr_type = '2d'
        expected_vars = {'x'}
    
    actual_vars = set(variables)
    if not actual_vars.issubset(expected_vars):
        extra = actual_vars - expected_vars
        raise ParseError(f"意外的变量: {sorted(extra)}")
    
    evaluator = _build_evaluator(parsed_expr)
    
    def func(*args):
        if expr_type == '3d':
            if len(args) != 3:
                raise ValueError("3D 函数需要 3 个参数 (x, y, z)")
            return evaluator(x=args[0], y=args[1], z=args[2])
        else:
            if len(args) != 2:
                raise ValueError("2D 函数需要 2 个参数 (x, y)")
            return evaluator(x=args[0], y=args[1])
    
    return {
        'func': func,
        'variables': variables,
        'type': expr_type,
    }

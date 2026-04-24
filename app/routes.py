from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal
from app.parser import parse_expression, ParseError
from app.calculator import generate_surface
from app.operations import apply_set_operation
from functools import lru_cache
import hashlib
import orjson

router = APIRouter()

PRESETS = [
    {
        "name": "抛物面",
        "expression": "x^2 + y^2",
        "type": "2d",
        "color": "#ff6b6b",
        "description": "z = x² + y²"
    },
    {
        "name": "正弦波",
        "expression": "sin(x) * cos(y)",
        "type": "2d",
        "color": "#4ecdc4",
        "description": "z = sin(x)·cos(y)"
    },
    {
        "name": "高斯函数",
        "expression": "exp(-x^2 - y^2)",
        "type": "2d",
        "color": "#45b7d1",
        "description": "z = e^(-x²-y²)"
    },
    {
        "name": "马鞍面",
        "expression": "x^2 - y^2",
        "type": "2d",
        "color": "#f9ca24",
        "description": "z = x² - y²"
    }
]

VALID_OPERATIONS = ['none', 'union', 'intersection', 'difference', 'symmetric_difference']


def _orjson_response(content: Any) -> Response:
    return Response(
        content=orjson.dumps(content, option=orjson.OPT_SERIALIZE_NUMPY),
        media_type="application/json"
    )


class FunctionInput(BaseModel):
    expression: str
    name: Optional[str] = None
    color: Optional[str] = "#ff6b6b"


class RenderParams(BaseModel):
    x_min: float = -5.0
    x_max: float = 5.0
    y_min: float = -5.0
    y_max: float = 5.0
    z_min: float = -5.0
    z_max: float = 5.0
    resolution: int = 50
    isovalue: float = 0.0
    epsilon: float = 0.5


class RenderRequest(BaseModel):
    functions: List[FunctionInput]
    operation: Literal['none', 'union', 'intersection', 'difference', 'symmetric_difference'] = "none"
    params: RenderParams = RenderParams()


@lru_cache(maxsize=128)
def _cached_parse_expression(expression: str):
    return parse_expression(expression)


def _make_cache_key(
    expressions: tuple,
    operation: str,
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    resolution: int,
    epsilon: float
) -> str:
    key_parts = [
        str(expressions),
        operation,
        f"{x_min},{x_max},{y_min},{y_max}",
        str(resolution),
        str(epsilon)
    ]
    key_str = "|".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


_render_cache: Dict[str, Any] = {}
_MAX_CACHE_SIZE = 32


@router.get("/presets")
async def get_presets():
    return _orjson_response({
        "success": True,
        "presets": PRESETS
    })


@router.post("/render")
async def post_render(request: RenderRequest):
    if not request.functions:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "函数列表不能为空"
            }
        )
    
    expressions = tuple(f.expression for f in request.functions)
    cache_key = _make_cache_key(
        expressions,
        request.operation,
        request.params.x_min, request.params.x_max,
        request.params.y_min, request.params.y_max,
        request.params.resolution,
        request.params.epsilon
    )
    
    if cache_key in _render_cache:
        return _orjson_response({
            "success": True,
            "data": _render_cache[cache_key],
            "_cached": True
        })
    
    parsed_functions = []
    expression_types = []
    
    for i, func_input in enumerate(request.functions):
        try:
            parsed = _cached_parse_expression(func_input.expression)
            parsed_functions.append({
                'func': parsed['func'],
                'type': parsed['type'],
                'expression': func_input.expression,
                'name': func_input.name,
                'color': func_input.color,
                'index': i
            })
            expression_types.append(parsed['type'])
        except ParseError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": f"函数 {i+1} 解析错误: {str(e)}"
                }
            )
    
    functions_3d = [f for f in parsed_functions if f['type'] == '3d']
    if functions_3d:
        exprs = [f"'{f['expression']}'" for f in functions_3d]
        indices = [str(f['index'] + 1) for f in functions_3d]
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"3D 函数暂不支持。函数 {', '.join(indices)}: {', '.join(exprs)}"
            }
        )
    
    if len(set(expression_types)) > 1:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "函数类型不一致，不能混合 2D 和 3D 函数"
            }
        )
    
    if request.operation not in VALID_OPERATIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": f"无效的运算类型: {request.operation}。有效类型: {VALID_OPERATIONS}"
            }
        )
    
    surfaces = []
    colors = []
    x_range = (request.params.x_min, request.params.x_max)
    y_range = (request.params.y_min, request.params.y_max)
    
    for parsed_func in parsed_functions:
        surface = generate_surface(
            func=parsed_func['func'],
            x_range=x_range,
            y_range=y_range,
            resolution=request.params.resolution
        )
        surfaces.append(surface)
        colors.append(parsed_func['color'])
    
    try:
        result = apply_set_operation(
            surfaces=surfaces,
            operation=request.operation,
            epsilon=request.params.epsilon
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e)
            }
        )
    
    if result['type'] == 'multiple':
        for i, surface in enumerate(result['surfaces']):
            if i < len(colors):
                surface['color'] = colors[i]
    
    if len(_render_cache) >= _MAX_CACHE_SIZE:
        first_key = next(iter(_render_cache.keys()))
        del _render_cache[first_key]
    _render_cache[cache_key] = result
    
    return _orjson_response({
        "success": True,
        "data": result
    })

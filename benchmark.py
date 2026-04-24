import time
import numpy as np
import sys
sys.path.insert(0, '.')

from app.parser import parse_expression
from app.calculator import generate_surface
from app.operations import apply_set_operation


def timeit(name, func, repeats=3):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    avg = np.mean(times)
    min_t = np.min(times)
    print(f"[{name}] avg={avg*1000:.2f}ms, min={min_t*1000:.2f}ms")
    return result, avg


def benchmark_parser():
    expressions = [
        "x^2 + y^2",
        "sin(x) * cos(y)",
        "exp(-x^2 - y^2)",
        "x^2 - y^2 + sin(x*y)",
        "max(x^2, y^2)",
    ]
    
    print("=== Parser 测试 ===")
    for expr in expressions:
        result, avg = timeit(f"parse: {expr[:20]}", lambda: parse_expression(expr))
    
    return parse_expression("x^2 + y^2")


def benchmark_calculator(resolutions=[25, 50, 100, 200]):
    func_info = parse_expression("x^2 + y^2")
    func = func_info['func']
    
    print("\n=== Calculator 测试 (曲面生成) ===")
    
    for res in resolutions:
        result, avg = timeit(
            f"resolution={res:3} ({res}x{res}={res*res} vertices)",
            lambda r=res: generate_surface(func, (-5, 5), (-5, 5), r)
        )
        verts = len(result['vertices'])
        faces = len(result['faces'])
        print(f"    -> vertices={verts}, faces={faces}")
    
    return generate_surface(func, (-5, 5), (-5, 5), 100)


def benchmark_operations():
    print("\n=== Operations 测试 (集合运算) ===")
    
    func1 = parse_expression("x^2 + y^2")['func']
    func2 = parse_expression("0 * x + 5")['func']
    
    surf1 = generate_surface(func1, (-3, 3), (-3, 3), 100)
    surf2 = generate_surface(func2, (-3, 3), (-3, 3), 100)
    
    operations = ['union', 'intersection', 'difference', 'symmetric_difference']
    
    for op in operations:
        result, avg = timeit(
            f"op={op}",
            lambda o=op: apply_set_operation([surf1, surf2], o, epsilon=0.5)
        )
    
    return surf1, surf2


def benchmark_full_flow():
    print("\n=== 完整流程测试 ===")
    
    def full_render():
        func_info = parse_expression("sin(x) * cos(y)")
        surface = generate_surface(func_info['func'], (-5, 5), (-5, 5), 100)
        result = apply_set_operation([surface], 'none')
        return result
    
    result, avg = timeit("完整渲染 (parse + calc + format)", full_render)
    
    print(f"\n=== 分解测试 ===")
    
    expr = "sin(x) * cos(y)"
    
    _, t_parse = timeit("1. parse_expression", lambda: parse_expression(expr))
    
    func_info = parse_expression(expr)
    _, t_calc = timeit("2. generate_surface (100x100)", 
                        lambda: generate_surface(func_info['func'], (-5, 5), (-5, 5), 100))
    
    surf = generate_surface(func_info['func'], (-5, 5), (-5, 5), 100)
    _, t_format = timeit("3. apply_set_operation (none)", 
                          lambda: apply_set_operation([surf], 'none'))
    
    total = t_parse + t_calc + t_format
    print(f"\n分解比例:")
    print(f"  Parse:      {t_parse*1000:.2f}ms ({t_parse/total*100:.1f}%)")
    print(f"  Calculate:  {t_calc*1000:.2f}ms ({t_calc/total*100:.1f}%)")
    print(f"  Format:     {t_format*1000:.2f}ms ({t_format/total*100:.1f}%)")


if __name__ == "__main__":
    print("=" * 60)
    print("           函数可视化工具 - 性能基准测试")
    print("=" * 60)
    
    benchmark_parser()
    benchmark_calculator()
    benchmark_operations()
    benchmark_full_flow()
    
    print("\n" + "=" * 60)
    print("           基准测试完成")
    print("=" * 60)

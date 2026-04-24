import time
import numpy as np
import sys
sys.path.insert(0, '.')

from app.parser import parse_expression, _build_evaluator, SafeExpressionVisitor
import ast


def timeit(name, func, repeats=5):
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


def test_expression_evaluation_speed():
    print("=" * 60)
    print("表达式计算性能测试")
    print("=" * 60)
    
    expressions = [
        ("x^2 + y^2", "简单二次"),
        ("sin(x) * cos(y)", "三角函数"),
        ("exp(-x^2 - y^2)", "高斯函数"),
        ("max(x^2, y^2) + min(x, y)", "max/min"),
        ("x^2 - y^2 + sin(x*y) * cos(x)", "复合"),
    ]
    
    resolutions = [50, 100, 200]
    
    for expr, desc in expressions:
        print(f"\n--- {desc}: {expr} ---")
        func_info = parse_expression(expr)
        func = func_info['func']
        
        for res in resolutions:
            n = res * res
            x = np.linspace(-5, 5, res, dtype=np.float64)
            y = np.linspace(-5, 5, res, dtype=np.float64)
            X, Y = np.meshgrid(x, y)
            
            _, avg = timeit(
                f"  {res}x{res} (n={n})",
                lambda X=X, Y=Y: func(X, Y)
            )
            
            ops_per_sec = n / avg if avg > 0 else float('inf')
            print(f"      → {ops_per_sec/1e6:.1f} M ops/sec")


def test_ast_vs_eval():
    print("\n" + "=" * 60)
    print("AST evaluator vs 直接 numpy 对比")
    print("=" * 60)
    
    res = 200
    x = np.linspace(-5, 5, res, dtype=np.float64)
    y = np.linspace(-5, 5, res, dtype=np.float64)
    X, Y = np.meshgrid(x, y)
    
    expr = "sin(x) * cos(y) + x^2 - y^2"
    
    func_info = parse_expression(expr)
    ast_func = func_info['func']
    
    def direct_func(X, Y):
        return np.sin(X) * np.cos(Y) + np.power(X, 2) - np.power(Y, 2)
    
    print(f"\n表达式: {expr}")
    print(f"分辨率: {res}x{res} = {res*res} points")
    
    print("\n--- AST evaluator ---")
    _, t_ast = timeit("计算", lambda: ast_func(X, Y))
    
    print("\n--- 直接 numpy ---")
    _, t_direct = timeit("计算", lambda: direct_func(X, Y))
    
    print(f"\n对比:")
    print(f"  AST: {t_ast*1000:.2f}ms")
    print(f"  直接: {t_direct*1000:.2f}ms")
    print(f"  比例: {t_ast/t_direct:.1f}x 较慢")


def test_cache_impact():
    print("\n" + "=" * 60)
    print("缓存影响测试")
    print("=" * 60)
    
    expr = "x^2 + y^2 + sin(x*y)"
    
    print("\n--- 重复 parse_expression ---")
    for i in range(5):
        start = time.perf_counter()
        parse_expression(expr)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  第{i+1}次: {elapsed:.3f}ms")
    
    print("\n--- 重复计算 (相同输入) ---")
    func_info = parse_expression(expr)
    func = func_info['func']
    
    res = 100
    x = np.linspace(-5, 5, res, dtype=np.float64)
    y = np.linspace(-5, 5, res, dtype=np.float64)
    X, Y = np.meshgrid(x, y)
    
    for i in range(5):
        start = time.perf_counter()
        result = func(X, Y)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  第{i+1}次: {elapsed:.2f}ms, sum={result.sum():.2f}")


if __name__ == "__main__":
    test_expression_evaluation_speed()
    test_ast_vs_eval()
    test_cache_impact()

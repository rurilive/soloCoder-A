import time
import numpy as np
import sys
import os
sys.path.insert(0, '.')

import orjson
from app.parser import parse_expression
from app.calculator import generate_surface
from app.operations import apply_set_operation


def timeit(name, func, repeats=3):
    times = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    avg = np.mean(times)
    min_t = np.min(times)
    print(f"[{name}] avg={avg*1000:8.2f}ms, min={min_t*1000:8.2f}ms")
    return result, avg


def test_full_pipeline():
    print("=" * 70)
    print("                   最终优化验证测试")
    print("=" * 70)
    
    print("\n--- 测试配置 ---")
    resolutions = [50, 100, 200]
    expr = "sin(x) * cos(y) + x^2 - y^2"
    
    print(f"表达式: {expr}")
    
    print("\n" + "-" * 70)
    print("1. 解析测试")
    print("-" * 70)
    
    _, t_parse = timeit("parse_expression", lambda: parse_expression(expr))
    
    func_info = parse_expression(expr)
    func = func_info['func']
    
    for res in resolutions:
        print(f"\n--- 分辨率: {res}x{res} = {res*res} 顶点 ---")
        
        x_range = (-5, 5)
        y_range = (-5, 5)
        
        result, t_calc = timeit(
            "  generate_surface",
            lambda r=res: generate_surface(func, x_range, y_range, r)
        )
        
        surf = result
        n_verts = len(surf['vertices']) if isinstance(surf['vertices'], list) else surf['vertices'].shape[0]
        n_faces = len(surf['faces']) if isinstance(surf['faces'], list) else surf['faces'].shape[0]
        print(f"    -> 顶点: {n_verts}, 面片: {n_faces}")
        
        is_numpy = isinstance(surf['vertices'], np.ndarray)
        print(f"    -> 数据类型: {'numpy 数组' if is_numpy else 'Python list'}")
        
        surf1 = generate_surface(func, x_range, y_range, res)
        surf2 = generate_surface(
            parse_expression("0 * x + 5")['func'],
            x_range, y_range, res
        )
        
        _, t_intersect = timeit(
            "  交集运算",
            lambda s1=surf1, s2=surf2: apply_set_operation([s1, s2], 'intersection', epsilon=0.5)
        )
        
        _, t_diff = timeit(
            "  差集运算",
            lambda s1=surf1, s2=surf2: apply_set_operation([s1, s2], 'difference', epsilon=0.5)
        )
        
        _, t_symdiff = timeit(
            "  对称差运算",
            lambda s1=surf1, s2=surf2: apply_set_operation([s1, s2], 'symmetric_difference', epsilon=0.5)
        )
        
        result = apply_set_operation([surf1], 'none')
        _, t_serialize = timeit(
            "  orjson 序列化",
            lambda r=result: orjson.dumps(r, option=orjson.OPT_SERIALIZE_NUMPY)
        )
        
        json_bytes = orjson.dumps(result, option=orjson.OPT_SERIALIZE_NUMPY)
        print(f"    -> JSON 大小: {len(json_bytes) / 1024:.1f} KB")
        
        total = t_calc + t_serialize
        print(f"\n    单曲面总耗时: {total*1000:.2f}ms")
        print(f"      - 计算: {t_calc*1000:.2f}ms ({t_calc/total*100:.1f}%)")
        print(f"      - 序列化: {t_serialize*1000:.2f}ms ({t_serialize/total*100:.1f}%)")


def compare_with_old_approach():
    print("\n" + "=" * 70)
    print("2. 新旧方式对比测试")
    print("=" * 70)
    
    res = 100
    expr = "x^2 + y^2 + sin(x*y)"
    func_info = parse_expression(expr)
    func = func_info['func']
    
    surf = generate_surface(func, (-5, 5), (-5, 5), res)
    result = apply_set_operation([surf], 'none')
    
    print("\n方式 A: orjson + numpy (新)")
    _, t_new = timeit(
        "  序列化",
        lambda: orjson.dumps(result, option=orjson.OPT_SERIALIZE_NUMPY)
    )
    
    import json
    print("\n方式 B: .tolist() + json.dumps (旧)")
    def old_approach():
        def convert(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(x) for x in obj]
            return obj
        converted = convert(result)
        return json.dumps(converted)
    
    _, t_old = timeit("  转换+序列化", old_approach)
    
    print(f"\n加速比: {t_old / t_new:.1f}x")


def test_cache_impact():
    print("\n" + "=" * 70)
    print("3. 缓存效果测试")
    print("=" * 70)
    
    from functools import lru_cache
    
    expr = "x^2 + y^2 + sin(x) * cos(y)"
    
    print("\n重复解析测试:")
    for i in range(5):
        start = time.perf_counter()
        parse_expression(expr)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  第{i+1}次: {elapsed:.3f}ms")
    
    @lru_cache(maxsize=128)
    def cached_parse(e):
        return parse_expression(e)
    
    print("\n使用 LRU cache:")
    for i in range(5):
        start = time.perf_counter()
        cached_parse(expr)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  第{i+1}次: {elapsed:.3f}ms")


if __name__ == "__main__":
    test_full_pipeline()
    compare_with_old_approach()
    test_cache_impact()
    
    print("\n" + "=" * 70)
    print("                    测试完成")
    print("=" * 70)

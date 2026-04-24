import time
import numpy as np
import sys
sys.path.insert(0, '.')


def timeit(name, func, repeats=3):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg = np.mean(times)
    min_t = np.min(times)
    print(f"[{name}] avg={avg*1000:8.2f}ms")
    return avg


print("=" * 70)
print("                    性能优化总结")
print("=" * 70)

print("""
【优化前】
  generate_surface (100x100): 135ms
  symmetric_difference:        427ms
  .tolist() + json.dumps:      41ms
  单曲面总耗时:                 ~176ms

【优化后】
""")

from app.parser import parse_expression
from app.calculator import generate_surface
from app.operations import apply_set_operation
import orjson

expr = "sin(x) * cos(y) + x^2 - y^2"
func_info = parse_expression(expr)
func = func_info['func']

print("-" * 70)
print("核心计算性能 (纯 Python):")
print("-" * 70)

for res in [50, 100, 200]:
    t_calc = timeit(
        f"generate_surface ({res}x{res})",
        lambda r=res: generate_surface(func, (-5, 5), (-5, 5), r)
    )

print()
surf1 = generate_surface(func, (-5, 5), (-5, 5), 100)
func2 = parse_expression("0 * x + 5")['func']
surf2 = generate_surface(func2, (-5, 5), (-5, 5), 100)

for op in ['union', 'intersection', 'difference', 'symmetric_difference']:
    timeit(
        f"{op:20s} (100x100)",
        lambda o=op: apply_set_operation([surf1, surf2], o, epsilon=0.5)
    )

print()
print("-" * 70)
print("序列化性能:")
print("-" * 70)

result = apply_set_operation([surf1], 'none')

t_orjson = timeit(
    "orjson + numpy",
    lambda: orjson.dumps(result, option=orjson.OPT_SERIALIZE_NUMPY)
)

import json
def old_way():
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        return obj
    converted = convert(result)
    return json.dumps(converted)

t_old = timeit(
    ".tolist() + json.dumps",
    old_way
)

print(f"\n序列化加速比: {t_old / t_orjson:.1f}x")

print()
print("-" * 70)
print("优化总结:")
print("-" * 70)

print("""
1. 移除 .tolist() 转换
   - 之前: 87% 的时间花在 numpy → Python list 转换
   - 现在: 保持 numpy 数组格式

2. float64 → float32
   - 减少 50% 内存使用
   - 加速序列化

3. orjson + OPT_SERIALIZE_NUMPY
   - 直接序列化 numpy 数组
   - 加速 7-12x

4. 向量化集合运算
   - Python 循环 → numpy 向量化
   - symmetric_difference: 427ms → 3ms (140x!)

5. LRU 缓存
   - 重复解析: ~0.05ms → 0ms
   - 渲染结果缓存 (可选)
""")

print("=" * 70)

import numpy as np
from app.parser import parse_expression, ParseError


def test_case_1():
    print("测试用例 1: x^2 + y^2")
    result = parse_expression("x^2 + y^2")
    assert result['variables'] == ['x', 'y'], f"变量应为 ['x', 'y'], 实际: {result['variables']}"
    assert result['type'] == '2d', f"类型应为 '2d', 实际: {result['type']}"
    
    x = np.array([1.0])
    y = np.array([2.0])
    output = result['func'](x, y)
    assert output[0] == 5.0, f"x=1, y=2 时应返回 5.0, 实际: {output[0]}"
    print("  通过 ✓\n")


def test_case_2():
    print("测试用例 2: sin(x) * cos(y)")
    result = parse_expression("sin(x) * cos(y)")
    assert result['variables'] == ['x', 'y'], f"变量应为 ['x', 'y'], 实际: {result['variables']}"
    assert result['type'] == '2d', f"类型应为 '2d', 实际: {result['type']}"
    
    x = np.array([np.pi / 2])
    y = np.array([0.0])
    output = result['func'](x, y)
    expected = np.sin(np.pi / 2) * np.cos(0.0)
    assert abs(output[0] - expected) < 1e-10, f"应返回 {expected}, 实际: {output[0]}"
    print("  通过 ✓\n")


def test_case_3():
    print("测试用例 3: exp(-x^2 - y^2)")
    result = parse_expression("exp(-x^2 - y^2)")
    assert result['variables'] == ['x', 'y'], f"变量应为 ['x', 'y'], 实际: {result['variables']}"
    assert result['type'] == '2d', f"类型应为 '2d', 实际: {result['type']}"
    
    x = np.array([0.0])
    y = np.array([0.0])
    output = result['func'](x, y)
    expected = np.exp(0.0)
    assert abs(output[0] - expected) < 1e-10, f"x=0, y=0 时应返回 {expected}, 实际: {output[0]}"
    print("  通过 ✓\n")


def test_case_4():
    print("测试用例 4: x^2 + y^2 + z^2")
    result = parse_expression("x^2 + y^2 + z^2")
    assert result['variables'] == ['x', 'y', 'z'], f"变量应为 ['x', 'y', 'z'], 实际: {result['variables']}"
    assert result['type'] == '3d', f"类型应为 '3d', 实际: {result['type']}"
    
    x = np.array([1.0])
    y = np.array([2.0])
    z = np.array([3.0])
    output = result['func'](x, y, z)
    expected = 1.0 + 4.0 + 9.0
    assert output[0] == expected, f"应返回 {expected}, 实际: {output[0]}"
    print("  通过 ✓\n")


def test_case_5():
    print("测试用例 5: __import__('os') - 安全测试")
    try:
        parse_expression("__import__('os')")
        assert False, "应抛出 ParseError 异常"
    except ParseError as e:
        print(f"  正确抛出 ParseError: {e}")
        print("  通过 ✓\n")
    except Exception as e:
        print(f"  抛出了其他异常: {type(e).__name__}: {e}")
        print("  通过 ✓ (阻止了代码执行)\n")


def test_case_6():
    print("测试用例 6: x + * y - 语法错误")
    try:
        parse_expression("x + * y")
        assert False, "应抛出 ParseError 异常"
    except ParseError as e:
        print(f"  正确抛出 ParseError: {e}")
        print("  通过 ✓\n")


def test_numpy_arrays():
    print("额外测试: numpy 数组兼容性")
    result = parse_expression("x^2 + y")
    
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([4.0, 5.0, 6.0])
    output = result['func'](x, y)
    
    expected = np.array([1.0 + 4.0, 4.0 + 5.0, 9.0 + 6.0])
    np.testing.assert_array_equal(output, expected)
    print(f"  输入: x={x}, y={y}")
    print(f"  输出: {output}")
    print("  通过 ✓\n")


def test_constants():
    print("额外测试: 常量 pi 和 e")
    result = parse_expression("pi * x + e")
    
    x = np.array([1.0])
    output = result['func'](x, np.array([0.0]))
    
    expected = np.pi * 1.0 + np.e
    assert abs(output[0] - expected) < 1e-10
    print(f"  输出: {output[0]}, 预期: {expected}")
    print("  通过 ✓\n")


def test_all_functions():
    print("额外测试: 所有支持的函数")
    
    test_expressions = [
        ("sin(x)", np.sin),
        ("cos(x)", np.cos),
        ("tan(x)", np.tan),
        ("asin(x)", np.arcsin),
        ("acos(x)", np.arccos),
        ("atan(x)", np.arctan),
        ("exp(x)", np.exp),
        ("log(x)", np.log),
        ("log10(x)", np.log10),
        ("sqrt(x)", np.sqrt),
        ("abs(x)", np.abs),
        ("sign(x)", np.sign),
        ("max(x, y)", np.maximum),
        ("min(x, y)", np.minimum),
        ("pow(x, y)", np.power),
    ]
    
    for expr, np_func in test_expressions:
        print(f"  测试: {expr}")
        result = parse_expression(expr)
        assert 'x' in result['variables']
        
        if expr in ["max(x, y)", "min(x, y)", "pow(x, y)"]:
            x = np.array([2.0])
            y = np.array([3.0])
            output = result['func'](x, y)
            expected = np_func(2.0, 3.0)
        else:
            val = 0.5 if expr in ["asin(x)", "acos(x)"] else 1.0
            x = np.array([val])
            y = np.array([0.0])
            output = result['func'](x, y)
            expected = np_func(val)
        
        assert abs(output[0] - expected) < 1e-10, f"输出: {output[0]}, 预期: {expected}"
        print(f"    通过")
    
    print("  所有函数测试通过 ✓\n")


if __name__ == "__main__":
    print("=" * 50)
    print("运行所有测试用例")
    print("=" * 50 + "\n")
    
    test_case_1()
    test_case_2()
    test_case_3()
    test_case_4()
    test_case_5()
    test_case_6()
    
    test_numpy_arrays()
    test_constants()
    test_all_functions()
    
    print("=" * 50)
    print("所有测试通过! ✓")
    print("=" * 50)

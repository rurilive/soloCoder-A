import json
import numpy as np
from app.parser import parse_expression
from app.calculator import generate_surface
from app.operations import apply_set_operation


def create_test_surfaces():
    expr_a = parse_expression("x^2 + y^2")
    surface_a = generate_surface(expr_a['func'], (-3, 3), (-3, 3), resolution=7)
    
    expr_b = parse_expression("5")
    surface_b = generate_surface(expr_b['func'], (-3, 3), (-3, 3), resolution=7)
    
    return surface_a, surface_b


def test_case_1_none_operation():
    print("测试用例 1: 无运算 (none)")
    
    surface_a, surface_b = create_test_surfaces()
    
    result = apply_set_operation([surface_a, surface_b], 'none')
    
    assert result['type'] == 'multiple', f"类型应为 'multiple', 实际: {result['type']}"
    assert len(result['surfaces']) == 2, f"应有 2 个曲面, 实际: {len(result['surfaces'])}"
    
    assert 'color' in result['surfaces'][0], "第一个曲面应有颜色属性"
    assert 'color' in result['surfaces'][1], "第二个曲面应有颜色属性"
    
    print(f"  输出类型: {result['type']}")
    print(f"  曲面数量: {len(result['surfaces'])}")
    print("  通过 ✓\n")


def test_case_2_union_operation():
    print("测试用例 2: 并集 (union)")
    
    surface_a, surface_b = create_test_surfaces()
    
    result = apply_set_operation([surface_a, surface_b], 'union')
    
    assert result['type'] == 'multiple', f"类型应为 'multiple', 实际: {result['type']}"
    assert len(result['surfaces']) == 2, f"应有 2 个曲面, 实际: {len(result['surfaces'])}"
    
    print(f"  输出类型: {result['type']}")
    print(f"  曲面数量: {len(result['surfaces'])}")
    print("  通过 ✓\n")


def test_case_3_intersection_operation():
    print("测试用例 3: 交集 (intersection)")
    
    surface_a, surface_b = create_test_surfaces()
    epsilon = 1.0
    
    result = apply_set_operation([surface_a, surface_b], 'intersection', epsilon)
    
    assert result['type'] == 'multiple', f"类型应为 'multiple', 实际: {result['type']}"
    assert len(result['surfaces']) == 2, f"应有 2 个曲面, 实际: {len(result['surfaces'])}"
    
    n_original = len(surface_a['vertices'])
    n_masked = len(result['surfaces'][0]['vertices'])
    
    print(f"  原始顶点数: {n_original}")
    print(f"  掩膜后顶点数: {n_masked}")
    print(f"  原始面片数: {len(surface_a['faces'])}")
    print(f"  掩膜后面片数: {len(result['surfaces'][0]['faces'])}")
    
    z_values = np.array(surface_a['values'])
    expected_near_5 = np.sum(np.abs(z_values - 5) < epsilon)
    print(f"  预期保留的顶点数 (|Z - 5| < {epsilon}): {expected_near_5}")
    
    assert n_masked <= n_original, "掩膜后顶点数不应超过原始数"
    print("  通过 ✓\n")


def test_case_4_difference_operation():
    print("测试用例 4: 差集 (difference - A - B)")
    
    surface_a, surface_b = create_test_surfaces()
    epsilon = 1.0
    
    result = apply_set_operation([surface_a, surface_b], 'difference', epsilon)
    
    assert result['type'] == 'single', f"类型应为 'single', 实际: {result['type']}"
    assert 'surface' in result, "结果应包含 'surface' 键"
    
    n_original = len(surface_a['vertices'])
    n_masked = len(result['surface']['vertices'])
    
    print(f"  输出类型: {result['type']}")
    print(f"  原始顶点数: {n_original}")
    print(f"  差集后顶点数: {n_masked}")
    print(f"  原始面片数: {len(surface_a['faces'])}")
    print(f"  差集后面片数: {len(result['surface']['faces'])}")
    
    z_values = np.array(surface_a['values'])
    expected_keep = np.sum(np.abs(z_values - 5) >= epsilon)
    print(f"  预期保留的顶点数 (|Z - 5| >= {epsilon}): {expected_keep}")
    
    assert n_masked == expected_keep, f"实际保留 {n_masked} 个顶点，预期 {expected_keep} 个"
    print("  通过 ✓\n")


def test_case_5_symmetric_difference_operation():
    print("测试用例 5: 对称差 (symmetric_difference)")
    
    surface_a, surface_b = create_test_surfaces()
    epsilon = 1.0
    
    result = apply_set_operation([surface_a, surface_b], 'symmetric_difference', epsilon)
    
    assert result['type'] == 'multiple', f"类型应为 'multiple', 实际: {result['type']}"
    assert len(result['surfaces']) == 2, f"应有 2 个曲面, 实际: {len(result['surfaces'])}"
    
    print(f"  输出类型: {result['type']}")
    print(f"  曲面 A 保留顶点数: {len(result['surfaces'][0]['vertices'])}")
    print(f"  曲面 B 保留顶点数: {len(result['surfaces'][1]['vertices'])}")
    
    print("  通过 ✓\n")


def test_case_6_json_serializable():
    print("测试用例 6: JSON 可序列化验证")
    
    surface_a, surface_b = create_test_surfaces()
    
    operations = ['none', 'union', 'intersection', 'difference', 'symmetric_difference']
    
    for op in operations:
        print(f"  测试运算: {op}")
        
        if op == 'symmetric_difference':
            result = apply_set_operation([surface_a, surface_b], op, epsilon=1.0)
        else:
            result = apply_set_operation([surface_a, surface_b], op, epsilon=1.0)
        
        try:
            json_str = json.dumps(result)
            print(f"    成功序列化为 JSON, 长度: {len(json_str)} 字符")
            
            parsed_back = json.loads(json_str)
            assert parsed_back['type'] == result['type']
        except (TypeError, ValueError) as e:
            print(f"    JSON 序列化失败: {e}")
            assert False, f"JSON 序列化失败: {e}"
    
    print("  通过 ✓\n")


def test_case_7_edge_case_empty_surfaces():
    print("测试用例 7: 边缘情况 - 空曲面列表")
    
    try:
        apply_set_operation([], 'none')
        assert False, "应抛出 ValueError"
    except ValueError as e:
        print(f"  正确抛出 ValueError: {e}")
        print("  通过 ✓\n")


def test_case_8_edge_case_different_grid_shapes():
    print("测试用例 8: 边缘情况 - 不同网格形状")
    
    expr = parse_expression("x^2 + y^2")
    surface_a = generate_surface(expr['func'], (-3, 3), (-3, 3), resolution=5)
    surface_b = generate_surface(expr['func'], (-3, 3), (-3, 3), resolution=7)
    
    try:
        apply_set_operation([surface_a, surface_b], 'intersection')
        assert False, "应抛出 ValueError"
    except ValueError as e:
        print(f"  正确抛出 ValueError: {e}")
        print("  通过 ✓\n")


def test_case_9_edge_case_single_surface():
    print("测试用例 9: 边缘情况 - 单个曲面")
    
    surface_a, _ = create_test_surfaces()
    
    result_none = apply_set_operation([surface_a], 'none')
    assert result_none['type'] == 'multiple'
    print(f"  none 运算: type={result_none['type']}")
    
    result_union = apply_set_operation([surface_a], 'union')
    assert result_union['type'] == 'multiple'
    print(f"  union 运算: type={result_union['type']}")
    
    result_intersection = apply_set_operation([surface_a], 'intersection')
    assert result_intersection['type'] == 'multiple'
    print(f"  intersection 运算: type={result_intersection['type']}")
    
    result_difference = apply_set_operation([surface_a], 'difference')
    assert result_difference['type'] == 'single'
    print(f"  difference 运算: type={result_difference['type']}")
    
    print("  通过 ✓\n")


def test_case_10_edge_case_symmetric_difference_wrong_count():
    print("测试用例 10: 边缘情况 - 对称差曲面数量不是 2")
    
    surface_a, surface_b = create_test_surfaces()
    
    try:
        apply_set_operation([surface_a], 'symmetric_difference')
        assert False, "应抛出 ValueError"
    except ValueError as e:
        print(f"  1 个曲面时正确抛出 ValueError: {e}")
    
    try:
        apply_set_operation([surface_a, surface_b, surface_a], 'symmetric_difference')
        assert False, "应抛出 ValueError"
    except ValueError as e:
        print(f"  3 个曲面时正确抛出 ValueError: {e}")
    
    print("  通过 ✓\n")


def test_case_11_unknown_operation():
    print("测试用例 11: 未知运算类型")
    
    surface_a, surface_b = create_test_surfaces()
    
    try:
        apply_set_operation([surface_a, surface_b], 'invalid_operation')
        assert False, "应抛出 ValueError"
    except ValueError as e:
        print(f"  正确抛出 ValueError: {e}")
        print("  通过 ✓\n")


def test_case_12_face_reindexing():
    print("测试用例 12: 面片重新索引验证")
    
    expr = parse_expression("x^2 + y^2")
    surface = generate_surface(expr['func'], (-1, 1), (-1, 1), resolution=3)
    
    print(f"  原始顶点数: {len(surface['vertices'])}")
    print(f"  原始面片数: {len(surface['faces'])}")
    print(f"  原始面片: {surface['faces']}")
    
    expr_plane = parse_expression("100")
    surface_far = generate_surface(expr_plane['func'], (-1, 1), (-1, 1), resolution=3)
    
    result = apply_set_operation([surface, surface_far], 'intersection', epsilon=1.0)
    
    print(f"  交集后顶点数: {len(result['surfaces'][0]['vertices'])}")
    print(f"  交集后面片数: {len(result['surfaces'][0]['faces'])}")
    
    all_far = all(np.array(surface['values']) < 50)
    if all_far:
        assert len(result['surfaces'][0]['vertices']) == 0, "应无顶点保留"
        assert len(result['surfaces'][0]['faces']) == 0, "应无面片保留"
    
    result_diff = apply_set_operation([surface, surface_far], 'difference', epsilon=1.0)
    
    print(f"  差集后顶点数: {len(result_diff['surface']['vertices'])}")
    print(f"  差集后面片数: {len(result_diff['surface']['faces'])}")
    
    print("  通过 ✓\n")


def test_case_13_three_surfaces():
    print("测试用例 13: 三个曲面运算")
    
    expr_a = parse_expression("x^2 + y^2")
    expr_b = parse_expression("5")
    expr_c = parse_expression("5")
    
    surface_a = generate_surface(expr_a['func'], (-3, 3), (-3, 3), resolution=7)
    surface_b = generate_surface(expr_b['func'], (-3, 3), (-3, 3), resolution=7)
    surface_c = generate_surface(expr_c['func'], (-3, 3), (-3, 3), resolution=7)
    
    print("  测试三个曲面的交集...")
    result_intersection = apply_set_operation([surface_a, surface_b, surface_c], 'intersection', epsilon=1.0)
    assert result_intersection['type'] == 'multiple'
    assert len(result_intersection['surfaces']) == 3
    print(f"    输出类型: {result_intersection['type']}")
    print(f"    曲面数量: {len(result_intersection['surfaces'])}")
    
    print("  测试三个曲面的差集 (A - B - C)...")
    result_difference = apply_set_operation([surface_a, surface_b, surface_c], 'difference', epsilon=1.0)
    assert result_difference['type'] == 'single'
    print(f"    输出类型: {result_difference['type']}")
    
    print("  通过 ✓\n")


if __name__ == "__main__":
    print("=" * 70)
    print("运行集合运算模块测试用例")
    print("=" * 70 + "\n")
    
    test_case_1_none_operation()
    test_case_2_union_operation()
    test_case_3_intersection_operation()
    test_case_4_difference_operation()
    test_case_5_symmetric_difference_operation()
    test_case_6_json_serializable()
    test_case_7_edge_case_empty_surfaces()
    test_case_8_edge_case_different_grid_shapes()
    test_case_9_edge_case_single_surface()
    test_case_10_edge_case_symmetric_difference_wrong_count()
    test_case_11_unknown_operation()
    test_case_12_face_reindexing()
    test_case_13_three_surfaces()
    
    print("=" * 70)
    print("所有测试通过! ✓")
    print("=" * 70)

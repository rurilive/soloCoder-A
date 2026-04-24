import json
import numpy as np
from app.parser import parse_expression
from app.calculator import generate_surface


def test_case_1_paraboloid():
    print("测试用例 1: 简单抛物面 x^2 + y^2")
    print("  x_range: (-5, 5), y_range: (-5, 5), resolution: 11")
    
    expr = parse_expression("x^2 + y^2")
    func = expr['func']
    
    result = generate_surface(func, (-5, 5), (-5, 5), resolution=11)
    
    expected_vertices = 11 * 11
    assert len(result['vertices']) == expected_vertices, \
        f"顶点数应为 {expected_vertices}, 实际: {len(result['vertices'])}"
    print(f"  顶点数: {len(result['vertices'])} ✓")
    
    expected_faces = (11 - 1) * (11 - 1) * 2
    assert len(result['faces']) == expected_faces, \
        f"面片数应为 {expected_faces}, 实际: {len(result['faces'])}"
    print(f"  面片数: {len(result['faces'])} ✓")
    
    center_idx = 5 * 11 + 5
    center_vertex = result['vertices'][center_idx]
    assert abs(center_vertex[0] - 0.0) < 1e-10, f"原点 x 应为 0.0, 实际: {center_vertex[0]}"
    assert abs(center_vertex[1] - 0.0) < 1e-10, f"原点 y 应为 0.0, 实际: {center_vertex[1]}"
    assert abs(center_vertex[2] - 0.0) < 1e-10, f"原点 z 应为 0.0, 实际: {center_vertex[2]}"
    print(f"  原点 (x=0,y=0) 处 z={center_vertex[2]} ✓")
    
    corner_idx = 10 * 11 + 10
    corner_vertex = result['vertices'][corner_idx]
    assert abs(corner_vertex[0] - 5.0) < 1e-10, f"角落 x 应为 5.0, 实际: {corner_vertex[0]}"
    assert abs(corner_vertex[1] - 5.0) < 1e-10, f"角落 y 应为 5.0, 实际: {corner_vertex[1]}"
    assert abs(corner_vertex[2] - 50.0) < 1e-10, f"角落 z 应为 50.0, 实际: {corner_vertex[2]}"
    print(f"  角落 (x=5,y=5) 处 z={corner_vertex[2]} ✓")
    
    assert result['grid_shape'] == (11, 11), f"网格形状应为 (11, 11), 实际: {result['grid_shape']}"
    print(f"  网格形状: {result['grid_shape']} ✓")
    
    print("  通过 ✓\n")
    return result


def test_case_2_normal_vector():
    print("测试用例 2: 平面法向量验证 z = x + y")
    
    expr = parse_expression("x + y")
    func = expr['func']
    
    result = generate_surface(func, (-5, 5), (-5, 5), resolution=5)
    
    expected_normal = np.array([-1.0, -1.0, 1.0])
    expected_normal = expected_normal / np.linalg.norm(expected_normal)
    
    center_idx = 2 * 5 + 2
    actual_normal = np.array(result['normals'][center_idx])
    
    dot_product = np.dot(actual_normal, expected_normal)
    assert abs(dot_product - 1.0) < 1e-5, \
        f"法向量方向不对。预期: {expected_normal}, 实际: {actual_normal}, 点积: {dot_product}"
    
    print(f"  预期法向量方向: (-1, -1, 1) 归一化")
    print(f"  实际法向量: {actual_normal}")
    print(f"  点积 (接近 1 表示方向一致): {dot_product}")
    print("  通过 ✓\n")


def test_case_3_json_serializable():
    print("测试用例 3: JSON 可序列化验证")
    
    expr = parse_expression("x^2 + y^2")
    func = expr['func']
    
    result = generate_surface(func, (-2, 2), (-2, 2), resolution=5)
    
    try:
        json_str = json.dumps(result)
        print(f"  成功序列化为 JSON, 长度: {len(json_str)} 字符")
        
        parsed_back = json.loads(json_str)
        assert tuple(parsed_back['grid_shape']) == result['grid_shape'], \
            f"grid_shape 不匹配: {parsed_back['grid_shape']} vs {result['grid_shape']}"
        assert len(parsed_back['vertices']) == len(result['vertices'])
        print("  反序列化验证通过")
    except (TypeError, ValueError) as e:
        print(f"  JSON 序列化失败: {e}")
        assert False, f"JSON 序列化失败: {e}"
    
    print("  通过 ✓\n")


def test_case_4_faces_structure():
    print("测试用例 4: 三角面片结构验证")
    
    expr = parse_expression("x^2 + y^2")
    func = expr['func']
    
    result = generate_surface(func, (0, 1), (0, 1), resolution=3)
    
    print(f"  顶点数: {len(result['vertices'])}")
    print(f"  面片数: {len(result['faces'])}")
    
    expected_faces = [
        [0, 1, 3], [1, 4, 3],
        [1, 2, 4], [2, 5, 4],
        [3, 4, 6], [4, 7, 6],
        [4, 5, 7], [5, 8, 7],
    ]
    
    for i, (actual, expected) in enumerate(zip(result['faces'], expected_faces)):
        assert actual == expected, f"面片 {i} 不正确。预期: {expected}, 实际: {actual}"
    
    print("  所有面片索引验证通过")
    
    for face in result['faces']:
        assert len(face) == 3, f"每个面片必须有 3 个顶点索引"
        for idx in face:
            assert 0 <= idx < len(result['vertices']), f"顶点索引 {idx} 超出范围"
    
    print("  顶点索引范围验证通过")
    print("  通过 ✓\n")


def test_case_5_coordinates():
    print("测试用例 5: x_coords 和 y_coords 验证")
    
    expr = parse_expression("x^2 + y^2")
    func = expr['func']
    
    result = generate_surface(func, (-2, 2), (-1, 3), resolution=5)
    
    expected_x = [-2.0, -1.0, 0.0, 1.0, 2.0]
    expected_y = [-1.0, 0.0, 1.0, 2.0, 3.0]
    
    for actual, expected in zip(result['x_coords'], expected_x):
        assert abs(actual - expected) < 1e-10, f"x 坐标不正确。预期: {expected}, 实际: {actual}"
    
    for actual, expected in zip(result['y_coords'], expected_y):
        assert abs(actual - expected) < 1e-10, f"y 坐标不正确。预期: {expected}, 实际: {actual}"
    
    print(f"  x_coords: {result['x_coords']}")
    print(f"  y_coords: {result['y_coords']}")
    print("  通过 ✓\n")


def test_case_6_values_array():
    print("测试用例 6: values 数组验证")
    
    expr = parse_expression("x^2 + y^2")
    func = expr['func']
    
    result = generate_surface(func, (-1, 1), (-1, 1), resolution=3)
    
    for i, vertex in enumerate(result['vertices']):
        x, y, z = vertex
        expected_z = x**2 + y**2
        assert abs(z - expected_z) < 1e-10, f"顶点 {i} z 值不正确"
        assert abs(result['values'][i] - expected_z) < 1e-10, f"values[{i}] 不正确"
    
    print(f"  vertices[0]: {result['vertices'][0]}")
    print(f"  values[0]: {result['values'][0]}")
    print("  通过 ✓\n")


def test_case_7_boundary_normals():
    print("测试用例 7: 边界点法向量验证 (单侧差分)")
    
    expr = parse_expression("x^2 + y^2")
    func = expr['func']
    
    result = generate_surface(func, (0, 2), (0, 2), resolution=3)
    
    center_idx = 1 * 3 + 1
    corner_idx = 0
    edge_idx = 1
    
    print(f"  中心点法向量: {result['normals'][center_idx]}")
    print(f"  角落点法向量: {result['normals'][corner_idx]}")
    print(f"  边界点法向量: {result['normals'][edge_idx]}")
    
    for normal in result['normals']:
        norm = np.linalg.norm(np.array(normal))
        assert abs(norm - 1.0) < 1e-5, f"法向量未归一化: {normal}, 长度: {norm}"
    
    print("  所有法向量已归一化")
    print("  通过 ✓\n")


if __name__ == "__main__":
    print("=" * 60)
    print("运行曲面网格生成器测试用例")
    print("=" * 60 + "\n")
    
    test_case_1_paraboloid()
    test_case_2_normal_vector()
    test_case_3_json_serializable()
    test_case_4_faces_structure()
    test_case_5_coordinates()
    test_case_6_values_array()
    test_case_7_boundary_normals()
    
    print("=" * 60)
    print("所有测试通过! ✓")
    print("=" * 60)

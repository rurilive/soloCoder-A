import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_presets():
    print("测试用例 1: GET /api/presets")
    
    response = client.get("/api/presets")
    assert response.status_code == 200
    
    data = response.json()
    assert data['success'] == True
    assert 'presets' in data
    assert len(data['presets']) == 5
    
    expected_presets = [
        {"name": "抛物面", "type": "2d"},
        {"name": "正弦波", "type": "2d"},
        {"name": "高斯函数", "type": "2d"},
        {"name": "马鞍面", "type": "2d"},
        {"name": "球体", "type": "3d"},
    ]
    
    for i, expected in enumerate(expected_presets):
        assert data['presets'][i]['name'] == expected['name']
        assert data['presets'][i]['type'] == expected['type']
        print(f"  预设 {i+1}: {data['presets'][i]['name']} ({data['presets'][i]['type']}) ✓")
    
    print("  通过 ✓\n")


def test_post_render_single_function():
    print("测试用例 2: POST /api/render - 单个函数")
    
    request_data = {
        "functions": [
            {
                "expression": "x^2 + y^2",
                "name": "抛物面",
                "color": "#ff6b6b"
            }
        ],
        "operation": "none",
        "params": {
            "x_min": -5.0,
            "x_max": 5.0,
            "y_min": -5.0,
            "y_max": 5.0,
            "z_min": -5.0,
            "z_max": 5.0,
            "resolution": 10,
            "isovalue": 0.0,
            "epsilon": 0.5
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 200, f"响应: {response.json()}"
    
    data = response.json()
    assert data['success'] == True
    assert 'data' in data
    assert data['data']['type'] == 'multiple'
    assert 'surfaces' in data['data']
    assert len(data['data']['surfaces']) == 1
    
    surface = data['data']['surfaces'][0]
    assert 'vertices' in surface
    assert 'faces' in surface
    assert 'normals' in surface
    assert 'color' in surface
    assert surface['color'] == '#ff6b6b'
    
    expected_vertices = 10 * 10
    assert len(surface['vertices']) == expected_vertices, f"顶点数应为 {expected_vertices}, 实际: {len(surface['vertices'])}"
    
    expected_faces = (10 - 1) * (10 - 1) * 2
    assert len(surface['faces']) == expected_faces, f"面片数应为 {expected_faces}, 实际: {len(surface['faces'])}"
    
    print(f"  顶点数: {len(surface['vertices'])} ✓")
    print(f"  面片数: {len(surface['faces'])} ✓")
    print(f"  颜色: {surface['color']} ✓")
    print("  通过 ✓\n")


def test_post_render_union():
    print("测试用例 3: POST /api/render - 两个函数 + operation=union")
    
    request_data = {
        "functions": [
            {
                "expression": "x^2 + y^2",
                "name": "抛物面",
                "color": "#ff6b6b"
            },
            {
                "expression": "0 * x + 5",
                "name": "平面",
                "color": "#4ecdc4"
            }
        ],
        "operation": "union",
        "params": {
            "x_min": -5.0,
            "x_max": 5.0,
            "y_min": -5.0,
            "y_max": 5.0,
            "z_min": -5.0,
            "z_max": 5.0,
            "resolution": 10,
            "isovalue": 0.0,
            "epsilon": 0.5
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 200, f"响应: {response.json()}"
    
    data = response.json()
    assert data['success'] == True
    assert data['data']['type'] == 'multiple'
    assert len(data['data']['surfaces']) == 2
    
    colors = [s['color'] for s in data['data']['surfaces']]
    assert '#ff6b6b' in colors
    assert '#4ecdc4' in colors
    
    print(f"  曲面数量: {len(data['data']['surfaces'])} ✓")
    print(f"  颜色: {colors} ✓")
    print("  通过 ✓\n")


def test_post_render_invalid_expression():
    print("测试用例 4: POST /api/render - 无效表达式")
    
    request_data = {
        "functions": [
            {
                "expression": "x + * y",
                "name": "错误表达式",
                "color": "#ff6b6b"
            }
        ],
        "operation": "none",
        "params": {
            "x_min": -5.0,
            "x_max": 5.0,
            "y_min": -5.0,
            "y_max": 5.0,
            "z_min": -5.0,
            "z_max": 5.0,
            "resolution": 10,
            "isovalue": 0.0,
            "epsilon": 0.5
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert data['detail']['success'] == False
    assert 'error' in data['detail']
    assert '语法错误' in data['detail']['error'] or '表达式解析错误' in data['detail']['error']
    
    print(f"  错误状态码: {response.status_code} ✓")
    print(f"  错误信息: {data['detail']['error']} ✓")
    print("  通过 ✓\n")


def test_post_render_empty_functions():
    print("测试用例 5: POST /api/render - 空函数列表")
    
    request_data = {
        "functions": [],
        "operation": "none",
        "params": {
            "x_min": -5.0,
            "x_max": 5.0,
            "y_min": -5.0,
            "y_max": 5.0,
            "z_min": -5.0,
            "z_max": 5.0,
            "resolution": 10,
            "isovalue": 0.0,
            "epsilon": 0.5
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert data['detail']['success'] == False
    assert '不能为空' in data['detail']['error']
    
    print(f"  错误状态码: {response.status_code} ✓")
    print(f"  错误信息: {data['detail']['error']} ✓")
    print("  通过 ✓\n")


def test_post_render_3d_function():
    print("测试用例 6: POST /api/render - 3D 函数暂不支持")
    
    request_data = {
        "functions": [
            {
                "expression": "x^2 + y^2 + z^2",
                "name": "球体",
                "color": "#6c5ce7"
            }
        ],
        "operation": "none",
        "params": {
            "x_min": -5.0,
            "x_max": 5.0,
            "y_min": -5.0,
            "y_max": 5.0,
            "z_min": -5.0,
            "z_max": 5.0,
            "resolution": 10,
            "isovalue": 0.0,
            "epsilon": 0.5
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert data['detail']['success'] == False
    assert '3D 函数暂不支持' in data['detail']['error']
    
    print(f"  错误状态码: {response.status_code} ✓")
    print(f"  错误信息: {data['detail']['error']} ✓")
    print("  通过 ✓\n")


def test_post_render_difference():
    print("测试用例 7: POST /api/render - difference 运算返回 single")
    
    request_data = {
        "functions": [
            {
                "expression": "x^2 + y^2",
                "name": "抛物面",
                "color": "#ff6b6b"
            },
            {
                "expression": "0 * x + 5",
                "name": "平面",
                "color": "#4ecdc4"
            }
        ],
        "operation": "difference",
        "params": {
            "x_min": -5.0,
            "x_max": 5.0,
            "y_min": -5.0,
            "y_max": 5.0,
            "z_min": -5.0,
            "z_max": 5.0,
            "resolution": 10,
            "isovalue": 0.0,
            "epsilon": 100.0
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 200, f"响应: {response.json()}"
    
    data = response.json()
    assert data['success'] == True
    assert data['data']['type'] == 'single'
    assert 'surface' in data['data']
    
    surface = data['data']['surface']
    assert 'vertices' in surface
    assert 'faces' in surface
    assert 'normals' in surface
    
    print(f"  类型: {data['data']['type']} ✓")
    print(f"  顶点数: {len(surface['vertices'])} ✓")
    print("  通过 ✓\n")


def test_json_serialization():
    print("测试用例 8: JSON 序列化验证")
    
    request_data = {
        "functions": [
            {
                "expression": "sin(x) * cos(y)",
                "name": "正弦波",
                "color": "#4ecdc4"
            }
        ],
        "operation": "none",
        "params": {
            "x_min": -3.0,
            "x_max": 3.0,
            "y_min": -3.0,
            "y_max": 3.0,
            "z_min": -2.0,
            "z_max": 2.0,
            "resolution": 20,
            "isovalue": 0.0,
            "epsilon": 0.5
        }
    }
    
    response = client.post("/api/render", json=request_data)
    assert response.status_code == 200
    
    response_json = response.json()
    json_str = json.dumps(response_json)
    
    parsed_back = json.loads(json_str)
    assert parsed_back['success'] == True
    assert parsed_back['data']['type'] == response_json['data']['type']
    assert len(parsed_back['data']['surfaces']) == len(response_json['data']['surfaces'])
    
    print(f"  响应 JSON 大小: {len(json_str)} 字符 ✓")
    print(f"  反序列化验证通过 ✓")
    print("  通过 ✓\n")


if __name__ == "__main__":
    print("=" * 60)
    print("运行 API 路由测试用例")
    print("=" * 60 + "\n")
    
    test_get_presets()
    test_post_render_single_function()
    test_post_render_union()
    test_post_render_invalid_expression()
    test_post_render_empty_functions()
    test_post_render_3d_function()
    test_post_render_difference()
    test_json_serialization()
    
    print("=" * 60)
    print("所有 API 路由测试通过! ✓")
    print("=" * 60)

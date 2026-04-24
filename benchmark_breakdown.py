import time
import numpy as np
import sys
sys.path.insert(0, '.')

from app.parser import parse_expression


def timeit(name, func, repeats=3):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return np.mean(times), np.min(times)


def benchmark_generate_surface_breakdown():
    print("=" * 60)
    print("generate_surface 详细时间分解")
    print("=" * 60)
    
    expr = "sin(x) * cos(y) + x^2 - y^2"
    func_info = parse_expression(expr)
    func = func_info['func']
    
    resolutions = [50, 100, 200]
    
    for res in resolutions:
        print(f"\n--- Resolution: {res}x{res} = {res*res} vertices ---")
        
        x_min, x_max = -5, 5
        y_min, y_max = -5, 5
        
        times = {}
        
        # 1. linspace + meshgrid
        def step1():
            x_coords = np.linspace(x_min, x_max, res, dtype=np.float64)
            y_coords = np.linspace(y_min, y_max, res, dtype=np.float64)
            X, Y = np.meshgrid(x_coords, y_coords)
            return X, Y, x_coords, y_coords
        
        t, _ = timeit("1. meshgrid", step1)
        times['meshgrid'] = t
        X, Y, x_coords, y_coords = step1()
        
        # 2. 函数计算
        def step2():
            Z = func(X, Y)
            if isinstance(Z, (int, float)):
                Z = np.full_like(X, Z, dtype=np.float64)
            return Z
        
        t, _ = timeit("2. func(X,Y)", step2)
        times['func_eval'] = t
        Z = step2()
        
        dx = (x_max - x_min) / (res - 1) if res > 1 else 1.0
        dy = (y_max - y_min) / (res - 1) if res > 1 else 1.0
        
        # 3. column_stack
        def step3():
            return np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
        
        t, _ = timeit("3. column_stack", step3)
        times['column_stack'] = t
        vertices = step3()
        
        # 4. generate_faces (numpy 向量化版本)
        def generate_faces_fast(nx, ny):
            if nx < 2 or ny < 2:
                return np.empty((0, 3), dtype=np.int32)
            n_faces = (nx - 1) * (ny - 1) * 2
            faces = np.empty((n_faces, 3), dtype=np.int32)
            i_idx, j_idx = np.ogrid[:ny-1, :nx-1]
            base = i_idx * nx + j_idx
            face_idx_0 = np.arange(0, n_faces, 2)
            face_idx_1 = face_idx_0 + 1
            faces[face_idx_0, 0] = base.ravel()
            faces[face_idx_0, 1] = base.ravel() + 1
            faces[face_idx_0, 2] = base.ravel() + nx
            faces[face_idx_1, 0] = base.ravel() + 1
            faces[face_idx_1, 1] = base.ravel() + 1 + nx
            faces[face_idx_1, 2] = base.ravel() + nx
            return faces
        
        t, _ = timeit("4. generate_faces", lambda: generate_faces_fast(res, res))
        times['generate_faces'] = t
        faces = generate_faces_fast(res, res)
        
        # 5. compute_normals
        def compute_normals(Z, dx, dy):
            ny, nx = Z.shape
            normals = np.zeros((ny, nx, 3), dtype=np.float64)
            if nx > 1:
                dz_dx = np.zeros((ny, nx), dtype=np.float64)
                dz_dx[:, 1:-1] = (Z[:, 2:] - Z[:, :-2]) / (2 * dx)
                dz_dx[:, 0] = (Z[:, 1] - Z[:, 0]) / dx
                dz_dx[:, -1] = (Z[:, -1] - Z[:, -2]) / dx
                normals[:, :, 0] = -dz_dx
            if ny > 1:
                dz_dy = np.zeros((ny, nx), dtype=np.float64)
                dz_dy[1:-1, :] = (Z[2:, :] - Z[:-2, :]) / (2 * dy)
                dz_dy[0, :] = (Z[1, :] - Z[0, :]) / dy
                dz_dy[-1, :] = (Z[-1, :] - Z[-2, :]) / dy
                normals[:, :, 1] = -dz_dy
            normals[:, :, 2] = 1.0
            norms = np.sqrt(np.sum(normals ** 2, axis=2, keepdims=True))
            norms = np.maximum(norms, 1e-10)
            normals = normals / norms
            return normals
        
        t, _ = timeit("5. compute_normals", lambda: compute_normals(Z, dx, dy))
        times['compute_normals'] = t
        normals = compute_normals(Z, dx, dy)
        normals_flat = normals.reshape(-1, 3)
        values = Z.ravel()
        
        # 6. tolist() 转换
        def step6():
            return (
                vertices.tolist(),
                faces.tolist(),
                normals_flat.tolist(),
                values.tolist()
            )
        
        t, _ = timeit("6. .tolist() 转换", step6)
        times['tolist'] = t
        
        # 汇总
        total = sum(times.values())
        print(f"\n时间分解 ({res}x{res}):")
        for name, t in times.items():
            pct = t / total * 100 if total > 0 else 0
            print(f"  {name:20s}: {t*1000:8.2f}ms ({pct:5.1f}%)")
        print(f"  {'-'*20}: {'-'*15}")
        print(f"  {'TOTAL':20s}: {total*1000:8.2f}ms (100.0%)")


def benchmark_json_serialization():
    print("\n" + "=" * 60)
    print("JSON 序列化开销测试")
    print("=" * 60)
    
    import json
    
    res = 100
    n_verts = res * res
    n_faces = (res - 1) * (res - 1) * 2
    
    # 创建测试数据
    vertices_np = np.random.rand(n_verts, 3).astype(np.float64)
    faces_np = np.random.randint(0, n_verts, (n_faces, 3), dtype=np.int32)
    normals_np = np.random.rand(n_verts, 3).astype(np.float64)
    
    # 转换为 list
    vertices_list = vertices_np.tolist()
    faces_list = faces_np.tolist()
    normals_list = normals_np.tolist()
    
    data = {
        'type': 'multiple',
        'surfaces': [{
            'vertices': vertices_list,
            'faces': faces_list,
            'normals': normals_list,
            'color': '#ff6b6b'
        }]
    }
    
    print(f"\n数据规模:")
    print(f"  顶点: {n_verts} x 3 = {n_verts * 3} floats")
    print(f"  面片: {n_faces} x 3 = {n_faces * 3} ints")
    
    # 测试 json.dumps
    t, _ = timeit("json.dumps", lambda: json.dumps(data))
    print(f"\n  json.dumps: {t*1000:.2f}ms")
    
    # 测试 orjson (如果可用)
    try:
        import orjson
        t, _ = timeit("orjson.dumps", lambda: orjson.dumps(data))
        print(f"  orjson.dumps: {t*1000:.2f}ms")
    except ImportError:
        print("  orjson 未安装")


if __name__ == "__main__":
    benchmark_generate_surface_breakdown()
    benchmark_json_serialization()

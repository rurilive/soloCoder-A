import numpy as np
from typing import Callable, List, Dict, Tuple


def _convert_to_python(obj):
    if isinstance(obj, np.ndarray):
        return [_convert_to_python(x) for x in obj]
    elif isinstance(obj, (np.float32, np.float64, np.floating)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64, np.integer)):
        return int(obj)
    return obj


def _compute_normals(Z: np.ndarray, dx: float, dy: float) -> np.ndarray:
    ny, nx = Z.shape
    normals = np.zeros((ny, nx, 3), dtype=np.float64)
    
    dz_dx = np.zeros((ny, nx), dtype=np.float64)
    dz_dy = np.zeros((ny, nx), dtype=np.float64)
    
    if nx > 1:
        dz_dx[:, 1:-1] = (Z[:, 2:] - Z[:, :-2]) / (2 * dx)
        dz_dx[:, 0] = (Z[:, 1] - Z[:, 0]) / dx
        dz_dx[:, -1] = (Z[:, -1] - Z[:, -2]) / dx
    
    if ny > 1:
        dz_dy[1:-1, :] = (Z[2:, :] - Z[:-2, :]) / (2 * dy)
        dz_dy[0, :] = (Z[1, :] - Z[0, :]) / dy
        dz_dy[-1, :] = (Z[-1, :] - Z[-2, :]) / dy
    
    normals[:, :, 0] = -dz_dx
    normals[:, :, 1] = -dz_dy
    normals[:, :, 2] = 1.0
    
    norms = np.sqrt(np.sum(normals ** 2, axis=2, keepdims=True))
    norms = np.maximum(norms, 1e-10)
    normals = normals / norms
    
    return normals


def _generate_faces(nx: int, ny: int) -> np.ndarray:
    faces = []
    for i in range(ny - 1):
        for j in range(nx - 1):
            idx00 = i * nx + j
            idx10 = i * nx + j + 1
            idx01 = (i + 1) * nx + j
            idx11 = (i + 1) * nx + j + 1
            
            faces.append([idx00, idx10, idx01])
            faces.append([idx10, idx11, idx01])
    
    return np.array(faces, dtype=np.int32)


def generate_surface(
    func: Callable,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    resolution: int = 50
) -> Dict:
    x_min, x_max = x_range
    y_min, y_max = y_range
    
    x_coords = np.linspace(x_min, x_max, resolution, dtype=np.float64)
    y_coords = np.linspace(y_min, y_max, resolution, dtype=np.float64)
    
    X, Y = np.meshgrid(x_coords, y_coords)
    
    Z = func(X, Y)
    
    if isinstance(Z, (int, float)):
        Z = np.full_like(X, Z, dtype=np.float64)
    
    dx = (x_max - x_min) / (resolution - 1) if resolution > 1 else 1.0
    dy = (y_max - y_min) / (resolution - 1) if resolution > 1 else 1.0
    
    vertices = np.column_stack([X.flatten(), Y.flatten(), Z.flatten()])
    
    faces = _generate_faces(resolution, resolution)
    
    normals = _compute_normals(Z, dx, dy)
    normals = normals.reshape(-1, 3)
    
    values = Z.flatten()
    
    return {
        'vertices': _convert_to_python(vertices),
        'faces': _convert_to_python(faces),
        'normals': _convert_to_python(normals),
        'values': _convert_to_python(values),
        'x_coords': _convert_to_python(x_coords),
        'y_coords': _convert_to_python(y_coords),
        'grid_shape': (resolution, resolution)
    }

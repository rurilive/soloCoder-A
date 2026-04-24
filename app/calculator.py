import numpy as np
from typing import Callable, Dict, Tuple


def _compute_normals_fast(Z: np.ndarray, dx: float, dy: float) -> np.ndarray:
    ny, nx = Z.shape
    normals = np.zeros((ny, nx, 3), dtype=np.float32)
    
    if nx > 1:
        dz_dx = np.zeros((ny, nx), dtype=np.float32)
        dz_dx[:, 1:-1] = (Z[:, 2:] - Z[:, :-2]) / (2 * dx)
        dz_dx[:, 0] = (Z[:, 1] - Z[:, 0]) / dx
        dz_dx[:, -1] = (Z[:, -1] - Z[:, -2]) / dx
        normals[:, :, 0] = -dz_dx
    
    if ny > 1:
        dz_dy = np.zeros((ny, nx), dtype=np.float32)
        dz_dy[1:-1, :] = (Z[2:, :] - Z[:-2, :]) / (2 * dy)
        dz_dy[0, :] = (Z[1, :] - Z[0, :]) / dy
        dz_dy[-1, :] = (Z[-1, :] - Z[-2, :]) / dy
        normals[:, :, 1] = -dz_dy
    
    normals[:, :, 2] = 1.0
    
    norms = np.sqrt(np.sum(normals ** 2, axis=2, keepdims=True))
    norms = np.maximum(norms, 1e-10)
    normals = normals / norms
    
    return normals


def _generate_faces_fast(nx: int, ny: int) -> np.ndarray:
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


def generate_surface(
    func: Callable,
    x_range: Tuple[float, float],
    y_range: Tuple[float, float],
    resolution: int = 50
) -> Dict:
    x_min, x_max = x_range
    y_min, y_max = y_range
    
    x_coords = np.linspace(x_min, x_max, resolution, dtype=np.float32)
    y_coords = np.linspace(y_min, y_max, resolution, dtype=np.float32)
    
    X, Y = np.meshgrid(x_coords, y_coords)
    
    Z = func(X, Y)
    
    if isinstance(Z, (int, float)):
        Z = np.full_like(X, Z, dtype=np.float32)
    elif Z.dtype != np.float32:
        Z = Z.astype(np.float32)
    
    dx = (x_max - x_min) / (resolution - 1) if resolution > 1 else 1.0
    dy = (y_max - y_min) / (resolution - 1) if resolution > 1 else 1.0
    
    vertices = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
    
    faces = _generate_faces_fast(resolution, resolution)
    
    normals = _compute_normals_fast(Z, dx, dy)
    normals = normals.reshape(-1, 3)
    
    values = Z.ravel()
    
    return {
        'vertices': vertices,
        'faces': faces,
        'normals': normals,
        'values': values,
        'x_coords': x_coords,
        'y_coords': y_coords,
        'grid_shape': (resolution, resolution)
    }

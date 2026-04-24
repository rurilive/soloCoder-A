import numpy as np
from typing import List, Dict, Tuple


def _extract_z_values(surface: Dict) -> np.ndarray:
    values = surface['values']
    grid_shape = surface['grid_shape']
    if isinstance(values, np.ndarray):
        return values.reshape(grid_shape)
    return np.asarray(values, dtype=np.float32).reshape(grid_shape)


def _validate_surfaces(surfaces: List[Dict]) -> None:
    if not surfaces:
        raise ValueError("Surface list cannot be empty")
    
    if len(surfaces) == 1:
        return
    
    grid_shape = surfaces[0]['grid_shape']
    for i, surface in enumerate(surfaces[1:], 1):
        if surface['grid_shape'] != grid_shape:
            raise ValueError(
                f"Surface {i} has different grid shape {surface['grid_shape']} "
                f"from surface 0 {grid_shape}. All surfaces must have same grid shape."
            )


def _create_fast_index_mapping(mask: np.ndarray, n_total: int) -> Tuple[np.ndarray, np.ndarray]:
    old_indices = np.where(mask)[0]
    index_array = np.full(n_total, -1, dtype=np.int32)
    index_array[old_indices] = np.arange(len(old_indices), dtype=np.int32)
    return index_array, old_indices


def _fast_reindex_faces(faces: np.ndarray, index_array: np.ndarray) -> np.ndarray:
    if len(faces) == 0:
        return np.empty((0, 3), dtype=np.int32)
    
    mapped = index_array[faces]
    valid_mask = np.all(mapped != -1, axis=1)
    return mapped[valid_mask]


def _apply_mask_to_surface_fast(surface: Dict, mask: np.ndarray) -> Dict:
    vertices = surface['vertices']
    faces = surface['faces']
    normals = surface['normals']
    values = surface['values']
    
    if not isinstance(vertices, np.ndarray):
        vertices = np.asarray(vertices, dtype=np.float32)
    if not isinstance(faces, np.ndarray):
        faces = np.asarray(faces, dtype=np.int32)
    if not isinstance(normals, np.ndarray):
        normals = np.asarray(normals, dtype=np.float32)
    if not isinstance(values, np.ndarray):
        values = np.asarray(values, dtype=np.float32)
    
    n_vertices = len(values)
    index_array, old_indices = _create_fast_index_mapping(mask, n_vertices)
    
    if len(old_indices) == 0:
        return {
            'vertices': np.empty((0, 3), dtype=np.float32),
            'faces': np.empty((0, 3), dtype=np.int32),
            'normals': np.empty((0, 3), dtype=np.float32),
            'values': np.empty(0, dtype=np.float32)
        }
    
    new_vertices = vertices[old_indices]
    new_normals = normals[old_indices]
    new_values = values[old_indices]
    
    if len(faces) > 0 and faces.ndim == 2:
        new_faces = _fast_reindex_faces(faces, index_array)
    else:
        new_faces = np.empty((0, 3), dtype=np.int32)
    
    return {
        'vertices': new_vertices,
        'faces': new_faces,
        'normals': new_normals,
        'values': new_values
    }


def _compute_union_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    n_vertices = len(surfaces[0]['values'])
    return np.ones(n_vertices, dtype=bool)


def _compute_intersection_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    z_arrays = [_extract_z_values(s).flatten() for s in surfaces]
    base_z = z_arrays[0]
    
    all_close = np.ones_like(base_z, dtype=bool)
    for z_flat in z_arrays[1:]:
        all_close = all_close & (np.abs(base_z - z_flat) < epsilon)
    
    return all_close


def _compute_difference_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    z_arrays = [_extract_z_values(s).flatten() for s in surfaces]
    base_z = z_arrays[0]
    
    not_overlapping = np.ones_like(base_z, dtype=bool)
    for z_flat in z_arrays[1:]:
        not_overlapping = not_overlapping & (np.abs(base_z - z_flat) >= epsilon)
    
    return not_overlapping


def _compute_symmetric_difference_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    if len(surfaces) != 2:
        raise ValueError("Symmetric difference requires exactly 2 surfaces")
    
    z0 = _extract_z_values(surfaces[0]).flatten()
    z1 = _extract_z_values(surfaces[1]).flatten()
    
    return np.abs(z0 - z1) >= epsilon


def _format_multiple_output_fast(surfaces: List[Dict], colors: List[str] = None) -> Dict:
    if colors is None:
        default_colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7']
        colors = default_colors[:len(surfaces)]
    
    formatted_surfaces = []
    for i, surface in enumerate(surfaces):
        formatted_surface = {
            'vertices': surface['vertices'],
            'faces': surface['faces'],
            'normals': surface['normals'],
            'color': colors[i % len(colors)]
        }
        formatted_surfaces.append(formatted_surface)
    
    return {
        'type': 'multiple',
        'surfaces': formatted_surfaces
    }


def _format_single_output_fast(surface: Dict) -> Dict:
    return {
        'type': 'single',
        'surface': {
            'vertices': surface['vertices'],
            'faces': surface['faces'],
            'normals': surface['normals']
        }
    }


def apply_set_operation(
    surfaces: List[Dict],
    operation: str,
    epsilon: float = 1e-3
) -> Dict:
    if not surfaces:
        raise ValueError("No surfaces provided")
    
    _validate_surfaces(surfaces)
    
    operation = operation.lower()
    
    if operation == 'none':
        return _format_multiple_output_fast(surfaces)
    
    elif operation == 'union':
        return _format_multiple_output_fast(surfaces)
    
    elif operation == 'intersection':
        if len(surfaces) < 2:
            return _format_multiple_output_fast(surfaces)
        
        mask = _compute_intersection_mask(surfaces, epsilon)
        masked_surfaces = [_apply_mask_to_surface_fast(s, mask) for s in surfaces]
        
        return _format_multiple_output_fast(masked_surfaces)
    
    elif operation == 'difference':
        if len(surfaces) < 2:
            return _format_single_output_fast(surfaces[0])
        
        mask = _compute_difference_mask(surfaces, epsilon)
        masked_surface = _apply_mask_to_surface_fast(surfaces[0], mask)
        
        return _format_single_output_fast(masked_surface)
    
    elif operation == 'symmetric_difference':
        if len(surfaces) != 2:
            raise ValueError("Symmetric difference requires exactly 2 surfaces")
        
        mask = _compute_symmetric_difference_mask(surfaces, epsilon)
        masked_surfaces = [_apply_mask_to_surface_fast(s, mask) for s in surfaces]
        
        return _format_multiple_output_fast(masked_surfaces)
    
    else:
        raise ValueError(
            f"Unknown operation: {operation}. "
            f"Supported operations: none, union, intersection, difference, symmetric_difference"
        )

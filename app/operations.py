import numpy as np
from typing import List, Dict, Tuple


def _convert_to_numpy(obj):
    if isinstance(obj, list):
        return np.array(obj, dtype=np.float64)
    elif isinstance(obj, np.ndarray):
        return obj.astype(np.float64)
    return obj


def _convert_to_python(obj):
    if isinstance(obj, np.ndarray):
        return [_convert_to_python(x) for x in obj]
    elif isinstance(obj, (np.float32, np.float64, np.floating)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64, np.integer)):
        return int(obj)
    return obj


def _extract_z_values(surface: Dict) -> np.ndarray:
    values = surface['values']
    grid_shape = surface['grid_shape']
    z_array = _convert_to_numpy(values)
    return z_array.reshape(grid_shape)


def _validate_surfaces(surfaces: List[Dict]) -> Tuple:
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


def _create_index_mapping(mask: np.ndarray) -> Dict[int, int]:
    old_indices = np.where(mask)[0]
    index_map = {old: new for new, old in enumerate(old_indices)}
    return index_map


def _reindex_faces(faces: np.ndarray, index_map: Dict[int, int]) -> np.ndarray:
    new_faces = []
    for face in faces:
        if all(idx in index_map for idx in face):
            new_face = [index_map[idx] for idx in face]
            new_faces.append(new_face)
    if not new_faces:
        return np.array([], dtype=np.int32).reshape(0, 3)
    return np.array(new_faces, dtype=np.int32)


def _apply_mask_to_surface(surface: Dict, mask: np.ndarray) -> Dict:
    vertices = _convert_to_numpy(surface['vertices'])
    faces = _convert_to_numpy(surface['faces']).astype(np.int32)
    normals = _convert_to_numpy(surface['normals'])
    values = _convert_to_numpy(surface['values'])
    
    index_map = _create_index_mapping(mask)
    
    if not index_map:
        return {
            'vertices': [],
            'faces': [],
            'normals': [],
            'values': []
        }
    
    new_vertices = vertices[mask]
    new_normals = normals[mask]
    new_values = values[mask]
    new_faces = _reindex_faces(faces, index_map)
    
    return {
        'vertices': _convert_to_python(new_vertices),
        'faces': _convert_to_python(new_faces),
        'normals': _convert_to_python(new_normals),
        'values': _convert_to_python(new_values)
    }


def _compute_union_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    n_vertices = len(surfaces[0]['values'])
    return np.ones(n_vertices, dtype=bool)


def _compute_intersection_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    z_arrays = [_extract_z_values(s) for s in surfaces]
    base_z = z_arrays[0].flatten()
    
    all_close = np.ones_like(base_z, dtype=bool)
    for z_array in z_arrays[1:]:
        z_flat = z_array.flatten()
        all_close = all_close & (np.abs(base_z - z_flat) < epsilon)
    
    return all_close


def _compute_difference_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    z_arrays = [_extract_z_values(s) for s in surfaces]
    base_z = z_arrays[0].flatten()
    
    not_overlapping = np.ones_like(base_z, dtype=bool)
    for z_array in z_arrays[1:]:
        z_flat = z_array.flatten()
        not_overlapping = not_overlapping & (np.abs(base_z - z_flat) >= epsilon)
    
    return not_overlapping


def _compute_symmetric_difference_mask(surfaces: List[Dict], epsilon: float) -> np.ndarray:
    if len(surfaces) != 2:
        raise ValueError("Symmetric difference requires exactly 2 surfaces")
    
    z0 = _extract_z_values(surfaces[0]).flatten()
    z1 = _extract_z_values(surfaces[1]).flatten()
    
    return np.abs(z0 - z1) >= epsilon


def _format_multiple_output(surfaces: List[Dict], colors: List[str] = None) -> Dict:
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


def _format_single_output(surface: Dict) -> Dict:
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
        return _format_multiple_output(surfaces)
    
    elif operation == 'union':
        return _format_multiple_output(surfaces)
    
    elif operation == 'intersection':
        if len(surfaces) < 2:
            return _format_multiple_output(surfaces)
        
        mask = _compute_intersection_mask(surfaces, epsilon)
        masked_surfaces = [_apply_mask_to_surface(s, mask) for s in surfaces]
        
        return _format_multiple_output(masked_surfaces)
    
    elif operation == 'difference':
        if len(surfaces) < 2:
            return _format_single_output(surfaces[0])
        
        mask = _compute_difference_mask(surfaces, epsilon)
        masked_surface = _apply_mask_to_surface(surfaces[0], mask)
        
        return _format_single_output(masked_surface)
    
    elif operation == 'symmetric_difference':
        if len(surfaces) != 2:
            raise ValueError("Symmetric difference requires exactly 2 surfaces")
        
        mask = _compute_symmetric_difference_mask(surfaces, epsilon)
        masked_surfaces = [_apply_mask_to_surface(s, mask) for s in surfaces]
        
        return _format_multiple_output(masked_surfaces)
    
    else:
        raise ValueError(
            f"Unknown operation: {operation}. "
            f"Supported operations: none, union, intersection, difference, symmetric_difference"
        )

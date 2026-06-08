import trimesh
import numpy as np

_AXES = {'x': [1, 0, 0], 'y': [0, 1, 0], 'z': [0, 0, 1]}


def translate(mesh, x=0, y=0, z=0):
    m = mesh.copy()
    m.apply_translation([x, y, z])
    return m


def rotate(mesh, angle, axis='z'):
    m = mesh.copy()
    ax = _AXES[axis] if isinstance(axis, str) else axis
    mat = trimesh.transformations.rotation_matrix(np.radians(angle), ax)
    m.apply_transform(mat)
    return m


def scale(mesh, x=1, y=1, z=1):
    m = mesh.copy()
    m.apply_transform(np.diag([x, y, z, 1.0]))
    return m


def mirror(mesh, axis='x'):
    m = mesh.copy()
    mat = trimesh.transformations.reflection_matrix([0, 0, 0], _AXES[axis])
    m.apply_transform(mat)
    return m


def linear_array(mesh, count, axis='x', spacing=1.0):
    d = np.array(_AXES[axis], dtype=float)
    return trimesh.util.concatenate([
        translate(mesh, *(d * spacing * i)) for i in range(count)
    ])


def polar_array(mesh, count, axis='z'):
    return trimesh.util.concatenate([
        rotate(mesh, 360 * i / count, axis) for i in range(count)
    ])

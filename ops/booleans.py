import numpy as np
import trimesh


def _boolean(a, b, op):
    # Try manifold3d first — robust, no external tool needed
    try:
        import manifold3d as m3d

        def to_m(mesh):
            return m3d.Manifold(mesh=m3d.Mesh(
                vert_properties=mesh.vertices.astype(np.float32),
                tri_verts=mesh.faces.astype(np.uint32),
            ))

        def from_m(man):
            r = man.to_mesh()
            return trimesh.Trimesh(vertices=r.vert_properties, faces=r.tri_verts, process=False)

        ma, mb = to_m(a), to_m(b)
        ops = {'union': lambda: ma + mb, 'subtract': lambda: ma - mb, 'intersect': lambda: ma ^ mb}
        return from_m(ops[op]())

    except ImportError:
        pass

    # Fallback: trimesh.boolean (needs OpenSCAD or Blender on PATH)
    try:
        if op == 'union':
            return trimesh.boolean.union([a, b])
        if op == 'subtract':
            return trimesh.boolean.difference(a, b)
        if op == 'intersect':
            return trimesh.boolean.intersection([a, b])
    except Exception as e:
        raise RuntimeError(
            f"Boolean '{op}' failed. Install manifold3d (`pip install manifold3d`) "
            f"or ensure OpenSCAD/Blender is on PATH.\nUnderlying error: {e}"
        )


def union(a, b):
    return _boolean(a, b, 'union')


def subtract(a, b):
    return _boolean(a, b, 'subtract')


def intersect(a, b):
    return _boolean(a, b, 'intersect')

"""Browser viewer for the simulated scene, built on viser.

viser renders in the browser with WebGL, so the host needs no display or GPU:
the simulator only streams geom poses over a websocket. Open
http://<host>:<port> (for a remote or headless host, see the README for the
SSH tunnel).

Which geoms are drawn: the model's visual geoms (group 1) if it has any,
otherwise group 0. Planes are replaced by a grid.
"""

import threading
import time

import mujoco
import numpy as np
import trimesh
import viser

G = mujoco.mjtGeom


def _geom_mesh(model: mujoco.MjModel, g: int):
    """Return (vertices, faces) of geom g in its own frame, or None."""
    t = int(model.geom_type[g])
    size = model.geom_size[g]
    if t == G.mjGEOM_MESH:
        mid = int(model.geom_dataid[g])
        v0, nv = model.mesh_vertadr[mid], model.mesh_vertnum[mid]
        f0, nf = model.mesh_faceadr[mid], model.mesh_facenum[mid]
        return (np.array(model.mesh_vert[v0:v0 + nv]),
                np.array(model.mesh_face[f0:f0 + nf]))
    if t == G.mjGEOM_SPHERE:
        mesh = trimesh.creation.icosphere(subdivisions=2, radius=size[0])
    elif t == G.mjGEOM_CAPSULE:
        mesh = trimesh.creation.capsule(height=2 * size[1], radius=size[0])
    elif t == G.mjGEOM_CYLINDER:
        mesh = trimesh.creation.cylinder(radius=size[0], height=2 * size[1])
    elif t == G.mjGEOM_BOX:
        mesh = trimesh.creation.box(extents=2 * size)
    elif t == G.mjGEOM_ELLIPSOID:
        mesh = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        mesh.apply_scale(size)
    else:
        return None
    return np.array(mesh.vertices), np.array(mesh.faces)


class SceneViewer:
    """Streams geom poses of an MjModel to a viser server."""

    def __init__(self, model: mujoco.MjModel, host: str, port: int,
                 rate_hz: float = 30.0):
        self.server = viser.ViserServer(host=host, port=port, verbose=False)
        scene = self.server.scene
        scene.set_up_direction('+z')
        scene.add_grid('/ground', width=6.0, height=6.0, plane='xy',
                       cell_size=0.5, section_size=1.0)

        group = 1 if np.any(model.geom_group == 1) else 0
        self.geom_ids, self.handles = [], []
        for g in range(model.ngeom):
            if int(model.geom_group[g]) != group:
                continue
            mesh = _geom_mesh(model, g)
            if mesh is None:
                continue
            rgba = model.geom_rgba[g]
            handle = scene.add_mesh_simple(
                f'/scene/geom_{g}', mesh[0], mesh[1],
                color=tuple(int(round(255 * c)) for c in rgba[:3]),
                opacity=float(rgba[3]) if rgba[3] < 1.0 else None)
            self.geom_ids.append(g)
            self.handles.append(handle)

        self._ids = np.array(self.geom_ids, dtype=int)
        self._lock = threading.Lock()
        self._pose = None
        self._period = 1.0 / rate_hz
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def push(self, data: mujoco.MjData):
        """Hand over the latest poses; called from the simulation thread."""
        pose = (data.geom_xpos[self._ids].copy(),
                data.geom_xmat[self._ids].copy())
        with self._lock:
            self._pose = pose

    def _run(self):
        quat = np.zeros(4)
        while not self._stop.wait(self._period):
            with self._lock:
                pose, self._pose = self._pose, None
            if pose is None:
                continue
            xpos, xmat = pose
            with self.server.atomic():
                for handle, p, r in zip(self.handles, xpos, xmat):
                    mujoco.mju_mat2Quat(quat, r)
                    handle.position = p
                    handle.wxyz = quat.copy()

    def close(self):
        self._stop.set()
        self._thread.join(timeout=2.0)
        self.server.stop()

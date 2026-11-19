"""Build the simulated scene: robot MJCF plus a dexterous hand on each wrist.

The hands are attached with MjSpec, so they move with the arm. The wrist
frame of tiangong3 is the body `wrist_roll_{l,r}_link`; `left_tcp_link` /
`right_tcp_link` are merged into it (0.044 m further along -z) and their mesh
ends about 0.105 m below that. The hand is mounted at the end of that mesh.
This is an approximation: the real hand mounting is not modelled.

A fixed bar is placed in the world just below each hand's palm (for the arm
at its zero pose) so that closing the hand produces contact and touch
readings. It does not move with the arm.
"""

import mujoco
import numpy as np

from xhumanoid_mujoco_sim.hand_model import (
    BAR_POS, BAR_QUAT, BAR_SIZE, HAND_CONTYPE, build_hand_mjcf,
)

# hand name -> (wrist body, side). side=+1 right hand, -1 left hand.
HAND_MOUNTS = {
    'left_hand': ('wrist_roll_l_link', -1.0),
    'right_hand': ('wrist_roll_r_link', 1.0),
}
# Hand origin in the wrist body frame: tcp offset plus the tcp link length.
MOUNT_POS = np.array([0.0, 0.0, -0.044 - 0.105])

# Hand frame (x along fingers, z palm normal) expressed in the wrist frame,
# with the arm hanging down (finger direction = wrist -z) and the palm facing
# the body. Columns are the hand x, y, z axes.
HAND_ROT = {
    1.0: np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], dtype=float),
    -1.0: np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=float),
}


def _quat(rot: np.ndarray) -> np.ndarray:
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, np.asarray(rot, dtype=float).reshape(9))
    return q


def hand_prefix(name: str) -> str:
    return f'{name}/'


def build_scene(robot_path: str, fix_base: bool, hands) -> mujoco.MjModel:
    """Compile the robot (optionally welded to the world) with `hands` attached."""
    spec = mujoco.MjSpec.from_file(robot_path)
    if fix_base:
        pelvis = spec.body('pelvis')
        for joint in list(pelvis.joints):
            spec.delete(joint)
    if not hands:
        return spec.compile()

    # Wrist poses of the zero configuration, to place the test bars.
    ref = spec.compile()
    ref_data = mujoco.MjData(ref)
    mujoco.mj_forward(ref, ref_data)

    for name in hands:
        wrist_name, side = HAND_MOUNTS[name]
        wrist = spec.body(wrist_name)
        quat = _quat(HAND_ROT[side])
        frame = wrist.add_frame(pos=MOUNT_POS, quat=quat)
        spec.attach(mujoco.MjSpec.from_string(build_hand_mjcf(side)),
                    prefix=hand_prefix(name), frame=frame)

        bid = mujoco.mj_name2id(ref, mujoco.mjtObj.mjOBJ_BODY, wrist_name)
        r_wrist = ref_data.xmat[bid].reshape(3, 3)
        r_hand = r_wrist @ HAND_ROT[side]
        p_hand = ref_data.xpos[bid] + r_wrist @ MOUNT_POS
        bar_rot = np.zeros(9)
        mujoco.mju_quat2Mat(bar_rot, np.array(BAR_QUAT))
        spec.worldbody.add_geom(
            name=f'{name}_test_bar', type=mujoco.mjtGeom.mjGEOM_CYLINDER,
            size=[BAR_SIZE[0], BAR_SIZE[1], 0.0],
            pos=p_hand + r_hand @ np.array(BAR_POS),
            quat=_quat(r_hand @ bar_rot.reshape(3, 3)),
            contype=HAND_CONTYPE, conaffinity=HAND_CONTYPE, group=1,
            friction=[1.0, 0.005, 0.0001], rgba=[0.45, 0.5, 0.6, 1.0])
    return spec.compile()

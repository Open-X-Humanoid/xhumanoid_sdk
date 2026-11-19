"""Minimal MJCF of a 6-motor dexterous hand, generated at runtime.

This is a simplified stand-in (capsule links, no meshes), not the BrainCo
Revo model. Motor order follows the xhumanoid_sdk hand examples:
0 thumb flex, 1 thumb rotate, 2 index, 3 middle, 4 ring, 5 pinky.

Every motor is a position actuator whose joint angle is a linear function of
the protocol value 1 (open) .. 1000 (closed). The distal joints of a finger
follow its first joint through an equality constraint. A fixed bar sits under
the palm, so closing the fingers produces contact and touch readings.
"""

# Protocol range of the SDK examples.
POS_MIN = 1
POS_MAX = 1000

# Joint angle (rad) of each motor's actuated joint at POS_MAX.
MOTOR_RANGE = [1.0, 1.2, 1.2, 1.2, 1.2, 1.2]

FINGERS = ['index', 'middle', 'ring', 'pinky']
FINGER_Y = {'index': 0.030, 'middle': 0.010, 'ring': -0.010, 'pinky': -0.030}
FINGER_LEN = {'index': (0.040, 0.030, 0.025), 'middle': (0.044, 0.032, 0.026),
              'ring': (0.040, 0.030, 0.025), 'pinky': (0.032, 0.024, 0.020)}


def _finger(name: str, side: float) -> str:
    l1, l2, l3 = FINGER_LEN[name]
    y = FINGER_Y[name] * side
    return f"""
      <body name="{name}_1" pos="0.085 {y} 0">
        <joint name="{name}_j1" axis="0 1 0" range="0 {MOTOR_RANGE[2]}"/>
        <geom type="capsule" fromto="0 0 0 {l1} 0 0" size="0.0085"/>
        <body name="{name}_2" pos="{l1} 0 0">
          <joint name="{name}_j2" axis="0 1 0" range="0 1.6"/>
          <geom type="capsule" fromto="0 0 0 {l2} 0 0" size="0.008"/>
          <body name="{name}_3" pos="{l2} 0 0">
            <joint name="{name}_j3" axis="0 1 0" range="0 1.2"/>
            <geom type="capsule" fromto="0 0 0 {l3} 0 0" size="0.0075"/>
            <site name="{name}_tip" pos="{l3} 0 0" size="0.011"/>
          </body>
        </body>
      </body>"""


def build_hand_mjcf(side: float = 1.0) -> str:
    """Return the MJCF. side=+1 right hand (thumb at +y), -1 left hand."""
    fingers = ''.join(_finger(n, side) for n in FINGERS)
    # Rotating about -side*x swings a thumb at y=side*0.05 towards the grasp (-z) side.
    return f"""
<mujoco model="brainco_hand_sim">
  <compiler angle="radian"/>
  <option timestep="0.001" integrator="implicitfast"/>
  <default>
    <joint damping="0.002" armature="0.0005"/>
    <geom contype="1" conaffinity="1" friction="1 0.005 0.0001" rgba="0.8 0.8 0.85 1"/>
  </default>
  <worldbody>
    <geom name="palm" type="box" size="0.04 0.045 0.012" pos="0.04 0 0"
          contype="0" conaffinity="0"/>
    <geom name="bar" type="cylinder" size="0.02 0.07" pos="0.065 0 -0.04"
          euler="1.5708 0 0"/>
    {fingers}
    <body name="thumb_0" pos="0.02 {0.05 * side} 0">
      <joint name="thumb_rot" axis="{-side} 0 0" range="0 {MOTOR_RANGE[1]}"/>
      <geom type="capsule" fromto="0 0 0 0.02 0 0" size="0.009"/>
      <body name="thumb_1" pos="0.02 0 0">
        <joint name="thumb_j1" axis="0 1 0" range="0 {MOTOR_RANGE[0]}"/>
        <geom type="capsule" fromto="0 0 0 0.035 0 0" size="0.0085"/>
        <body name="thumb_2" pos="0.035 0 0">
          <joint name="thumb_j2" axis="0 1 0" range="0 1.2"/>
          <geom type="capsule" fromto="0 0 0 0.028 0 0" size="0.008"/>
          <site name="thumb_tip" pos="0.028 0 0" size="0.011"/>
        </body>
      </body>
    </body>
  </worldbody>
  <equality>
    {''.join(f'''
    <joint joint1="{n}_j2" joint2="{n}_j1" polycoef="0 1.0 0 0 0"/>
    <joint joint1="{n}_j3" joint2="{n}_j1" polycoef="0 0.7 0 0 0"/>''' for n in FINGERS)}
    <joint joint1="thumb_j2" joint2="thumb_j1" polycoef="0 0.8 0 0 0"/>
  </equality>
  <actuator>
    <position name="thumb_flex" joint="thumb_j1" kp="2" kv="0.05" forcerange="-0.25 0.25" ctrlrange="0 {MOTOR_RANGE[0]}"/>
    <position name="thumb_rotate" joint="thumb_rot" kp="2" kv="0.05" forcerange="-0.25 0.25" ctrlrange="0 {MOTOR_RANGE[1]}"/>
    {''.join(f'''
    <position name="{n}" joint="{n}_j1" kp="2" kv="0.05" forcerange="-0.25 0.25" ctrlrange="0 {MOTOR_RANGE[2]}"/>''' for n in FINGERS)}
  </actuator>
  <sensor>
    <touch name="touch_thumb" site="thumb_tip"/>
    {''.join(f'''
    <touch name="touch_{n}" site="{n}_tip"/>''' for n in FINGERS)}
  </sensor>
</mujoco>
"""

# Per-motor command. Layout follows the message tables in single_joint_control/README.md.
uint16 name        # motor id, e.g. 21 = right shoulder pitch
float64 kp         # hybrid mode
float64 kd         # hybrid mode
float64 pos        # rad
float64 spd        # rad/s
float64 tor        # feed-forward torque, Nm (hybrid mode)
float64 cur        # max current, A (position mode)

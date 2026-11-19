# Only `name` and `pos` are read by xhumanoid_sdk; the other fields are assumptions
# modelled on bodyctrl_msgs/MotorStatus.
uint16 name
float64 pos          # rad
float64 speed        # rad/s
float64 current      # sim: joint actuator torque in Nm (no motor model)
float64 temperature  # sim: always 0

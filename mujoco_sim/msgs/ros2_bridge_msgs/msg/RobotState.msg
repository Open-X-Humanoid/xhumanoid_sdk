# Reduced RobotState: only the fields xhumanoid_sdk reads (imu, arm.status).
std_msgs/Header header
ImuStatus imu
MotorStatusGroup arm

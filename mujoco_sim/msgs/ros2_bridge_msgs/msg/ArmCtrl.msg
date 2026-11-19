std_msgs/Header header
uint8 mode         # 0=position, 1=force-position hybrid, 2=speed, 3=zeroing, 4=distance, 5=current
uint8 label
uint8 reserved
MotorCtrl[] ctrl

# SIMULATION-ONLY stand-in. Field names come from the xhumanoid_sdk examples;
# the integer widths are inferred from how the examples use them.
uint8 mode            # 1=position 2=speed 3=current 4=PWM 5=position+time 6=position+speed
uint16[6] positions   # 1 (open) .. 1000 (closed)
int16[6] speeds
int16[6] currents
int16[6] pwms
uint16[6] durations

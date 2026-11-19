# Layout as documented in brainco_hand_touch_display/README.md
uint16 normal_force1          # 0.01 N
uint16 tangential_force1      # 0.01 N
uint16 tangential_direction1  # 0..359 deg, 65535 = invalid
uint32 self_proximity1
uint16 status                 # low byte: 0 ok, 1 bad data, 2 comm error

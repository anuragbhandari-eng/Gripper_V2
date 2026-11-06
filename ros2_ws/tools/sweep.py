"""Drive the jaw through open-close cycles at the node's real speed and print wall-clock cycle starts."""
import time
import rclpy
from std_msgs.msg import Float64

OPEN, CLOSED, HOLD, MOVE = 0.0605, 0.0, 0.8, 0.7
rclpy.init()
node = rclpy.create_node('sweep_recorder')
pub = node.create_publisher(Float64, 'jaw_gap_command', 10)
time.sleep(1.5)
pub.publish(Float64(data=OPEN))
time.sleep(2.0)
for cycle in range(3):
    print(f'CYCLE {cycle} {time.time():.4f}', flush=True)
    time.sleep(HOLD)
    pub.publish(Float64(data=CLOSED))
    time.sleep(MOVE + HOLD)
    pub.publish(Float64(data=OPEN))
    time.sleep(MOVE)
print(f'END {time.time():.4f}', flush=True)
rclpy.shutdown()

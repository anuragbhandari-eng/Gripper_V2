"""A small window with a jaw-gap slider in mm that commands the kinematics node."""
import tkinter as tk

import rclpy
from std_msgs.msg import Float64

from lead_screw_gripper_kinematics.linkage import GAP_MAX


def main():
    rclpy.init()
    node = rclpy.create_node('jaw_slider')
    publisher = node.create_publisher(Float64, 'jaw_gap_command', 10)

    def send(value_mm):
        publisher.publish(Float64(data=float(value_mm) / 1000.0))

    window = tk.Tk()
    window.title('Jaw gap')
    slider = tk.Scale(window, label='Jaw gap (mm)', from_=0.0, to=GAP_MAX * 1000.0,
                      resolution=0.5, orient=tk.HORIZONTAL, length=400, command=send)
    slider.set(30.0)
    slider.pack(padx=12, pady=12)

    # Send the starting value again once the kinematics node has had time to connect
    window.after(1500, lambda: send(slider.get()))

    def spin():
        # Let ROS do its work between window updates; close the window when ROS shuts down
        if rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0)
            window.after(50, spin)
        else:
            window.destroy()

    window.after(50, spin)
    try:
        window.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

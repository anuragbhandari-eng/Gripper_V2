// ros2_control hardware interface for the lead-screw gripper.
//
// The gripper has one moving joint as far as ROS is concerned: "jaw_gap", the distance between the narrow-tip
// pads in metres (0 to 0.0605). This plugin sends the controller's commands to the Pico firmware
// (gripper_fabrication_rev7/firmware/ros_main.py) over USB serial and reads the jaw gap back.
//
// Interfaces on the jaw_gap joint:
//   command: position (m), effort (N per jaw, the grip force limit; optional)
//   state:   position (m), velocity (m/s)
#ifndef LEAD_SCREW_GRIPPER_HARDWARE__GRIPPER_SYSTEM_HPP_
#define LEAD_SCREW_GRIPPER_HARDWARE__GRIPPER_SYSTEM_HPP_

#include <string>

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_component_interface_params.hpp"
#include "lead_screw_gripper_hardware/serial_port.hpp"
#include "rclcpp_lifecycle/state.hpp"

namespace lead_screw_gripper_hardware
{

// One `S` reply from the firmware, in firmware units (mm, mm/s)
struct Status
{
  double gap_mm = 0.0;     // NaN until homed
  double vel_mm_s = 0.0;
  double amps = 0.0;
  int flags = 0;
};

// Status flags, same numbers as gripper_core.py
enum : int
{
  F_HOMED = 1, F_MOVING = 2, F_STALLED = 4, F_NO_POWER = 8, F_DRIVER = 16, F_ENCODER = 32, F_HOMING = 64,
  F_FAULTS = F_NO_POWER | F_DRIVER | F_ENCODER,
};

// Parse "S <gap> <vel> <amps> <flags>". Returns false if the line is not a status line.
bool parse_status(const std::string & line, Status & status);

class GripperSystem : public hardware_interface::SystemInterface
{
public:
  using CallbackReturn = hardware_interface::CallbackReturn;

  CallbackReturn on_init(const hardware_interface::HardwareComponentInterfaceParams & params) override;
  CallbackReturn on_configure(const rclcpp_lifecycle::State & previous_state) override;
  CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override;
  CallbackReturn on_deactivate(const rclcpp_lifecycle::State & previous_state) override;
  CallbackReturn on_cleanup(const rclcpp_lifecycle::State & previous_state) override;
  CallbackReturn on_shutdown(const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;
  hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  bool read_status(Status & status);
  std::string describe_faults(int flags) const;

  // Settings from the <hardware> block of the robot description
  std::string port_ = "/dev/ttyACM0";
  int timeout_ms_ = 50;
  bool home_on_activate_ = true;
  double home_timeout_s_ = 20.0;
  double default_force_ = 30.0;

  SerialPort serial_;
  std::string joint_;            // "jaw_gap"
  bool has_effort_command_ = false;
  int missed_replies_ = 0;
  double sent_gap_mm_ = -1.0;    // last gap sent with G (negative: nothing sent yet)
  double sent_force_ = -1.0;
};

}  // namespace lead_screw_gripper_hardware

#endif  // LEAD_SCREW_GRIPPER_HARDWARE__GRIPPER_SYSTEM_HPP_

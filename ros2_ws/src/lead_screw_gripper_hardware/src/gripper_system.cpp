// ros2_control hardware interface for the lead-screw gripper: see gripper_system.hpp.
//
// Every control cycle (50 Hz):
//   read():  send "R", get "S <gap mm> <speed mm/s> <amps> <flags>", fill the jaw_gap position and velocity.
//   write(): if the commanded gap or force changed, send "G <gap mm> <force N>".
// The serial talk happens inside read() and write(), so a slow reply delays the control loop. At 50 Hz with
// replies of a few milliseconds that is fine for a gripper; it would not be for a fast robot arm.
#include "lead_screw_gripper_hardware/gripper_system.hpp"

#include <chrono>
#include <cmath>
#include <cstdio>
#include <limits>
#include <sstream>
#include <thread>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "pluginlib/class_list_macros.hpp"
#include "rclcpp/rclcpp.hpp"

namespace lead_screw_gripper_hardware
{

namespace
{
constexpr int kMaxMissedReplies = 3;     // this many missed replies in a row is an error
constexpr double kResendGapMm = 0.05;    // only resend G when the command moved more than this
constexpr double kResendForceN = 0.5;

std::string param_or(
  const hardware_interface::HardwareInfo & info, const std::string & name, const std::string & fallback)
{
  const auto it = info.hardware_parameters.find(name);
  return it == info.hardware_parameters.end() ? fallback : it->second;
}
}  // namespace

bool parse_status(const std::string & line, Status & status)
{
  std::istringstream in(line);
  std::string tag, gap, vel, amps;
  int flags = 0;
  if (!(in >> tag >> gap >> vel >> amps >> flags) || tag != "S") {
    return false;
  }
  try {
    status.gap_mm = gap == "nan" ? std::numeric_limits<double>::quiet_NaN() : std::stod(gap);
    status.vel_mm_s = std::stod(vel);
    status.amps = std::stod(amps);
  } catch (const std::exception &) {
    return false;
  }
  status.flags = flags;
  return true;
}

hardware_interface::CallbackReturn GripperSystem::on_init(
  const hardware_interface::HardwareComponentInterfaceParams & params)
{
  if (hardware_interface::SystemInterface::on_init(params) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }
  const auto & info = info_;
  try {
    port_ = param_or(info, "port", port_);
    timeout_ms_ = std::stoi(param_or(info, "timeout_ms", "50"));
    home_on_activate_ = param_or(info, "home_on_activate", "true") == "true";
    home_timeout_s_ = std::stod(param_or(info, "home_timeout_s", "20"));
    default_force_ = std::stod(param_or(info, "default_force", "30"));
  } catch (const std::exception & e) {
    RCLCPP_ERROR(get_logger(), "Bad hardware parameter: %s", e.what());
    return CallbackReturn::ERROR;
  }

  // Exactly one joint, with position (+ optional effort) commands and position + velocity states
  if (info.joints.size() != 1) {
    RCLCPP_ERROR(get_logger(), "Expected exactly 1 joint (jaw_gap), got %zu", info.joints.size());
    return CallbackReturn::ERROR;
  }
  const auto & joint = info.joints[0];
  joint_ = joint.name;
  bool has_position_command = false;
  for (const auto & c : joint.command_interfaces) {
    if (c.name == hardware_interface::HW_IF_POSITION) {
      has_position_command = true;
    } else if (c.name == hardware_interface::HW_IF_EFFORT) {
      has_effort_command_ = true;
    } else {
      RCLCPP_ERROR(get_logger(), "Unsupported command interface '%s'", c.name.c_str());
      return CallbackReturn::ERROR;
    }
  }
  if (!has_position_command) {
    RCLCPP_ERROR(get_logger(), "Joint '%s' needs a position command interface", joint_.c_str());
    return CallbackReturn::ERROR;
  }
  if (joint.state_interfaces.size() != 2 ||
    joint.state_interfaces[0].name != hardware_interface::HW_IF_POSITION ||
    joint.state_interfaces[1].name != hardware_interface::HW_IF_VELOCITY)
  {
    RCLCPP_ERROR(get_logger(), "Joint '%s' needs state interfaces position then velocity", joint_.c_str());
    return CallbackReturn::ERROR;
  }
  return CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn GripperSystem::on_configure(const rclcpp_lifecycle::State &)
{
  std::string error;
  if (!serial_.open(port_, error)) {
    RCLCPP_ERROR(get_logger(), "%s. Is the gripper plugged in, and is Thonny closed?", error.c_str());
    return CallbackReturn::ERROR;
  }
  // The Pico may still be printing its boot messages: give it a few tries to answer "?"
  std::string reply;
  for (int i = 0; i < 5; ++i) {
    if (serial_.request("?", reply, 200) && reply == "ID lsg 1") {
      RCLCPP_INFO(get_logger(), "Gripper firmware found on %s", port_.c_str());
      missed_replies_ = 0;
      return CallbackReturn::SUCCESS;
    }
  }
  RCLCPP_ERROR(
    get_logger(), "No gripper firmware on %s (last reply: '%s'). Is ros_main.py saved as main.py on the Pico?",
    port_.c_str(), reply.c_str());
  serial_.close();
  return CallbackReturn::ERROR;
}

hardware_interface::CallbackReturn GripperSystem::on_activate(const rclcpp_lifecycle::State &)
{
  Status st;
  if (!read_status(st)) {
    RCLCPP_ERROR(get_logger(), "The gripper does not answer");
    return CallbackReturn::ERROR;
  }
  if (st.flags & F_FAULTS) {
    RCLCPP_ERROR(get_logger(), "Gripper fault: %s", describe_faults(st.flags).c_str());
    return CallbackReturn::ERROR;
  }
  if (!(st.flags & F_HOMED)) {
    if (!home_on_activate_) {
      RCLCPP_ERROR(get_logger(), "The gripper is not homed and home_on_activate is false");
      return CallbackReturn::ERROR;
    }
    // Homing closes the jaws slowly until they stop. Keep objects out of the jaws while this runs.
    // This blocks the controller manager for up to home_timeout_s, which is fine at start-up only.
    std::string reply;
    if (!serial_.request("H", reply, timeout_ms_) || reply != "OK") {
      RCLCPP_ERROR(get_logger(), "Homing refused: '%s'", reply.c_str());
      return CallbackReturn::ERROR;
    }
    RCLCPP_INFO(get_logger(), "Homing: closing the jaws until they stop...");
    const auto deadline = std::chrono::steady_clock::now() +
      std::chrono::duration<double>(home_timeout_s_);
    while (true) {
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
      if (!read_status(st)) {
        RCLCPP_ERROR(get_logger(), "The gripper stopped answering while homing");
        return CallbackReturn::ERROR;
      }
      if (st.flags & F_FAULTS) {
        RCLCPP_ERROR(get_logger(), "Gripper fault while homing: %s", describe_faults(st.flags).c_str());
        return CallbackReturn::ERROR;
      }
      if (st.flags & F_HOMED) {break;}
      if (!(st.flags & F_HOMING)) {
        RCLCPP_ERROR(get_logger(), "Homing failed: the jaws never stopped. Check the encoder.");
        return CallbackReturn::ERROR;
      }
      if (std::chrono::steady_clock::now() > deadline) {
        serial_.request("X", reply, timeout_ms_);
        RCLCPP_ERROR(get_logger(), "Homing timed out after %.0f s", home_timeout_s_);
        return CallbackReturn::ERROR;
      }
    }
    RCLCPP_INFO(get_logger(), "Homed. Jaw gap %.1f mm", st.gap_mm);
  }

  // Start with the command equal to where the jaws are, so nothing jumps when the controller starts.
  const double gap_m = st.gap_mm / 1000.0;
  set_state(joint_ + "/" + hardware_interface::HW_IF_POSITION, gap_m);
  set_state(joint_ + "/" + hardware_interface::HW_IF_VELOCITY, 0.0);
  set_command(joint_ + "/" + hardware_interface::HW_IF_POSITION, gap_m);
  if (has_effort_command_) {
    set_command(joint_ + "/" + hardware_interface::HW_IF_EFFORT, default_force_);
  }
  sent_gap_mm_ = -1.0;
  sent_force_ = -1.0;
  return CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn GripperSystem::on_deactivate(const rclcpp_lifecycle::State &)
{
  // Stop where it is. The driver stays on, so an object being held is not dropped.
  std::string reply;
  serial_.request("X", reply, timeout_ms_);
  return CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn GripperSystem::on_cleanup(const rclcpp_lifecycle::State &)
{
  serial_.close();
  return CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn GripperSystem::on_shutdown(const rclcpp_lifecycle::State &)
{
  if (serial_.is_open()) {
    std::string reply;
    serial_.request("X", reply, timeout_ms_);
    serial_.close();
  }
  return CallbackReturn::SUCCESS;
}

bool GripperSystem::read_status(Status & status)
{
  std::string reply;
  if (serial_.request("R", reply, timeout_ms_) && parse_status(reply, status)) {
    missed_replies_ = 0;
    return true;
  }
  ++missed_replies_;
  return false;
}

std::string GripperSystem::describe_faults(int flags) const
{
  std::string s;
  if (flags & F_NO_POWER) {s += "no motor power (plug the USB-C power in) ";}
  if (flags & F_DRIVER) {s += "TMC2209 driver not answering ";}
  if (flags & F_ENCODER) {s += "AS5600 encoder not answering ";}
  return s.empty() ? "none" : s;
}

hardware_interface::return_type GripperSystem::read(const rclcpp::Time &, const rclcpp::Duration &)
{
  Status st;
  if (!read_status(st)) {
    if (missed_replies_ >= kMaxMissedReplies) {
      RCLCPP_ERROR(get_logger(), "No reply from the gripper %d times in a row", missed_replies_);
      return hardware_interface::return_type::ERROR;
    }
    return hardware_interface::return_type::OK;   // keep the last values for a missed cycle or two
  }
  if (st.flags & F_FAULTS) {
    RCLCPP_ERROR(get_logger(), "Gripper fault: %s", describe_faults(st.flags).c_str());
    return hardware_interface::return_type::ERROR;
  }
  if (!(st.flags & F_HOMED) || std::isnan(st.gap_mm)) {
    RCLCPP_ERROR(get_logger(), "The gripper lost its position (driver restart?). Restart to home again.");
    return hardware_interface::return_type::ERROR;
  }
  set_state(joint_ + "/" + hardware_interface::HW_IF_POSITION, st.gap_mm / 1000.0);
  set_state(joint_ + "/" + hardware_interface::HW_IF_VELOCITY, st.vel_mm_s / 1000.0);
  return hardware_interface::return_type::OK;
}

hardware_interface::return_type GripperSystem::write(const rclcpp::Time &, const rclcpp::Duration &)
{
  const double gap_m = get_command<double>(joint_ + "/" + hardware_interface::HW_IF_POSITION);
  if (!std::isfinite(gap_m)) {
    return hardware_interface::return_type::OK;   // no command yet
  }
  double force = default_force_;
  if (has_effort_command_) {
    const double f = get_command<double>(joint_ + "/" + hardware_interface::HW_IF_EFFORT);
    if (std::isfinite(f) && f > 0.0) {force = f;}
  }
  const double gap_mm = gap_m * 1000.0;
  if (sent_gap_mm_ >= 0.0 && std::fabs(gap_mm - sent_gap_mm_) < kResendGapMm &&
    std::fabs(force - sent_force_) < kResendForceN)
  {
    return hardware_interface::return_type::OK;   // nothing new to send
  }
  char line[64];
  std::snprintf(line, sizeof(line), "G %.3f %.1f", gap_mm, force);
  std::string reply;
  if (!serial_.request(line, reply, timeout_ms_)) {
    ++missed_replies_;
    return missed_replies_ >= kMaxMissedReplies ?
           hardware_interface::return_type::ERROR : hardware_interface::return_type::OK;
  }
  missed_replies_ = 0;
  if (reply != "OK") {
    RCLCPP_ERROR(get_logger(), "Gripper refused '%s': %s", line, reply.c_str());
    return hardware_interface::return_type::ERROR;
  }
  sent_gap_mm_ = gap_mm;
  sent_force_ = force;
  return hardware_interface::return_type::OK;
}

}  // namespace lead_screw_gripper_hardware

PLUGINLIB_EXPORT_CLASS(lead_screw_gripper_hardware::GripperSystem, hardware_interface::SystemInterface)

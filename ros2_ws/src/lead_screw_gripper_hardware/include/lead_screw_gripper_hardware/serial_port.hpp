// A small serial port for line-based talk with the Pico (or the fake Pico's pseudo-terminal).
// Uses only Linux system calls (termios, poll), no extra library.
#ifndef LEAD_SCREW_GRIPPER_HARDWARE__SERIAL_PORT_HPP_
#define LEAD_SCREW_GRIPPER_HARDWARE__SERIAL_PORT_HPP_

#include <string>

namespace lead_screw_gripper_hardware
{

class SerialPort
{
public:
  ~SerialPort();
  // Open the port at 115200 baud in raw mode. Returns false and fills `error` if it fails.
  bool open(const std::string & path, std::string & error);
  void close();
  bool is_open() const {return fd_ >= 0;}
  // Throw away anything already received (a late reply to an earlier command).
  void flush_input();
  // Send `line` followed by a newline.
  bool write_line(const std::string & line);
  // Wait up to `timeout_ms` for one full line. Returns false on timeout or error.
  bool read_line(std::string & line, int timeout_ms);
  // One command, one reply: flush, send, wait for the reply.
  bool request(const std::string & command, std::string & reply, int timeout_ms);

private:
  int fd_ = -1;
  std::string buffer_;  // bytes received but not yet returned as a line
};

}  // namespace lead_screw_gripper_hardware

#endif  // LEAD_SCREW_GRIPPER_HARDWARE__SERIAL_PORT_HPP_

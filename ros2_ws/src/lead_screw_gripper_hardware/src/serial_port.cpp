// Serial port for the gripper: see serial_port.hpp.
#include "lead_screw_gripper_hardware/serial_port.hpp"

#include <fcntl.h>
#include <poll.h>
#include <termios.h>
#include <unistd.h>

#include <cerrno>
#include <chrono>
#include <cstring>

namespace lead_screw_gripper_hardware
{

SerialPort::~SerialPort() {close();}

bool SerialPort::open(const std::string & path, std::string & error)
{
  close();
  fd_ = ::open(path.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
  if (fd_ < 0) {
    error = "cannot open " + path + ": " + std::strerror(errno);
    return false;
  }
  termios tty{};
  if (tcgetattr(fd_, &tty) != 0) {
    error = "not a serial port: " + path;
    close();
    return false;
  }
  cfmakeraw(&tty);              // no echo, no line editing, no newline translation
  cfsetispeed(&tty, B115200);   // ignored by USB serial and by pseudo-terminals, needed for a real UART
  cfsetospeed(&tty, B115200);
  tty.c_cflag |= (CLOCAL | CREAD);
  if (tcsetattr(fd_, TCSANOW, &tty) != 0) {
    error = "cannot configure " + path;
    close();
    return false;
  }
  buffer_.clear();
  flush_input();
  return true;
}

void SerialPort::close()
{
  if (fd_ >= 0) {
    ::close(fd_);
    fd_ = -1;
  }
  buffer_.clear();
}

void SerialPort::flush_input()
{
  if (fd_ < 0) {return;}
  tcflush(fd_, TCIFLUSH);
  char tmp[256];
  while (::read(fd_, tmp, sizeof(tmp)) > 0) {}
  buffer_.clear();
}

bool SerialPort::write_line(const std::string & line)
{
  if (fd_ < 0) {return false;}
  const std::string out = line + "\n";
  size_t sent = 0;
  while (sent < out.size()) {
    const ssize_t n = ::write(fd_, out.data() + sent, out.size() - sent);
    if (n < 0) {
      if (errno == EAGAIN || errno == EINTR) {continue;}
      return false;
    }
    sent += static_cast<size_t>(n);
  }
  return true;
}

bool SerialPort::read_line(std::string & line, int timeout_ms)
{
  if (fd_ < 0) {return false;}
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
  while (true) {
    const auto nl = buffer_.find('\n');
    if (nl != std::string::npos) {
      line = buffer_.substr(0, nl);
      buffer_.erase(0, nl + 1);
      if (!line.empty() && line.back() == '\r') {line.pop_back();}
      return true;
    }
    const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
      deadline - std::chrono::steady_clock::now()).count();
    if (left <= 0) {return false;}
    pollfd p{fd_, POLLIN, 0};
    const int r = ::poll(&p, 1, static_cast<int>(left));
    if (r < 0 && errno == EINTR) {continue;}
    if (r <= 0) {return false;}
    if (p.revents & (POLLERR | POLLHUP | POLLNVAL)) {return false;}  // unplugged, or the fake Pico stopped
    char tmp[256];
    const ssize_t n = ::read(fd_, tmp, sizeof(tmp));
    if (n <= 0) {
      if (n < 0 && (errno == EAGAIN || errno == EINTR)) {continue;}
      return false;
    }
    buffer_.append(tmp, static_cast<size_t>(n));
    if (buffer_.size() > 4096) {buffer_.clear();}  // garbage with no newline: drop it
  }
}

bool SerialPort::request(const std::string & command, std::string & reply, int timeout_ms)
{
  flush_input();
  return write_line(command) && read_line(reply, timeout_ms);
}

}  // namespace lead_screw_gripper_hardware

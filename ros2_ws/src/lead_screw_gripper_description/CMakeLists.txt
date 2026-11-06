cmake_minimum_required(VERSION 3.8)
project(lead_screw_gripper_description)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch meshes onshape onshape_render rviz urdf worlds
  DESTINATION share/${PROJECT_NAME})

ament_package()

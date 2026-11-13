"""Run the gripper through ros2_control.

    # real gripper on USB (after the bench tests, with ros_main.py on the Pico as main.py)
    ros2 launch lead_screw_gripper_bringup hardware.launch.py
    # no hardware: the fake Pico (real firmware logic + simulated gripper), a 30 mm object after homing
    ros2 launch lead_screw_gripper_bringup hardware.launch.py fake:=true object_mm:=30
    # no serial at all: ros2_control's mock hardware (checks the description and controllers only)
    ros2 launch lead_screw_gripper_bringup hardware.launch.py use_mock_hardware:=true

Then command it with the standard action, for example open to 45 mm:
    ros2 action send_goal /gripper_controller/gripper_cmd control_msgs/action/ParallelGripperCommand \
      "{command: {name: [jaw_gap], position: [0.045], effort: [30.0]}}"
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _setup(context):
    fake = LaunchConfiguration('fake').perform(context) == 'true'
    mock = LaunchConfiguration('use_mock_hardware').perform(context) == 'true'
    port = LaunchConfiguration('fake_link').perform(context) if fake else LaunchConfiguration('port').perform(context)
    rviz = LaunchConfiguration('rviz').perform(context) == 'true'
    object_mm = LaunchConfiguration('object_mm').perform(context)

    bringup = FindPackageShare('lead_screw_gripper_bringup')
    xacro_file = PathJoinSubstitution([bringup, 'urdf', 'lead_screw_gripper_hardware.urdf.xacro'])
    robot_description = ParameterValue(Command([
        'xacro ', xacro_file, ' port:=', port, ' use_mock_hardware:=', 'true' if mock else 'false',
    ]), value_type=str)
    controllers = PathJoinSubstitution([bringup, 'config', 'hardware_controllers.yaml'])

    actions = [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}]),
        Node(package='lead_screw_gripper_bringup', executable='gap_to_joints'),
    ]

    control = [
        Node(package='controller_manager', executable='ros2_control_node',
             parameters=[controllers],
             remappings=[('~/robot_description', '/robot_description')],
             output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['joint_state_broadcaster', '--controller-manager-timeout', '60']),
        Node(package='controller_manager', executable='spawner',
             arguments=['gripper_controller', '--controller-manager-timeout', '60']),
    ]
    if fake and not mock:
        fake_args = ['--link', port, '--verbose']
        if object_mm:
            fake_args += ['--object-mm', object_mm]
        actions.append(Node(package='lead_screw_gripper_bringup', executable='fake_pico',
                            arguments=fake_args, output='screen'))
        actions.append(TimerAction(period=2.0, actions=control))   # give the fake serial port time to appear
    else:
        actions += control

    if rviz:
        rviz_config = PathJoinSubstitution([FindPackageShare('lead_screw_gripper_description'),
                                            'rviz', 'display.rviz'])
        actions.append(Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config]))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('port', default_value='/dev/ttyACM0', description='Pico USB serial port'),
        DeclareLaunchArgument('fake', default_value='false',
                              description='true: run the fake Pico instead of the real gripper'),
        DeclareLaunchArgument('fake_link', default_value='/tmp/lsg_fake_pico',
                              description='where the fake Pico puts its serial port'),
        DeclareLaunchArgument('object_mm', default_value='',
                              description='fake Pico only: object width (mm) placed after homing'),
        DeclareLaunchArgument('use_mock_hardware', default_value='false',
                              description="true: ros2_control's mock hardware, no serial at all"),
        DeclareLaunchArgument('rviz', default_value='true', description='open RViz'),
        OpaqueFunction(function=_setup),
    ])

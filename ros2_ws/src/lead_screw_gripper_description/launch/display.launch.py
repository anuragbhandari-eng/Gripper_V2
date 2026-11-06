from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('lead_screw_gripper_description')
    # Which robot file in urdf/ to show: the full Onshape export (default)
    # or the phase 3 hand-written model (lead_screw_gripper.urdf.xacro)
    model = LaunchConfiguration('model')
    xacro_file = PathJoinSubstitution([pkg, 'urdf', model])
    rviz_config = PathJoinSubstitution([pkg, 'rviz', 'display.rviz'])

    # Run xacro on the file and pass the resulting URDF text to robot_state_publisher
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('model', default_value='lead_screw_gripper_full.urdf.xacro'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
        ),
    ])

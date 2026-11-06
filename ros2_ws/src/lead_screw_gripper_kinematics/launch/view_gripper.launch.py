from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description = FindPackageShare('lead_screw_gripper_description')
    xacro_file = PathJoinSubstitution([description, 'urdf', LaunchConfiguration('model')])
    rviz_config = PathJoinSubstitution([description, 'rviz', LaunchConfiguration('rviz')])
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('slider', default_value='true',
                              description='Open the jaw-gap slider window'),
        DeclareLaunchArgument('model', default_value='lead_screw_gripper_full.urdf.xacro',
                              description='Robot file in urdf/ (lead_screw_gripper_render.urdf.xacro: covers off)'),
        DeclareLaunchArgument('rviz', default_value='display.rviz',
                              description='RViz config in rviz/ (render.rviz: page colours, for recording)'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        # Replaces joint_state_publisher_gui: one jaw gap in, all nine joints out
        Node(
            package='lead_screw_gripper_kinematics',
            executable='jaw_kinematics',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
        ),
        # Slider window (mm) that sends jaw_gap_command to the kinematics node
        Node(
            package='lead_screw_gripper_kinematics',
            executable='jaw_slider',
            condition=IfCondition(LaunchConfiguration('slider')),
        ),
    ])

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument, ExecuteProcess,
                            IncludeLaunchDescription, RegisterEventHandler, TimerAction)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description = FindPackageShare('lead_screw_gripper_description')
    xacro_file = PathJoinSubstitution([description, 'urdf', 'lead_screw_gripper_gazebo.urdf.xacro'])
    world = PathJoinSubstitution([description, 'worlds', 'grasp_test.sdf'])
    controllers = PathJoinSubstitution([description, 'config', 'gripper_controllers.yaml'])
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)
    sim_time = {'use_sim_time': True}

    # Lets Gazebo find the package:// meshes
    mesh_path = os.path.join(get_package_share_directory('lead_screw_gripper_description'), '..')

    def spawner(controller):
        return Node(package='controller_manager', executable='spawner',
                    arguments=[controller, '--param-file', controllers])

    spawn_robot = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'lead_screw_gripper'],
    )

    return LaunchDescription([
        DeclareLaunchArgument('demo', default_value='true',
                              description='Run the scripted grasp test'),
        DeclareLaunchArgument('rviz', default_value='false', description='Also open RViz'),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', mesh_path),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])),
            launch_arguments=[('gz_args', ['-r -v 1 ', world])],
        ),
        # Gazebo's camera starts metres away; once the window is up, move it close to the gripper
        TimerAction(period=8.0, actions=[ExecuteProcess(
            cmd=['gz', 'service', '-s', '/gui/move_to/pose', '--reqtype', 'gz.msgs.GUICamera',
                 '--reptype', 'gz.msgs.Boolean', '--timeout', '2000', '--req',
                 'pose: {position: {x: 0.18, y: -0.054, z: 0.214}, '
                 'orientation: {x: -0.3485, y: 0.0671, z: 0.9180, w: 0.1768}}'],
            output='screen',
        )]),
        Node(
            package='ros_gz_bridge', executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        ),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}, sim_time],
        ),
        spawn_robot,
        # Start the controllers once the robot is in Gazebo
        RegisterEventHandler(OnProcessExit(
            target_action=spawn_robot,
            on_exit=[spawner('joint_state_broadcaster'),
                     spawner('gripper_controller'),
                     spawner('lift_controller')],
        )),
        Node(
            package='lead_screw_gripper_kinematics', executable='jaw_kinematics',
            parameters=[{'use_controller': True, 'jaw_gap': 0.050}, sim_time],
        ),
        Node(
            package='lead_screw_gripper_kinematics', executable='grasp_demo',
            parameters=[{'start_delay': 10.0}, sim_time],  # after the camera move above
            condition=IfCondition(LaunchConfiguration('demo')),
        ),
        Node(
            package='rviz2', executable='rviz2',
            arguments=['-d', PathJoinSubstitution([description, 'rviz', 'display.rviz'])],
            parameters=[sim_time],
            condition=IfCondition(LaunchConfiguration('rviz')),
        ),
    ])

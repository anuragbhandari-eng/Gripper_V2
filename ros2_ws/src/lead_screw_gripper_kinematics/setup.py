from setuptools import find_packages, setup

package_name = 'lead_screw_gripper_kinematics'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/view_gripper.launch.py', 'launch/sim_grasp.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Anurag Bhandari',
    maintainer_email='anuragbhandari121@gmail.com',
    description='Closed-form kinematics node for the lead-screw parallel gripper: jaw gap to all joint positions',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'jaw_kinematics = lead_screw_gripper_kinematics.jaw_node:main',
            'grasp_demo = lead_screw_gripper_kinematics.grasp_demo:main',
            'jaw_slider = lead_screw_gripper_kinematics.jaw_slider:main',
        ],
    },
)

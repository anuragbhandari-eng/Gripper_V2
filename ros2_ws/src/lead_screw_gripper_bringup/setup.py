import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'lead_screw_gripper_bringup'

# The fake Pico runs the real firmware logic. These two files are installed straight from the firmware
# folder, so there is only one copy of them in the repository.
FIRMWARE = os.path.join('..', '..', '..', 'gripper_fabrication_rev7', 'firmware')

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/urdf', glob('urdf/*.xacro')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/firmware',
            [os.path.join(FIRMWARE, 'gripper_core.py'), os.path.join(FIRMWARE, 'hal_sim.py')]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Anurag Bhandari',
    maintainer_email='anuragbhandari121@gmail.com',
    description='Runs the lead-screw gripper through ros2_control, with a fake Pico for testing without hardware',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'fake_pico = lead_screw_gripper_bringup.fake_pico:main',
            'gap_to_joints = lead_screw_gripper_bringup.gap_to_joints:main',
        ],
    },
)

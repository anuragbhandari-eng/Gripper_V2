"""onshape-to-robot processor: name every moving link after the joint that moves it.

Gazebo's SDF format needs link and joint names to be unique together, but the export gave
some links the same name as their joint (bell_crank_U and so on). After this processor the
links are bell_crank_U_link, finger_U_link, carriage_link, ... and base_link stays as it is.
Registered in config.json; export.sh puts this folder on the Python path.
"""
from onshape_to_robot.processor import Processor


class ProcessorLinkNames(Processor):

    def process(self, robot):
        for joint in robot.joints:
            joint.child.name = f'{joint.name}_link'

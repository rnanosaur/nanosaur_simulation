# Copyright (C) 2022, Raffaello Bonghi <raffaello@rnext.it>
# All rights reserved
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os

from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch import LaunchDescription, LaunchContext
from launch.substitutions import LaunchConfiguration
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import re

PATTERN_COMMAND = re.compile(r'(\w+):=\s*(\[[^\]]+\]|".+?"|\S+)')

def launch_setup(context: LaunchContext, support_use_sim_time, support_robot_name, support_camera_type, support_lidar_type, support_simulation_tool):

    package_nanosaur_isaac_sim = get_package_share_directory('nanosaur_isaac-sim')
    package_nanosaur_gazebo = get_package_share_directory('nanosaur_gazebo')
    
    use_sim_time = context.perform_substitution(support_use_sim_time)
    robot_name = context.perform_substitution(support_robot_name)
    camera_type = context.perform_substitution(support_camera_type)
    lidar_type = context.perform_substitution(support_lidar_type)
    simulation_tool = context.perform_substitution(support_simulation_tool)

    robot_configuration = {
            'use_sim_time': use_sim_time,
            'robot_name': robot_name,
            'camera_type': camera_type,
            'lidar_type': lidar_type,
    }

    if 'NANOSAUR_COMMANDS' in os.environ:
        print("[WARNING] Docker environment detected.")
        commands = os.environ['NANOSAUR_COMMANDS']
        commands_dict = {match.group(1): match.group(2) for match in PATTERN_COMMAND.finditer(commands)}
        print(f"Parsed commands: {commands_dict}")
        robot_configuration = commands_dict
        simulation_tool = robot_configuration.get('simulation_tool', simulation_tool)

    if simulation_tool == 'isaac-sim':
        launch_file_dir = os.path.join(package_nanosaur_isaac_sim, 'launch')
    elif simulation_tool == 'gazebo':
        launch_file_dir = os.path.join(package_nanosaur_gazebo, 'launch')
    else:
        print(f"Error: Simulation tool '{simulation_tool}' not supported")
        exit(1)

    nanosaur_sim_launcher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [launch_file_dir, '/nanosaur_bridge.launch.py']),
        launch_arguments=robot_configuration.items(),
    )
    
    return [nanosaur_sim_launcher]


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    camera_type = LaunchConfiguration('camera_type')
    lidar_type = LaunchConfiguration('lidar_type')
    simulation_tool = LaunchConfiguration('simulation_tool')
    
    use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation clock if true')

    nanosaur_cmd = DeclareLaunchArgument(
        name='robot_name',
        default_value='nanosaur',
        description='robot name (namespace). If you are working with multiple robot you can change this parameter.')

    declare_camera_type_cmd = DeclareLaunchArgument(
        name='camera_type',
        default_value='empty',
        description='camera type to use. Options: empty, Realsense, zed.')

    declare_lidar_type_cmd = DeclareLaunchArgument(
        name='lidar_type',
        default_value='empty',
        description='Lidar type to use. Options: empty, LD06.')

    declare_simulation_tool_cmd = DeclareLaunchArgument(
        name='simulation_tool',
        default_value='',
        description='Simulation tool to use. Options: gazebo, isaac_sim.')

    ld = LaunchDescription()
    ld.add_action(nanosaur_cmd)
    ld.add_action(declare_camera_type_cmd)
    ld.add_action(declare_lidar_type_cmd)
    ld.add_action(use_sim_time_cmd)
    ld.add_action(declare_simulation_tool_cmd)
    ld.add_action(OpaqueFunction(function=launch_setup, args=[use_sim_time, robot_name, camera_type, lidar_type, simulation_tool]))

    return ld
# EOF

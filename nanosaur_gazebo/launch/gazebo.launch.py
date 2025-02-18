# Copyright (C) 2024, Raffaello Bonghi <raffaello@rnext.it>
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
import re
import yaml
from pathlib import Path

from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch import LaunchDescription, LaunchContext
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

PATTERN_COMMAND = re.compile(r'(\w+):=\s*(\[[^\]]+\]|".+?"|\S+)')

def docker_decoder():
    print("[WARNING] Docker environment detected.")
    commands = os.environ['SIMULATION_COMMANDS']
    commands_dict = {match.group(1): match.group(2) for match in PATTERN_COMMAND.finditer(commands)}
    print(f"Parsed commands: {commands_dict}")
    return commands_dict


def launch_gazebo_setup(context: LaunchContext, support_world, support_headless):
    """ Reference:
        https://answers.ros.org/question/396345/ros2-launch-file-how-to-convert-launchargument-to-string/ 
        https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/main/ur_moveit_config/launch/ur_moveit.launch.py
    """
    package_gazebo = get_package_share_directory('nanosaur_gazebo')
    package_worlds = get_package_share_directory('nanosaur_worlds')
    # render namespace, dumping the support_package.
    world = context.perform_substitution(support_world)
    headless = context.perform_substitution(support_headless).lower() == 'true'
    # This variable override the argument passed to the launch file, designed only when start from docker
    if 'SIMULATION_COMMANDS' in os.environ:
        commands_dict = docker_decoder()
        world = commands_dict.get("world", 'empty')
        headless = commands_dict.get("headless", 'false').lower() == 'true'
    
    basic_world = os.path.join(package_worlds, "worlds", f'{world}.sdf')
    gui_config = os.path.join(package_gazebo, "gui", "gui.config")
    
    gz_args = f'-r -v 3 {basic_world}  --gui-config {gui_config}'
    if headless:
        print("Run Gazebo in headless mode")
        gz_args += ' -s'

    ign_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    get_package_share_directory('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py',
                )
            ]
        ),
        launch_arguments={'gz_args': gz_args}.items(),
    )

    return [ign_gazebo]


def generate_launch_description():
    world_name = LaunchConfiguration('world')

    # Set gazebo resource path
    ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH', value=[
            os.path.join(get_package_prefix('nanosaur_description'), "share"),
            ":" +
            os.path.join(get_package_share_directory('nanosaur_worlds'), "models")])

    use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    world_cmd = DeclareLaunchArgument(
        name='world',
        default_value='lab', # Empty world: empty
        description='Simulation world name.')

    headless_cmd = DeclareLaunchArgument(
        name='headless',
        default_value='false',
        description='Run Isaac Sim in headless mode'
    )
    
    headless = LaunchConfiguration('headless')

    ld = LaunchDescription()
    ld.add_action(ign_resource_path)
    ld.add_action(use_sim_time_cmd)
    ld.add_action(world_cmd)
    ld.add_action(headless_cmd)
    ld.add_action(OpaqueFunction(function=launch_gazebo_setup, args=[world_name, headless]))

    return ld
# EOF

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
from launch import LaunchDescription, LaunchContext
from launch.actions import DeclareLaunchArgument,IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource


# Convert name to stage path
WORLD_NAME_MAP = {
    "empty": "",
    "lab": "/Isaac/Environments/Simple_Room/simple_room.usd",
    "office": "/Isaac/Environments/Office/office.usd",
    "warehouse": "/Isaac/Environments/Simple_Warehouse/warehouse.usd",
}


def launch_setup(context: LaunchContext, support_world, support_isaac_sim_path, support_config_file_path, support_renderer, support_headless, support_livestream):
    # Get the package share directory
    package_isaac_sim = get_package_share_directory('isaac_sim_wrapper')
    # Get the path to the Isaac Sim folder
    world_name = context.perform_substitution(support_world)
    isaac_sim_path = context.perform_substitution(support_isaac_sim_path)
    config_file_path = context.perform_substitution(support_config_file_path)
    renderer = context.perform_substitution(support_renderer)
    headless = context.perform_substitution(support_headless).lower() == 'true'
    livestream = context.perform_substitution(support_livestream).lower() == 'true'
    # Check if the environment variable SIMULATION_IN_DOCKER is set
    # This variable overrides the livestream argument passed to the launch file
    if 'SIMULATION_IN_DOCKER' in os.environ:
        print("[WARNING] Docker environment detected.")
        # Headless mode is forced to true in Docker
        headless = True
        livestream = True
        if 'SIMULATION_HEADLESS' in os.environ:
            livestream = os.getenv('SIMULATION_HEADLESS', 'false').lower() != 'true'
        print(f"Docker environment detected. Livestream is set to {livestream}.")
        
    if 'SIMULATION_COMMANDS' in os.environ:
        print("[INFO] Simulation commands detected.")
        print(f"Simulation commands: {os.getenv('SIMULATION_COMMANDS')}")
    
    world = WORLD_NAME_MAP.get(world_name, "empty")

    isaac_sim_launcher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [os.path.join(package_isaac_sim, 'launch'), '/isaac_sim_server.launch.py']
            ),
            launch_arguments={
                'world': world,
                'isaac_sim_path': isaac_sim_path,
                'config_file_path': config_file_path,
                'renderer': renderer,
                'headless': str(headless).lower(),
                'livestream': str(livestream).lower(),
                }.items(),
    )
    
    return [isaac_sim_launcher]


def generate_launch_description():

    world = LaunchConfiguration('world')
    isaac_sim_path = LaunchConfiguration('isaac_sim_path')
    config_file_path = LaunchConfiguration('config_file_path')
    renderer = LaunchConfiguration('renderer')
    headless = LaunchConfiguration('headless')
    livestream = LaunchConfiguration('livestream')

    use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    world_cmd = DeclareLaunchArgument(
        name='world',
        default_value='empty', # Empty world: empty
        description='Simulation world name.')


    isaac_sim_path_cmd = DeclareLaunchArgument(
        name='isaac_sim_path',
        default_value='/isaac-sim',
        description='Path to Isaac Sim'
    )

    config_file_path_cmd = DeclareLaunchArgument(
        name='config_file_path',
        default_value='',
        description='Path to the configuration file'
    )
    
    renderer_cmd = DeclareLaunchArgument(
        name='renderer',
        default_value='RayTracedLighting',
        description='Set the render mode'
    )
    
    headless_cmd = DeclareLaunchArgument(
        name='headless',
        default_value='true',
        description='Run Isaac Sim in headless mode'
    )

    # Follow documentation for livestream
    # https://docs.isaacsim.omniverse.nvidia.com/latest/installation/manual_livestream_clients.html
    livestream_cmd = DeclareLaunchArgument(
        name='livestream',
        default_value='false',
        description='Enable livestream'
    )

    ld = LaunchDescription()
    ld.add_action(use_sim_time_cmd)
    ld.add_action(world_cmd)
    ld.add_action(isaac_sim_path_cmd)
    ld.add_action(config_file_path_cmd)
    ld.add_action(renderer_cmd)
    ld.add_action(headless_cmd)
    ld.add_action(livestream_cmd)
    ld.add_action(OpaqueFunction(function=launch_setup, args=[world, isaac_sim_path, config_file_path, renderer, headless, livestream]))
    
    return ld
# EOF
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

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchContext
from launch.substitutions import LaunchConfiguration
from launch.actions import ExecuteProcess, DeclareLaunchArgument, OpaqueFunction


def launch_setup(context: LaunchContext, support_isaac_sim_path, support_config_file_path, support_renderer, support_headless, support_webrtc):
    # Get the package share directory
    package_isaac_sim = get_package_share_directory('isaac_sim_wrapper')
    # Get the path to the Isaac Sim folder
    isaac_sim_path = context.perform_substitution(support_isaac_sim_path)
    config_file_path = context.perform_substitution(support_config_file_path)
    renderer = context.perform_substitution(support_renderer)
    headless = context.perform_substitution(support_headless).lower() == 'true'
    webrtc = context.perform_substitution(support_webrtc).lower() == 'true'
    # Check if the environment variable SIMULATION_HEADLESS is set to true
    # This variable overrides the headless argument passed to the launch file
    if 'SIMULATION_HEADLESS' in os.environ:
        print("Environment variable SIMULATION_HEADLESS is set to true. Running in headless mode with webRTC enabled.")
        headless = os.getenv('SIMULATION_HEADLESS', 'false').lower() == 'true'
        webrtc = os.getenv('SIMULATION_HEADLESS', 'false').lower() == 'true'
    # Read the VERSION file from the isaac_sim_folder
    version_file_path = os.path.join(isaac_sim_path, 'VERSION')
    if os.path.exists(version_file_path):
        with open(version_file_path, 'r') as version_file:
            version_content = version_file.read().strip().split('-')[0]
    else:
        print(f"Could not find the VERSION file in {isaac_sim_path}")
        print("Please make sure that the Isaac Sim folder is correct.")
        exit(1)

    print(f"Run Isaac Sim {version_content} from {isaac_sim_path} in {renderer} mode with headless={headless}")
    # Path Launcher Isaac Sim
    isaac_sim_wrapper_launcher = os.path.join(package_isaac_sim, "scripts", "isaac_sim_robot_launcher.py")
    # Check if the version is less than 4.5.0
    if version_content < '4.5.0':
        print(f"Warning: The version of Isaac Sim ({version_content}) is less than 4.5.0. Some features may not be available.")
        # Path Launcher Isaac Sim
        isaac_sim_wrapper_launcher = os.path.join(package_isaac_sim, "scripts", "old_version", "isaac_sim_robot_launcher.py")

    # Command to start Isaac Sim
    command = [f"{isaac_sim_path}/python.sh", isaac_sim_wrapper_launcher, "--renderer", renderer]
    if headless:
        command += ["--headless"]
    if webrtc:
        command += ["--webrtc"]
    # Add the configuration file if it exists
    if config_file_path:
        print(f"Load configuration file {config_file_path}")
        command += ["--config_file", config_file_path]
    # Start Isaac Sim from python script
    isaac_sim = ExecuteProcess(
            cmd=command,
            name='IsaacSim',
            output='screen',
            shell=True
        )
    
    return [isaac_sim]


def generate_launch_description():

    isaac_sim_path_cmd = DeclareLaunchArgument(
        name='isaac_sim_path',
        default_value='/isaac-sim',
        description='Path to Isaac Sim'
    )
    
    isaac_sim_path = LaunchConfiguration('isaac_sim_path')

    config_file_path_cmd = DeclareLaunchArgument(
        name='config_file_path',
        default_value='',
        description='Path to the configuration file'
    )
    
    config_file_path = LaunchConfiguration('config_file_path')

    renderer_cmd = DeclareLaunchArgument(
        name='renderer',
        default_value='RayTracedLighting',
        description='Set the render mode'
    )
    
    renderer = LaunchConfiguration('renderer')
    
    headless_cmd = DeclareLaunchArgument(
        name='headless',
        default_value='true',
        description='Run Isaac Sim in headless mode'
    )
    
    headless = LaunchConfiguration('headless')
    
    # Default WebRTC address:
    # http://localhost:8211/streaming/webrtc-client/
    webrtc_cmd = DeclareLaunchArgument(
        name='webrtc',
        default_value='false',
        description='Enable WebRTC'
    )

    webrtc = LaunchConfiguration('webrtc')
    
    ld = LaunchDescription()
    ld.add_action(isaac_sim_path_cmd)
    ld.add_action(config_file_path_cmd)
    ld.add_action(renderer_cmd)
    ld.add_action(headless_cmd)
    ld.add_action(webrtc_cmd)
    ld.add_action(OpaqueFunction(function=launch_setup, args=[isaac_sim_path, config_file_path, renderer, headless, webrtc]))
    
    return ld
# EOF
#!/usr/bin/python3
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Standard modules
import glob
import importlib
import os
import shutil
import signal
import subprocess
import sys

# Custom modules
from config import Config
from config import color_str_red
from config import color_str_green
from config import color_str_yellow

# Number of input arguments
NUM_ARGS = 1

# Other defines
LINE_SEP = "==================================================================="

# Handler to gracefully exit on ctrl+c
def sigint_handler(sig, frame):
    print(color_str_red('\nTERMINATING EXPERIMENT!'))
    sys.exit(0)

def add_env_to_cmd(cmd, param, value):
    if value != None:
        cmd.extend(["-e", "%s=%s" % (param.upper(), value)])
    return cmd

def add_volume_mount_to_cmd(cmd, src, dst):
    cmd.extend(["-v", "%s:%s" % (src, dst)])
    return cmd

def run_cmd(cmd, error_str):
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        print(color_str_red(error_str))
        sys.exit(1)

def build_docker_image(config):
    print(LINE_SEP)
    print("Building Docker image to fuzz %s ..." % config.circuit)
    print(LINE_SEP)
    cmd = ["docker", "build", \
           "-t", "gcr.io/hardware-fuzzing/%s" % config.circuit, \
           "%s/circuits/%s" % (config.root_path, config.circuit)]
    error_str = "ERROR: image build FAILED. Terminating experiment!"
    run_cmd(cmd, error_str)
    print(color_str_green("IMAGE BUILD SUCCESSFUL -- Done!"))

def run_docker_container_locally(config, exp_data_path):
    print(LINE_SEP)
    print("Running Docker container to fuzz %s ..." % config.circuit)
    print(LINE_SEP)
    cmd = ["docker", "run", "-it", "--rm", "--name", config.experiment_name]
    # Set environment variables for general configs
    cmd = add_env_to_cmd(cmd, "circuit", config.circuit)
    cmd = add_env_to_cmd(cmd, "tb", config.testbench)
    cmd = add_env_to_cmd(cmd, "fuzzer", config.fuzzer)
    # Set environment variables for HDL generator configs
    for param, value in config.hdl_gen_params.items():
        cmd = add_env_to_cmd(cmd, param, value)
    # Set environment variables for fuzzer configs
    for param, value in config.fuzzer_params.items():
        cmd = add_env_to_cmd(cmd, param, value)
    # Mount volumes for output data
    cmd.extend(["-v", "%s/logs:/src/circuits/%s/logs" % \
            (exp_data_path, config.circuit)])
    cmd.extend(["-v", "%s/out:/src/circuits/%s/out" % \
            (exp_data_path, config.circuit)])
    cmd.extend(["-v", "%s/in:/src/circuits/%s/in" % \
            (exp_data_path, config.circuit)])
    # Run container with current user/group IDs
    # cmd.extend(["-u", "%d:%d" % (os.getuid(), os.getgid())])
    # Set target Docker image and run
    cmd.extend(["-t", "gcr.io/hardware-fuzzing/%s" % config.circuit])
    # print(cmd)
    # sys.exit(1)
    # cmd.append("/bin/bash")
    error_str = "ERROR: container run FAILED. Terminating experiment!"
    run_cmd(cmd, error_str)
    print(color_str_green("CONTAINER RUN SUCCESSFUL -- Done!"))

def run_docker_container_on_gcp_vm(config, exp_data_path):
    return

def create_experiment_data_dir(config):
    exp_data_path = "%s/experiments/data/%s" % \
            (config.root_path, config.experiment_name)

    # Check if experiment data directory with same name exists
    if glob.glob(exp_data_path):
        ovw = input(color_str_yellow( \
                'WARNING: experiment data exists. Overwrite? [Yn]'))
        if ovw in {'yes', 'y', 'Y', 'YES', 'Yes', ''}:
            shutil.rmtree(exp_data_path)
        else:
            abort_str = "ABORT: re-run with different experiment name."
            print(color_str_red(abort_str))
            sys.exit(-1)

    # Create experiment data directories
    os.mkdir(exp_data_path)
    os.mkdir(os.path.join(exp_data_path, "out"))
    os.mkdir(os.path.join(exp_data_path, "logs"))

    # Copy over seeds that were used in this experiment
    seeds_dir = "%s/circuits/%s/seeds" % (config.root_path, config.circuit)
    shutil.copytree(seeds_dir, os.path.join(exp_data_path, "in"))

    # Copy over HJSON config file that was used
    shutil.copy2(config.config_filename, exp_data_path)

    return exp_data_path

# Main
def main(args):

    # Parse cmd args
    if len(args) != NUM_ARGS:
        print("Usage: [python3] ./run_experiment.py <config filename>")
        sys.exit(1)

    # Load experiment configurations
    config = Config(args[0])

    # make local directory to hold resulting data and copy of config file
    exp_data_path = create_experiment_data_dir(config)

    # Build docker image to fuzz target circuit
    build_docker_image(config)

    # Run Docker container to fuzz circuit
    if config.run_on_gcp == 0:
        run_docker_container_locally(config, exp_data_path)
    else:
        run_docker_container_on_gcp_vm(config, exp_data_path)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main(sys.argv[1:])

# # Generate fuzzer input seeds
# def copy_seeds(config):
    # print(LINE_SEP)
    # print("Copying seeds for fuzzer ...")

    # # Set fuzzer seeds input path
    # full_fuzzer_input_path = "%s/%s" % ( \
            # config.exp_data_path, \
            # config.fuzzer_input_dir)

    # # Check if seed(s) already exist, if so ask for permission to do nothing
    # if os.listdir(full_fuzzer_input_path):
        # ovw = input(color_str_yellow( \
                # 'WARNING: input seed(s) exist. Update them? [yN]'))
        # if ovw in {'yes', 'y', 'Y', 'YES', 'Yes'}:
            # # Remove old seeds
            # for seed_filename in os.listdir(full_fuzzer_input_path):
                # os.remove(os.path.join(full_fuzzer_input_path, seed_filename))
        # else:
            # print(color_str_green("CONTINUING WITH EXISTING SEEDS -- Done!"))
            # return

    # # Check if seeds directory exists
    # if os.path.isdir(config.seeds_dir) and os.listdir(config.seeds_dir):
        # # Copy over new seeds
        # for seed_filename in os.listdir(config.seeds_dir):
            # full_seed_path = os.path.join(config.seeds_dir, seed_filename)
            # shutil.copy(full_seed_path, full_fuzzer_input_path)
        # print(color_str_green("SEED COPYING SUCCESSFUL -- Done!"))
    # else:
        # # No seeds to copy
        # error_str = "ERROR: no seeds to copy. Terminating experiment!"
        # print(color_str_red(error_str))
        # sys.exit(1)

# # Fuzz the software model of the core
# def fuzz_core(config):
    # print(LINE_SEP)
    # print("Fuzzing SW model of %s ..." % config.circuit)
    # print(LINE_SEP)

    # # Check if fuzzer identical fuzzer data already exists
    # full_fuzzer_output_path = "%s/%s/%s_*" % ( \
            # config.exp_data_path, \
            # config.fuzzer_output_dir, \
            # config.fuzzer_instance_basename)
    # if glob.glob(full_fuzzer_output_path):
        # ovw = input(color_str_yellow( \
                # 'WARNING: experiment data exists. Overwrite? [Yn]'))
        # if ovw in {'yes', 'y', 'Y', 'YES', 'Yes', ''}:
            # for fuzzer_data_dir in glob.glob(full_fuzzer_output_path):
                # shutil.rmtree(fuzzer_data_dir)
        # else:
            # abort_str = "ABORT: re-run with different configurations."
            # print(color_str_red(abort_str))
            # sys.exit(-1)

    # # Launch fuzzer
    # command = [\
        # "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        # "--name", "%s_%s_%s_fuzz" % ( \
            # config.circuit, \
            # config.experiment_name, \
            # config.fuzzer_instance_basename), \
        # "-e", "CORE=%s" % config.circuit, \
        # "-e", "FUZZER=%s" % config.fuzzer, \
        # "-e", "DEBUG=%d" % config.debug, \
        # "-e", "NUM_INSTANCES=%d" % config.num_instances, \
        # "-e", "FUZZER_INSTANCE_BASENAME=%s" % config.fuzzer_instance_basename, \
        # "-e", "FUZZING_DURATION_MINS=%s" % \
            # xstr(config.fuzzing_duration_mins), \
        # "-e", "CHECKPOINT_INTERVAL_MINS=%s" % \
            # xstr(config.checkpoint_interval_mins), \
        # "-e", "TIME_TO_EXPLOITATION_MINS=%s" % \
            # config.time_to_exploitation_mins, \
        # "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        # "-e", "FUZZER_INPUT_DIR=%s" % config.fuzzer_input_dir, \
        # "-e", "FUZZER_OUTPUT_DIR=%s" % config.fuzzer_output_dir, \
        # "-v", "%s/scripts:/scripts" % config.root_path, \
        # "-v", "%s/circuits:/src/circuits" % config.root_path, \
        # "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        # "-t", "hw-fuzzing/base-%s%s" % (config.fuzzer, USE_FORKED_FUZZER), \
        # "bash", "/scripts/gen_seeds_and_fuzz.sh" \
    # ]
    # try:
        # subprocess.check_call(command)
    # except subprocess.CalledProcessError:
        # error_str = "ERROR: fuzzing FAILED. Terminating experiment!"
        # print(color_str_red(error_str))
        # sys.exit(1)

# # Re-verilate/compile core for simulation and (VCD) tracing
# def simulate_and_trace(config):
    # print(LINE_SEP)
    # print("Generating VCD traces from fuzzer generated inputs ...")
    # print(LINE_SEP)
    # command = [\
        # "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        # "--name", "%s_%s_%s_vcd" % ( \
            # config.circuit, \
            # config.experiment_name, \
            # config.fuzzer_instance_basename), \
        # "-e", "CORE=%s" % config.circuit, \
        # "-e", "TB=%s" % config.testbench, \
        # "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        # "-e", "FUZZER_OUTPUT_DIR=%s" % config.fuzzer_output_dir, \
        # "-e", "NUM_INSTANCES=%d" % config.num_instances, \
        # "-e", "FUZZER_INSTANCE_BASENAME=%s" % config.fuzzer_instance_basename, \
        # "-v", "%s/scripts:/scripts" % config.root_path, \
        # "-v", "%s/circuits:/src/circuits" % config.root_path, \
        # "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        # "-t", "hw-fuzzing/base-%s%s" % (config.fuzzer, USE_FORKED_FUZZER), \
        # "bash", "/scripts/compile_and_sim_dut_wtracing.sh" \
    # ]
    # try:
        # subprocess.check_call(command)
    # except subprocess.CalledProcessError:
        # error_str = "ERROR: VCD tracing FAILED. Terminating experiment!"
        # print(color_str_red(error_str))
        # sys.exit(1)

# # Extract data from VCD traces for plotting
# def extract_data_for_plotting(config):
    # print(LINE_SEP)
    # print("Extracting VCD data to analyze ...")
    # sys.path.append(config.root_path + "/scripts/data_extraction")
    # data_extraction_module = importlib.import_module(\
            # config.data_extraction_script)
    # for instance_num in range(1, config.num_instances + 1):
        # fuzzer_data_path = "%s/%s/%s_%d/vcd" % \
                # (config.exp_data_path, \
                # config.fuzzer_output_dir, \
                # config.fuzzer_instance_basename, \
                # instance_num)
    # data_extraction_module.main([fuzzer_data_path])
    # print(color_str_green("DATA EXTRACTION SUCCESSFUL -- Done!"))

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

# Use forked fuzzer source code
USE_FORKED_FUZZER=""
# USE_FORKED_FUZZER="-fork"

# Handler to gracefully exit on ctrl+c
def sigint_handler(sig, frame):
    print(color_str_red('\nTERMINATING EXPERIMENT!'))
    sys.exit(0)

# Convert to empty string if None
def xstr(s):
    if s is None:
        return ''
    return str(s)

# Verilate and compile target core for fuzzing
def compile_core(config):
    print(LINE_SEP)
    print("Verilating/Compiling %s for fuzzing ..." % config.core)
    print(LINE_SEP)
    command = [\
        "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s_%s_%s_compile" % ( \
            config.core, \
            config.experiment_name, \
            config.fuzzer_instance_basename), \
        "-e", "CORE=%s" % config.core, \
        "-e", "TB=%s" % config.testbench, \
        "-e", "FUZZER=%s" % config.fuzzer, \
        "-e", "DEBUG=%d" % config.debug, \
        "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        "-v", "%s/scripts:/scripts" % config.root_path, \
        "-v", "%s/circuits:/src/circuits" % config.root_path, \
        "-v", "%s/third_party:/src/third_party" % config.root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-%s%s" % (config.fuzzer, USE_FORKED_FUZZER), \
        "bash", "/scripts/compile_dut_for_fuzzing.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        error_str = "ERROR: build FAILED. Terminating experiment!"
        print(color_str_red(error_str))
        sys.exit(1)

# Generate fuzzer input seeds
def copy_seeds(config):
    print(LINE_SEP)
    print("Copying seeds for fuzzer ...")

    # Set fuzzer seeds input path
    full_fuzzer_input_path = "%s/%s" % ( \
            config.exp_data_path, \
            config.fuzzer_input_dir)

    # Check if seed(s) already exist, if so ask for permission to do nothing
    if os.listdir(full_fuzzer_input_path):
        ovw = input(color_str_yellow( \
                'WARNING: input seed(s) exist. Update them? [yN]'))
        if ovw in {'yes', 'y', 'Y', 'YES', 'Yes'}:
            # Remove old seeds
            for seed_filename in os.listdir(full_fuzzer_input_path):
                os.remove(os.path.join(full_fuzzer_input_path, seed_filename))
        else:
            print(color_str_green("CONTINUING WITH EXISTING SEEDS -- Done!"))
            return

    # Check if seeds directory exists
    if os.path.isdir(config.seeds_dir) and os.listdir(config.seeds_dir):
        # Copy over new seeds
        for seed_filename in os.listdir(config.seeds_dir):
            full_seed_path = os.path.join(config.seeds_dir, seed_filename)
            shutil.copy(full_seed_path, full_fuzzer_input_path)
        print(color_str_green("SEED COPYING SUCCESSFUL -- Done!"))
    else:
        # No seeds to copy
        error_str = "ERROR: no seeds to copy. Terminating experiment!"
        print(color_str_red(error_str))
        sys.exit(1)


# Fuzz the software model of the core
def fuzz_core(config):
    print(LINE_SEP)
    print("Fuzzing SW model of %s ..." % config.core)
    print(LINE_SEP)

    # Check if fuzzer identical fuzzer data already exists
    full_fuzzer_output_path = "%s/%s/%s_*" % ( \
            config.exp_data_path, \
            config.fuzzer_output_dir, \
            config.fuzzer_instance_basename)
    if glob.glob(full_fuzzer_output_path):
        ovw = input(color_str_yellow( \
                'WARNING: experiment data exists. Overwrite? [Yn]'))
        if ovw in {'yes', 'y', 'Y', 'YES', 'Yes', ''}:
            for fuzzer_data_dir in glob.glob(full_fuzzer_output_path):
                shutil.rmtree(fuzzer_data_dir)
        else:
            abort_str = "ABORT: re-run with different configurations."
            print(color_str_red(abort_str))
            sys.exit(-1)

    # Launch fuzzer
    command = [\
        "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s_%s_%s_fuzz" % ( \
            config.core, \
            config.experiment_name, \
            config.fuzzer_instance_basename), \
        "-e", "CORE=%s" % config.core, \
        "-e", "FUZZER=%s" % config.fuzzer, \
        "-e", "DEBUG=%d" % config.debug, \
        "-e", "NUM_INSTANCES=%d" % config.num_instances, \
        "-e", "FUZZER_INSTANCE_BASENAME=%s" % config.fuzzer_instance_basename, \
        "-e", "FUZZING_DURATION_MINS=%s" % \
            xstr(config.fuzzing_duration_mins), \
        "-e", "CHECKPOINT_INTERVAL_MINS=%s" % \
            xstr(config.checkpoint_interval_mins), \
        "-e", "TIME_TO_EXPLOITATION_MINS=%s" % \
            config.time_to_exploitation_mins, \
        "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        "-e", "FUZZER_INPUT_DIR=%s" % config.fuzzer_input_dir, \
        "-e", "FUZZER_OUTPUT_DIR=%s" % config.fuzzer_output_dir, \
        "-v", "%s/scripts:/scripts" % config.root_path, \
        "-v", "%s/circuits:/src/circuits" % config.root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-%s%s" % (config.fuzzer, USE_FORKED_FUZZER), \
        "bash", "/scripts/gen_seeds_and_fuzz.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        error_str = "ERROR: fuzzing FAILED. Terminating experiment!"
        print(color_str_red(error_str))
        sys.exit(1)

# Re-verilate/compile core for simulation and (VCD) tracing
def simulate_and_trace(config):
    print(LINE_SEP)
    print("Generating VCD traces from fuzzer generated inputs ...")
    print(LINE_SEP)
    command = [\
        "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s_%s_%s_vcd" % ( \
            config.core, \
            config.experiment_name, \
            config.fuzzer_instance_basename), \
        "-e", "CORE=%s" % config.core, \
        "-e", "TB=%s" % config.testbench, \
        "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        "-e", "FUZZER_OUTPUT_DIR=%s" % config.fuzzer_output_dir, \
        "-e", "NUM_INSTANCES=%d" % config.num_instances, \
        "-e", "FUZZER_INSTANCE_BASENAME=%s" % config.fuzzer_instance_basename, \
        "-v", "%s/scripts:/scripts" % config.root_path, \
        "-v", "%s/circuits:/src/circuits" % config.root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-%s%s" % (config.fuzzer, USE_FORKED_FUZZER), \
        "bash", "/scripts/compile_and_sim_dut_wtracing.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        error_str = "ERROR: VCD tracing FAILED. Terminating experiment!"
        print(color_str_red(error_str))
        sys.exit(1)

# Extract data from VCD traces for plotting
def extract_data_for_plotting(config):
    print(LINE_SEP)
    print("Extracting VCD data to analyze ...")
    sys.path.append(config.root_path + "/scripts/data_extraction")
    data_extraction_module = importlib.import_module(\
            config.data_extraction_script)
    for instance_num in range(1, config.num_instances + 1):
        fuzzer_data_path = "%s/%s/%s_%d/vcd" % \
                (config.exp_data_path, \
                config.fuzzer_output_dir, \
                config.fuzzer_instance_basename, \
                instance_num)
    data_extraction_module.main([fuzzer_data_path])
    print(color_str_green("DATA EXTRACTION SUCCESSFUL -- Done!"))

# Main
def main(args):

    # Parse cmd args
    if len(args) != NUM_ARGS:
        print("Usage: [python3] ./run_experiment.py <config filename>")
        sys.exit(1)

    # Load experiment configurations
    config = Config(args[0])
    config.print_configurations()

    # Create experiment directories
    config.create_experiment_dirs()

    # Verilate and compile target core for fuzzing
    compile_core(config)

    # Copy input seeds to experiment directory
    copy_seeds(config)

    # Fuzz target core
    fuzz_core(config)

    # Generate VCD traces
    # simulate_and_trace(config)

    # Extract VCD data for plotting
    # extract_data_for_plotting(config)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main(sys.argv[1:])

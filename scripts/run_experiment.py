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
import importlib
import os
import subprocess
import sys

# Custom modules
from config import Config

# Number of input arguments
NUM_ARGS = 1

# Other defines
# LINE_SEP = "-------------------------------------------------------------------"
LINE_SEP = "==================================================================="

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
        "--name", "%s-compile" % config.core, \
        "-e", "CORE=%s" % config.core, \
        "-e", "FUZZER=%s" % config.fuzzer, \
        "-e", "DEBUG=%d" % config.debug, \
        "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        "-v", "%s/scripts:/scripts" % config.root_path, \
        "-v", "%s/circuits:/src/circuits" % config.root_path, \
        "-v", "%s/third_party:/src/third_party" % config.root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-%s" % config.fuzzer, \
        "bash", "/scripts/compile_dut_for_fuzzing.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print("ERROR: compilation for fuzzing FAILED. Terminating experiment!")
        sys.exit(1)

# Generate fuzzer input seeds
def generate_seeds(config):
    print(LINE_SEP)
    print("Generating seeds for fuzzer ...")
    sys.path.append(config.root_path + "/scripts")
    seed_gen_module = importlib.import_module("gen_afl_seeds")
    seed_file_basename = config.exp_data_path + \
            "/" + config.fuzzer_input_dir + "/seed"
    seed_gen_module.gen_afl_seeds(\
            seed_file_basename, \
            config.num_seeds, \
            config.num_tests_per_seed)
    print("Done!")

# Fuzz the software model of the core
def fuzz_core(config):
    print(LINE_SEP)
    print("Fuzzing SW model of %s ..." % config.core)
    print(LINE_SEP)
    command = [\
        "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-fuzz" % config.core, \
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
        "-t", "hw-fuzzing/base-%s" % config.fuzzer, \
        "bash", "/scripts/gen_seeds_and_fuzz.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print("ERROR: fuzzing FAILED. Terminating experiment!")
        sys.exit(1)

# Re-verilate/compile core for simulation and (VCD) tracing
def simulate_and_trace(config):
    print(LINE_SEP)
    print("Generating VCD traces from fuzzer generated inputs ...")
    print(LINE_SEP)
    command = [\
        "docker", "run", "-it", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-vcd" % config.core, \
        "-e", "CORE=%s" % config.core, \
        "-e", "EXP_DATA_PATH=%s" % config.exp_data_path, \
        "-e", "FUZZER_OUTPUT_DIR=%s" % config.fuzzer_output_dir, \
        "-e", "NUM_INSTANCES=%d" % config.num_instances, \
        "-e", "FUZZER_INSTANCE_BASENAME=%s" % config.fuzzer_instance_basename, \
        "-v", "%s/scripts:/scripts" % config.root_path, \
        "-v", "%s/circuits:/src/circuits" % config.root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-%s" % config.fuzzer, \
        "bash", "/scripts/compile_and_sim_dut_wtracing.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print("ERROR: VCD tracing FAILED. Terminating experiment!")
        sys.exit(1)

# Extract data from VCD traces for plotting
def extract_data_for_plotting(config):
    print(LINE_SEP)
    print("Extracting VCD data to analyze ...")
    print(LINE_SEP)
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
    print(LINE_SEP)
    print("Done!")

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

    # Generate inputs seeds
    generate_seeds(config)

    # Fuzz target core
    fuzz_core(config)

    # Generate VCD traces
    simulate_and_trace(config)

    # Extract VCD data for plotting
    extract_data_for_plotting(config)

if __name__ == "__main__":
    main(sys.argv[1:])

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

import errno
import importlib
import json
import os
import shutil
import subprocess
import sys

# Number of input arguments
NUM_ARGS = 1

# Configurations dictionary keys
KEY_EXPERIMENT_NUMBER = "experiment_number"
KEY_EXPERIMENT_NAME = "experiment_name"
KEY_CORE = "core"
KEY_DEBUG = "debug"
KEY_BB_TARGET_GENERATION_SCRIPT = "bb_target_generation_script"
KEY_NUM_SEEDS = "num_seeds"
KEY_NUM_TESTS_PER_SEED = "num_tests_per_seed"
KEY_FUZZING_DURATION_MINS = "fuzzing_duration_mins"
KEY_DATA_EXTRACTION_SCRIPT = "data_extraction_script"
KEY_TAG = "tag"

# Docker infrastructure scripts
INFRA_PATH = "infra/scripts"

# Fuzzer
FUZZER = "aflgo"

# Root data directory name
ROOT_DATA_PATH = "data"

def main(args):

    # Parse cmd args
    if len(args) != NUM_ARGS:
        print("Usage: [python3] ./run_experiment.py <config filename>")
        sys.exit(1)
    config_filename = args[0]

    # Load experiment configurations file
    print("-------------------------------------------------------------------")
    print("Loading experiment configurations ...")
    print("-------------------------------------------------------------------")
    with open(config_filename, 'r') as json_file:
        config = json.load(json_file)

    # Parse experiment configurations
    experiment_number = config[KEY_EXPERIMENT_NUMBER]
    experiment_name = config[KEY_EXPERIMENT_NAME]
    core = config[KEY_CORE]
    debug = int(config[KEY_DEBUG])
    bb_target_generation_script = config[KEY_BB_TARGET_GENERATION_SCRIPT]
    num_seeds = int(config[KEY_NUM_SEEDS])
    num_tests_per_seed = int(config[KEY_NUM_TESTS_PER_SEED])
    fuzzing_duration_mins = float(config[KEY_FUZZING_DURATION_MINS])
    data_extraction_script = config[KEY_DATA_EXTRACTION_SCRIPT]
    tag = config[KEY_TAG]

    # Print experiment configurations
    print("Experiment Number:", experiment_number)
    print("Experiment Name:", experiment_name)
    print("Core:", core)
    print("Debug:", debug)
    print("BB Target Generation Script:", bb_target_generation_script)
    print("Number of Fuzzing Seeds:", num_seeds)
    print("Number of Test per Seed:", num_tests_per_seed)
    print("Fuzzing Duration (min.):", fuzzing_duration_mins)
    print("Data Extraction Script:", data_extraction_script)
    print("Tag:", tag)

    # Create root data directory if it does not exist
    print("-------------------------------------------------------------------")
    print("Creating directories for fuzzing data ...")
    print("-------------------------------------------------------------------")
    root_path = os.getenv('HW_FUZZING')
    core_data_path = ROOT_DATA_PATH
    exp_data_path = "%s/exp%s_%s" % \
            (core_data_path, str(experiment_number).zfill(3), experiment_name)

    # Create core data path
    try:
        os.makedirs(core_data_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Create experiment data path
    try:
        os.makedirs(exp_data_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    # Construct output directory name
    fuzz_data_path = "%s/%s_%dseeds_%dtests_%smins%s" % ( \
            exp_data_path, \
            FUZZER, \
            num_seeds, \
            num_tests_per_seed, \
            str(fuzzing_duration_mins).replace(".", "_"), \
            tag)

    # Check if fuzz data directory already exists
    if os.path.exists(fuzz_data_path):
        ovw = input('WARNING: fuzzing data already exists. Overwrite? [Yn]')
        if ovw in {'yes', 'y', 'Y', 'YES', 'Yes', ''}:
            shutil.rmtree(fuzz_data_path)
        else:
            print("ABORT: re-run with different experiment parameters.")
            sys.exit(-1)

    # Print output directories
    print("Output Data Paths:")
    print("Root Path:", root_path)
    print("Core Data Path:", core_data_path)
    print("Experiment Data Path:", exp_data_path)
    print("Fuzzing Data Path:", fuzz_data_path)
    print("Done!")

    # Compile target core for fuzzing
    print("-------------------------------------------------------------------")
    print("Verilating/Compiling %s for fuzzing ..." % core)
    print("-------------------------------------------------------------------")
    command = [\
        "docker", "run", "-i", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-compile" % core, \
        "-e", "CORE=%s" % core, \
        "-e", "DEBUG=%d" % debug, \
        "-v", "%s/scripts:/scripts" % root_path, \
        "-v", "%s/circuits:/src/circuits" % root_path, \
        "-v", "%s/third_party:/src/third_party" % root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-aflgo", \
        "bash", "/scripts/compile_dut_for_fuzzing.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print("ERROR: compilation for fuzzing FAILED. Terminating experiment!")
        sys.exit(1)
    print("Done!")

    # Fuzz target core
    print("-------------------------------------------------------------------")
    print("Fuzzing SW model of %s ..." % core)
    print("-------------------------------------------------------------------")
    command = [\
        "docker", "run", "-i", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-fuzz" % core, \
        "-e", "CORE=%s" % core, \
        "-e", "NUM_SEEDS=%d" % num_seeds, \
        "-e", "NUM_TESTS_PER_SEED=%d" % num_tests_per_seed, \
        "-e", "FUZZING_DURATION_MINS=%f" % fuzzing_duration_mins, \
        "-e", "BK_DIR=%s" % fuzz_data_path, \
        "-v", "%s/scripts:/scripts" % root_path, \
        "-v", "%s/circuits:/src/circuits" % root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-aflgo", \
        "bash", "/scripts/gen_seeds_and_fuzz.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print("ERROR: fuzzing FAILED. Terminating experiment!")
        sys.exit(1)
    print("Done!")

    # Generate VCD traces
    print("-------------------------------------------------------------------")
    print("Generating VCD traces from fuzzer generated inputs ...")
    print("-------------------------------------------------------------------")
    command = [\
        "docker", "run", "-i", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-vcd" % core, \
        "-e", "CORE=%s" % core, \
        "-e", "FUZZ_RESULTS_DIR=%s" % fuzz_data_path, \
        "-v", "%s/scripts:/scripts" % root_path, \
        "-v", "%s/circuits:/src/circuits" % root_path, \
        "-u", "%d:%d" % (os.getuid(), os.getgid()), \
        "-t", "hw-fuzzing/base-aflgo", \
        "bash", "/scripts/compile_and_sim_dut_wtracing.sh" \
    ]
    try:
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        print("ERROR: VCD tracing FAILED. Terminating experiment!")
        sys.exit(1)
    print("Done!")

    # Extract data
    print("-------------------------------------------------------------------")
    print("Extracting data to analyze ...")
    print("-------------------------------------------------------------------")
    sys.path.append(root_path + "/scripts/data_extraction")
    data_extraction_module = importlib.import_module(data_extraction_script)
    data_extraction_module.main([fuzz_data_path + "/vcd"])
    print("Done!")

if __name__ == "__main__":
    main(sys.argv[1:])

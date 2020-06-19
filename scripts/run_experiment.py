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

import importlib
import json
import os
import subprocess
import sys

# Number of input arguments
NUM_ARGS = 1

# Configurations dictionary keys
KEY_EXPERIMENT_NUMBER = "experiment_number"
KEY_EXPERIMENT_NAME = "experiment_name"
KEY_ROOT_PATH = "root_path"
KEY_CORE = "core"
KEY_DEBUG = "debug"
KEY_BB_TARGET_GENERATION_SCRIPT = "bb_target_generation_script"
KEY_NUM_SEEDS = "num_seeds"
KEY_NUM_TESTS_PER_SEED = "num_tests_per_seed"
KEY_DATA_EXTRACTION_SCRIPT = "data_extraction_script"

# Docker infrastructure scripts
INFRA_PATH = "infra/scripts"

def run_subprocess_and_wait(cmd_list, cwd, env):
    cmd_list = ["./compile_core.sh"]
    print(env)
    print(cwd)
    print(cmd_list)
    compile_proc = subprocess.Popen(cmd_list, \
            stdin=subprocess.PIPE, \
            stdout=subprocess.PIPE, \
            stderr=subprocess.PIPE, \
            cwd=cwd, \
            env=env)
    output, errors = compile_proc.communicate()
    compile_proc.wait()
    print("Output:", output)
    print("Errors:", errors)

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
    root_path = config[KEY_ROOT_PATH]
    core = config[KEY_CORE]
    debug = config[KEY_DEBUG]
    bb_target_generation_script = config[KEY_BB_TARGET_GENERATION_SCRIPT]
    num_seeds = config[KEY_NUM_SEEDS]
    num_tests_per_seed = config[KEY_NUM_TESTS_PER_SEED]
    data_extraction_script = config[KEY_DATA_EXTRACTION_SCRIPT]

    # Print experiment configurations
    print("-------------------------------------------------------------------")
    print("Experiment Configurations:")
    print("-------------------------------------------------------------------")
    print("Experiment Number:", experiment_number)
    print("Experiment Name:", experiment_name)
    print("Root Path:", root_path)
    print("Core:", core)
    print("Debug:", debug)
    print("BB Target Generation Script:", bb_target_generation_script)
    print("Number of Fuzzing Seeds:", num_seeds)
    print("Number of Test per Seed:", num_tests_per_seed)
    print("Data Extraction Script:", data_extraction_script)

    # Compile target core for fuzzing
    print("-------------------------------------------------------------------")
    print("Verilating/Compiling %s for fuzzing ..." % core)
    print("-------------------------------------------------------------------")
    command = [\
        "docker", "run", "-i", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-compile" % core, \
        "-e", "CORE=%s" % core, \
        "-e", "DEBUG=%d" % debug, \
        "-v", "%s/scripts:/scripts" % os.getenv('HW_FUZZING'), \
        "-v", "%s/circuits:/src/circuits" % os.getenv('HW_FUZZING'), \
        "-v", "%s/third_party:/src/third_party" % os.getenv('HW_FUZZING'), \
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
    exp_data_dir = "exp%s_%s_data" % \
            (str(experiment_number).zfill(3), experiment_name)
    command = [\
        "docker", "run", "-i", "--rm", "--cap-add", "SYS_PTRACE", \
        "--name", "%s-fuzz" % core, \
        "-e", "CORE=%s" % core, \
        "-e", "NUM_SEEDS=%d" % num_seeds, \
        "-e", "NUM_TESTS_PER_SEED=%d" % num_tests_per_seed, \
        "-e", "BK_DIR=%s" % exp_data_dir, \
        "-v", "%s/scripts:/scripts" % os.getenv('HW_FUZZING'), \
        "-v", "%s/circuits:/src/circuits" % os.getenv('HW_FUZZING'), \
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
        "-e", "FUZZ_RESULTS_DIR=%s" % exp_data_dir, \
        "-v", "%s/scripts:/scripts" % os.getenv('HW_FUZZING'), \
        "-v", "%s/circuits:/src/circuits" % os.getenv('HW_FUZZING'), \
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
    sys.path.append(os.getenv('HW_FUZZING') + "/scripts/data_extraction")
    data_extraction_module = importlib.import_module(data_extraction_script)
    data_extraction_module.main([exp_data_dir + "/vcd"])
    print("Done!")

if __name__ == "__main__":
    main(sys.argv[1:])

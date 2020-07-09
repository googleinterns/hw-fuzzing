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
import json
import os

# Configurations dictionary keys
KEY_EXPERIMENT_NUMBER           = "experiment_number"
KEY_EXPERIMENT_NAME             = "experiment_name"
KEY_CORE                        = "core"
KEY_FUZZER                      = "fuzzer"
KEY_DEBUG                       = "debug"
KEY_NUM_SEEDS                   = "num_seeds"
KEY_NUM_TESTS_PER_SEED          = "num_tests_per_seed"
KEY_NUM_INSTANCES               = "num_instances"
KEY_FUZZER_INPUT_DIR            = "fuzzer_input_dir"
KEY_FUZZER_OUTPUT_DIR           = "fuzzer_output_dir"
KEY_FUZZING_DURATION_MINS       = "fuzzing_duration_mins"
KEY_CHECKPOINT_INTERVAL_MINS    = "checkpoint_interval_mins"
KEY_TIME_TO_EXPLOITATION_MINS   = "time_to_exploitation_mins"
KEY_DATA_EXTRACTION_SCRIPT      = "data_extraction_script"
KEY_TAG                         = "tag"

# Root data directory name
ROOT_DATA_PATH = "data"

# Other defines
LINE_SEP = "==================================================================="

# Color string RED for printing to terminal
def color_str_red(s):
    return "\033[1m\033[91m{}\033[00m".format(s)

# Color string GREEN for printing to terminal
def color_str_green(s):
    return "\033[1m\033[92m{}\033[00m".format(s)

# Color string YELLOW for printing to terminal
def color_str_yellow(s):
    return "\033[93m{}\033[00m".format(s)

class Config():
    def __init__(self, config_filename):
        # Config filename
        self.config_filename = config_filename

        # Configurations
        self.experiment_number = None
        self.experiment_name = None
        self.core = None
        self.fuzzer = None
        self.debug = None
        self.num_seeds = None
        self.num_tests_per_seed = None
        self.num_instances = None
        self.fuzzer_input_dir = None
        self.fuzzer_output_dir = None
        self.fuzzing_duration_mins = None
        self.checkpoint_interval_mins = None
        self.time_to_exploitation_mins = None
        self.data_extraction_script = None
        self.tag = None
        self.exp_data_path = None

        # Set root path
        self.root_path = os.getenv('HW_FUZZING')

        # Load configurations
        self.load_configurations()

        # Set experiment directory names
        self.set_experiment_dir_name()

        # Set fuzzer instance basename
        self.set_fuzzer_instance_basename()

    # Load experiment configurations
    def load_configurations(self):
        print(LINE_SEP)
        print("Loading experiment configurations ...")
        with open(self.config_filename, 'r') as json_file:
            cdict = json.load(json_file)
            self.experiment_number = cdict[KEY_EXPERIMENT_NUMBER]
            self.experiment_name = cdict[KEY_EXPERIMENT_NAME]
            self.core = cdict[KEY_CORE]
            self.fuzzer = cdict[KEY_FUZZER]
            self.debug = int(cdict[KEY_DEBUG])
            self.num_seeds = int(cdict[KEY_NUM_SEEDS])
            self.num_tests_per_seed = int(cdict[KEY_NUM_TESTS_PER_SEED])
            self.num_instances = int(cdict[KEY_NUM_INSTANCES])
            self.fuzzer_input_dir = cdict[KEY_FUZZER_INPUT_DIR]
            self.fuzzer_output_dir = cdict[KEY_FUZZER_OUTPUT_DIR]
            self.fuzzing_duration_mins = cdict[KEY_FUZZING_DURATION_MINS]
            self.checkpoint_interval_mins = cdict[KEY_CHECKPOINT_INTERVAL_MINS]
            self.time_to_exploitation_mins = \
                    cdict[KEY_TIME_TO_EXPLOITATION_MINS]
            self.data_extraction_script = cdict[KEY_DATA_EXTRACTION_SCRIPT]
            self.tag = cdict[KEY_TAG]

    # Set experiment directory name
    def set_experiment_dir_name(self):
        self.exp_data_path = "%s/exp%s_%s" % \
                (ROOT_DATA_PATH, \
                str(self.experiment_number).zfill(3), \
                self.experiment_name)

    # Set fuzzer instance basename
    def set_fuzzer_instance_basename(self):
        self.fuzzer_instance_basename = "%s" % (self.fuzzer)
        if self.fuzzing_duration_mins:
            self.fuzzer_instance_basename += ("_%smins" % \
                str(self.fuzzing_duration_mins).replace(".", "_"))
        if self.time_to_exploitation_mins:
            self.fuzzer_instance_basename += ("_%dttemins" % \
                self.time_to_exploitation_mins)
        if self.checkpoint_interval_mins:
            self.fuzzer_instance_basename += ("_%sminscp" % \
                str(self.checkpoint_interval_mins).replace(".", "_"))
        if self.tag:
            self.fuzzer_instance_basename += ("_%s" % self.tag)

    # Create directories for experiment data
    def create_experiment_dirs(self):
        print(LINE_SEP)
        print("Creating experiment directories ...")

        # Create core data path if it does not exist
        try:
            os.makedirs(ROOT_DATA_PATH)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Create experiment data path if it does not exist
        try:
            os.makedirs(self.exp_data_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Create fuzzer input directory if it does not exist
        fuzzer_input_path = "%s/%s" % \
                (self.exp_data_path, self.fuzzer_input_dir)
        try:
            os.makedirs(fuzzer_input_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Create fuzzer output directory if it does not exist
        fuzzer_output_path = "%s/%s" % \
                (self.exp_data_path, self.fuzzer_output_dir)
        try:
            os.makedirs(fuzzer_output_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        print(color_str_green("DIRECTORY CREATION SUCCESSFUL -- Done!"))

    # Print experiment configurations
    def print_configurations(self):
        print(color_str_yellow("Configurations:"))
        print(color_str_yellow("Experiment Number:          "), self.experiment_number)
        print(color_str_yellow("Experiment Name:            "), self.experiment_name)
        print(color_str_yellow("Core:                       "), self.core)
        print(color_str_yellow("Fuzzer:                     "), self.fuzzer)
        print(color_str_yellow("Debug:                      "), self.debug)
        print(color_str_yellow("Number of Fuzzing Seeds:    "), self.num_seeds)
        print(color_str_yellow("Number of Test per Seed:    "), self.num_tests_per_seed)
        print(color_str_yellow("Number of Instances:        "), self.num_instances)
        print(color_str_yellow("Fuzzing Duration (min):     "), self.fuzzing_duration_mins)
        print(color_str_yellow("Checkpoint Interval (min):  "), self.checkpoint_interval_mins)
        print(color_str_yellow("Time to Exploitation (min): "), self.time_to_exploitation_mins)
        print(color_str_yellow("Data Extraction Script:     "), self.data_extraction_script)
        print(color_str_yellow("Tag:                        "), self.tag)
        print(color_str_yellow("Experiment Data Path:       "), self.exp_data_path)
        print(color_str_yellow("Fuzzer Input Directory:     "), self.fuzzer_input_dir)
        print(color_str_yellow("Fuzzer Output Directory:    "), self.fuzzer_output_dir)
        print(color_str_yellow("Fuzzer Instance Basename:   "), self.fuzzer_instance_basename)

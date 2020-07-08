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
import shutil
import sys

# Configurations dictionary keys
KEY_EXPERIMENT_NUMBER           = "experiment_number"
KEY_EXPERIMENT_NAME             = "experiment_name"
KEY_CORE                        = "core"
KEY_FUZZER                      = "fuzzer"
KEY_DEBUG                       = "debug"
KEY_BB_TARGET_GENERATION_SCRIPT = "bb_target_generation_script"
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
        self.bb_target_generation_script = None
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
            self.bb_target_generation_script = \
                    cdict[KEY_BB_TARGET_GENERATION_SCRIPT]
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
        self.fuzzer_instance_basename = "%s_%dttemins" % ( \
                self.fuzzer, \
                self.time_to_exploitation_mins)
        if self.fuzzing_duration_mins:
            self.fuzzer_instance_basename += ("_%smins" % \
                str(self.fuzzing_duration_mins).replace(".", "_"))
        if self.checkpoint_interval_mins:
            self.fuzzer_instance_basename += ("_%sminscp" % \
                str(self.checkpoint_interval_mins).replace(".", "_"))
        if self.tag:
            self.fuzzer_instance_basename += ("_%s" % self.tag)

    # Create directories for experiment data
    def create_experiment_dirs(self):
        print(LINE_SEP)
        print("Creating experiment directories ...")

        # Check if experiment data directory already exists
        if os.path.exists(self.exp_data_path):
            ovw = input('WARNING: experiment data exists. Overwrite? [Yn]')
            if ovw in {'yes', 'y', 'Y', 'YES', 'Yes', ''}:
                shutil.rmtree(self.exp_data_path)
            else:
                print("ABORT: re-run with different experiment configurations.")
                sys.exit(-1)

        # Create core data path
        try:
            os.makedirs(ROOT_DATA_PATH)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Create experiment data path
        try:
            os.makedirs(self.exp_data_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Create fuzzer input directory (for seeds)
        fuzzer_input_path = "%s/%s" % \
                (self.exp_data_path, self.fuzzer_input_dir)
        try:
            os.makedirs(fuzzer_input_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        # Create fuzzer output directory
        fuzzer_output_path = "%s/%s" % \
                (self.exp_data_path, self.fuzzer_output_dir)
        try:
            os.makedirs(fuzzer_output_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        print("Done!")

    # Print experiment configurations
    def print_configurations(self):
        print("Configurations:")
        print("Experiment Number:           ", self.experiment_number)
        print("Experiment Name:             ", self.experiment_name)
        print("Core:                        ", self.core)
        print("Fuzzer:                      ", self.fuzzer)
        print("Debug:                       ", self.debug)
        print("BB Target Generation Script: ", self.bb_target_generation_script)
        print("Number of Fuzzing Seeds:     ", self.num_seeds)
        print("Number of Test per Seed:     ", self.num_tests_per_seed)
        print("Number of Instances:         ", self.num_instances)
        print("Fuzzing Duration (min):      ", self.fuzzing_duration_mins)
        print("Checkpoint Interval (min):   ", self.checkpoint_interval_mins)
        print("Time to Exploitation (min):  ", self.time_to_exploitation_mins)
        print("Data Extraction Script:      ", self.data_extraction_script)
        print("Tag:                         ", self.tag)
        print("Experiment Data Path:        ", self.exp_data_path)
        print("Fuzzer Input Directory:      ", self.fuzzer_input_dir)
        print("Fuzzer Output Directory:     ", self.fuzzer_output_dir)
        print("Fuzzer Instance Basename:    ", self.fuzzer_instance_basename)

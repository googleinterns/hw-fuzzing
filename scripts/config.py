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
# import json
import hjson
import os
import prettytable
import sys

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
        # Experiment configs
        self.experiment_name = None
        self.circuit = None
        self.testbench = None
        self.hdl_gen_params = None
        self.compile_params = None
        self.fuzzer = None
        self.fuzzer_params = None

        # Initialize experiment data paths
        self.root_path = os.getenv('HW_FUZZING')
        self.exp_data_path = None

        # Setup experiment
        self.load_configurations(config_filename)
        self.set_testbench_filename()
        self.set_experiment_dir_name()
        self.print_configs()
        self.validate_configs()

    # Load experiment configurations
    def load_configurations(self, config_filename):
        print(LINE_SEP)
        print("Loading experiment configurations ...")
        with open(config_filename, 'r') as hjson_file:
            # Load HJSON file
            cdict = hjson.load(hjson_file)
            # Parse config dict
            self.experiment_name = cdict["experiment_name"]
            self.circuit = cdict["circuit"]
            self.testbench = cdict["testbench"]
            self.run_on_gcp = cdict["run_on_gcp"]
            self.hdl_gen_params = cdict["hdl_gen_params"]
            self.compile_params = cdict["compile_params"]
            self.fuzzer = cdict["fuzzer"]
            self.fuzzer_params = cdict["fuzzer_params"]

    # TODO: make sure didn't make mistakes writing config file!
    def validate_configs(self):
        # print(color_str_red("ERROR: fuzzer instance basename too long."), \
                # color_str_red("Terminating experiment!"))
        # sys.exit(1)
        return True

    # Set testbench filename
    def set_testbench_filename(self):
        self.testbench = os.path.join("src", self.testbench)

    # Set experiment directory name
    def set_experiment_dir_name(self):
        self.exp_data_path = os.path.join(ROOT_DATA_PATH, self.experiment_name)

    def print_configs(self):
        # Create table for printing
        exp_config_table = prettytable.PrettyTable(header=False)
        exp_config_table.title = "Experiment Parameters"
        exp_config_table.field_names = ["Parameter", "Value"]

        # Add main experiment parameters
        exp_config_table.add_row(["Experiment Name:", self.experiment_name])
        exp_config_table.add_row(["Circuit:", self.circuit])
        exp_config_table.add_row(["Testbench:", self.testbench])
        exp_config_table.add_row(["Fuzzer:", self.fuzzer])
        exp_config_table.add_row(["Run on GCP:", self.run_on_gcp])
        exp_config_table.add_row(["Experiment Data Path:", self.exp_data_path])

        # Add other parameters
        sub_configs = [self.hdl_gen_params, \
                self.compile_params, \
                self.fuzzer_params]
        for config in sub_configs:
            for param, value in config.items():
                param = param.replace("_", " ").title() + ":"
                exp_config_table.add_row([param, value])

        # Print table
        exp_config_table.align = "l"
        print(color_str_yellow(exp_config_table.get_string()))

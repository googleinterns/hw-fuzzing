#!/usr/bin/python3.8
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
import os

# Installed dependencies
import hjson
import prettytable

# Macros
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
  """Loads and stores experiment configuration data."""

  def __init__(self, args):
    """Constructs experiment configuration object from an HJSON file."""
    self.args = args
    self.config_filename = args.config_filename

    # Load experiment configurations
    print(LINE_SEP)
    print("Loading experiment configurations ...")
    with open(self.config_filename, "r") as hjson_file:
      # Load HJSON file
      cdict = hjson.load(hjson_file)
      # Parse config dict
      self.experiment_name = cdict["experiment_name"]
      self.circuit = cdict["circuit"]
      self.tb_type = cdict["tb_type"]
      self.tb = cdict["tb"]
      self.fuzzer = cdict["fuzzer"]
      self.run_on_gcp = cdict["run_on_gcp"]
      self.gcp_params = cdict["gcp_params"]
      self.env_var_params = [cdict["verilator_params"]]
      self.env_var_params.append(cdict["hdl_gen_params"])
      self.env_var_params.append(cdict["fuzzer_params"])

    # Initialize experiment data paths
    self.root_path = os.getenv("HW_FUZZING")

    # Initialize docker image name:
    self.docker_image = "gcr.io/%s/%s-%s" % \
        (self.gcp_params["project"], self.fuzzer, self.circuit)

    # Validate and print configurations
    self.validate_configs()
    self.print_configs()

  # Load experiment configurations
  def load_configs_from_hjson_file(self, config_filename):
    """Loads experiment configurations from an HJSON file."""

  # TODO(ttrippel): make sure didn't make mistakes writing config file!
  def validate_configs(self):
    VALID_TB_TYPES = ["cpp", "cocotb"]
    VALID_FUZZERS = ["afl", "afl-term-on-crash", "none"]
    VALID_VLT_OPTS = ["-O0", "-O1", "-O2", "-O3", "-Os", "-Oz"]
    VALID_AFL_FUZZER_MODES = ["m", "s"]
    return

  def print_configs(self):
    """Creates a table detailing experiment configurations and prints."""
    exp_config_table = prettytable.PrettyTable(header=False)
    exp_config_table.title = "Experiment Parameters"
    exp_config_table.field_names = ["Parameter", "Value"]

    # Add main experiment parameters
    exp_config_table.add_row(["Experiment Name", self.experiment_name])
    exp_config_table.add_row(["Circuit", self.circuit])
    exp_config_table.add_row(["Testbench Type", self.tb_type])
    exp_config_table.add_row(["Testbench", self.tb])
    exp_config_table.add_row(["Fuzzer", self.fuzzer])
    exp_config_table.add_row(["Run on GCP", self.run_on_gcp])

    # Add other parameters
    for params in [self.gcp_params] + self.env_var_params:
      for param, value in params.items():
        param = param.replace("_", " ").title()
        exp_config_table.add_row([param, value])

    # Print table
    exp_config_table.align = "l"
    print(color_str_yellow(exp_config_table.get_string()))

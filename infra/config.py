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
"""This module parses an HJSON config file defining how/what toplevel to fuzz.

Description:
This module implements an HJSON configuration file parser to launch fuzzing
experiments on various toplevel designs contained in this repository. It is
designed to be invoked by the fuzz.py module in the root directory of this
repository. See the tests/ directory for example HJSON configuration files.
"""

import os

import hjson
import prettytable

from string_color import color_str_yellow as yellow

LINE_SEP = "==================================================================="


class Config():
  """Loads and stores experiment configuration data.

  Attributes:
    experiment_name: A name to give the fuzzing experiment output directory.
    toplevel: Name of the toplevel to fuzz (from hw/).
    tb_type: Type of testbench [cpp | cocotb].
    tb: Testbench name [default | afl].
    fuzzer: Fuzzer to use [sim | afl | afl-term-on-crash].
    run_on_gcp: Determines whether fuzzer will be run locally or on GCP [0 | 1].
    gcp_params: GCP parameters specifying what machine to launch fuzzer on. See
      example gcp_config.hjson file in root hw-fuzzing/.
    env_var_params: Other environment variables to define HDL generation,
      Verilator, and Fuzzer parameters. See example HJSON files in
      tests/.
    root_path: Root path of hw-fuzzing repository (set as an environment var).
    docker_image: Name of the Docker image that will be built to fuzz the DUT.
  """
  def __init__(self, args):
    """Constructs experiment configuration object from an HJSON file."""
    self.args = args
    self.config_filename = args.config_filename

    # Initialize experiment data paths
    self.root_path = os.getenv("HW_FUZZING")

    # Load GCP configurations
    print(LINE_SEP)
    print("Loading GCP configurations ...")
    with open(self.root_path + "/gcp_config.hjson", "r") as hjson_file:
      self.gcp_params = hjson.load(hjson_file)

    # Load experiment configurations
    print(LINE_SEP)
    print("Loading experiment configurations ...")
    with open(self.config_filename, "r") as hjson_file:
      cdict = hjson.load(hjson_file)
      self.experiment_name = cdict["experiment_name"]
      self.toplevel = cdict["toplevel"]
      self.version = cdict["version"]
      self.tb_type = cdict["tb_type"]
      self.tb = cdict["tb"]
      self.fuzzer = cdict["fuzzer"]
      self.manual = cdict["manual"]
      self.run_on_gcp = cdict["run_on_gcp"]
      self.env_var_params = [cdict["verilator_params"]]
      self.env_var_params.append(cdict["hdl_gen_params"])
      self.env_var_params.append(cdict["fuzzer_params"])

    # Initialize docker image tag
    if self.version == "HEAD":
      self.docker_image_tag = "latest"
    else:
      self.docker_image_tag = self.version

    # Initialize docker image name
    self.docker_image = "gcr.io/%s/%s-%s:%s" % (self.gcp_params["project_id"],
                                                self.fuzzer, self.toplevel,
                                                self.docker_image_tag)

    # Validate and print configurations
    self._validate_configs()
    self._print_configs()

  # TODO(ttrippel): make sure didn't make mistakes writing config file!
  def _validate_configs(self):
    return

  def _print_configs(self):
    exp_config_table = prettytable.PrettyTable(header=False)
    exp_config_table.title = "Experiment Parameters"
    exp_config_table.field_names = ["Parameter", "Value"]

    # Add main experiment parameters
    exp_config_table.add_row(["Experiment Name", self.experiment_name])
    exp_config_table.add_row(["Toplevel", self.toplevel])
    exp_config_table.add_row(["Version", self.version])
    exp_config_table.add_row(["Testbench Type", self.tb_type])
    exp_config_table.add_row(["Testbench", self.tb])
    exp_config_table.add_row(["Fuzzer", self.fuzzer])
    exp_config_table.add_row(["Manual", self.manual])
    exp_config_table.add_row(["Run on GCP", self.run_on_gcp])

    # Add other parameters
    for params in [self.gcp_params] + self.env_var_params:
      for param, value in params.items():
        param = param.replace("_", " ").title()
        exp_config_table.add_row([param, value])

    # Print table
    exp_config_table.align = "l"
    print(yellow(exp_config_table.get_string()))

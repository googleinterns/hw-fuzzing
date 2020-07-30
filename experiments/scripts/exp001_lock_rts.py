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
import copy
import os
import subprocess
import sys

# Installed dependencies
import hjson

# Custom modules
from config import color_str_green
from config import color_str_red
from config import color_str_yellow
from run_experiment import run_experiment

# Experiment configurations
BASE_CONFIG_DICT = {
    "experiment_name": None,
    "circuit": "lock",
    "testbench": "lock_test.cpp",
    "fuzzer": "afl",
    "run_on_gcp": "1",
    "hdl_gen_params": {},
    "fuzzer_params": {
        "num_instances": 1,
        "mode": "s",
        "duration_mins": None,
    },
}
NUM_STATES = [2, 4, 8, 16, 32, 64, 128, 156]
COMP_WIDTHS = [1, 2, 4, 8, 16, 32]

# Macros
LINE_SEP = "*******************************************************************"


def run_cmd(cmd, error_str):
  try:
    print("Running command:")
    print(color_str_yellow(subprocess.list2cmdline(cmd)))
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    print(color_str_red(error_str))
    sys.exit(1)


def main():
  num_experiments = len(NUM_STATES) * len(COMP_WIDTHS)
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(color_str_green("LAUNCHING %d EXPERIMENTS ..." % num_experiments))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  for states in NUM_STATES:
    for width in COMP_WIDTHS:
      # craft config dictionary
      cdict = copy.deepcopy(BASE_CONFIG_DICT)
      experiment_name = "exp001-lock-runtime-%dstates-%dwidth" % (states, width)
      cdict["experiment_name"] = experiment_name
      cdict["hdl_gen_params"]["num_lock_states"] = states
      cdict["hdl_gen_params"]["lock_comp_width"] = width
      cdict["hdl_gen_params"]["backtrack_probability"] = 0

      # write to HJSON file
      hjson_filename = experiment_name + ".hjson"
      hjson_file_path = os.path.join(os.getenv("HW_FUZZING"), \
          "experiments", "configs", hjson_filename)
      with open(hjson_file_path, "w") as fp:
        hjson.dump(cdict, fp)

      # launch experiment
      run_experiment([hjson_file_path])

      # cleanup config file
      os.remove(hjson_file_path)
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(color_str_green("DONE!"))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)

if __name__ == "__main__":
  main()

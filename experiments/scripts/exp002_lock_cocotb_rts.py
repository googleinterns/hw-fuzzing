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
    "testbench_dir": "tb/vlt",
    "fuzzer": "cocotb",
    "run_on_gcp": "1",
    "hdl_gen_params": {},
    "gcp_params": {
        "project": "hardware-fuzzing",
        "data_bucket": "fuzzing-data",
        "container_restart_policy": "never",
        "zone": "us-east1-b",
        "machine_type": "n1-standard-2",
        "boot_disk_size": "10GB",
        "scopes": "default,compute-rw,storage-rw",
        "startup_script_url": "gs://vm-management/gce_vm_startup.sh",
    },
    "verilator_params": {
        "opt_slow": "-O3",
        "opt_fast": "-O3",
        "opt_global": "-O3",
    },
    "fuzzer_params": {
    },
}

NUM_STATES = [2, 4, 8, 16, 32, 64]
COMP_WIDTHS = [1, 2, 4, 8]
RUNS = range(0, 20)

# NUM_STATES = [2]
# COMP_WIDTHS = [2]
# RUNS = range(0, 1)

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
  num_experiments = len(NUM_STATES) * len(COMP_WIDTHS) * len(RUNS)
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(color_str_green("LAUNCHING %d EXPERIMENTS ..." % num_experiments))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  for run in RUNS:
    for states in NUM_STATES:
      for width in COMP_WIDTHS:
        # craft config dictionary
        cdict = copy.deepcopy(BASE_CONFIG_DICT)
        experiment_name = "exp004-lock-runtime-cocotb-%dstates-%dwidth-%d" % \
            (states, width, run)
        cdict["experiment_name"] = experiment_name
        cdict["hdl_gen_params"]["num_lock_states"] = states
        cdict["hdl_gen_params"]["lock_comp_width"] = width

        # write to HJSON file
        hjson_filename = experiment_name + ".hjson"
        hjson_file_path = os.path.join(os.getenv("HW_FUZZING"), \
            "experiments", "configs", hjson_filename)
        with open(hjson_file_path, "w") as fp:
          hjson.dump(cdict, fp)

        # launch experiment
        run_experiment(["-y", hjson_file_path])

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

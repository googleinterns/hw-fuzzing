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
"""This launches several fuzzing experiments on GCP.

Description:

Usage Example:
  exp004_lock_afl_instru_complexity_throughput.py
"""

import copy
import os
import subprocess
import sys

import hjson

sys.path.append(os.getenv("HW_FUZZING"))
from infra.fuzz import fuzz
from infra.string_color import color_str_green as green
from infra.string_color import color_str_red as red
from infra.string_color import color_str_yellow as yellow

# Experiment configurations
BASE_CONFIG_DICT = {
    "experiment_name": "not-set",
    "toplevel": "lock",
    "version": "HEAD",
    "tb_type": "cpp",
    "tb": "afl",
    "fuzzer": "afl-term-on-crash",
    "instrument_dut": 1,
    "instrument_tb": 1,
    "instrument_vltrt": 1,
    "manual": 1,
    "run_on_gcp": 0,
    "hdl_gen_params": {},
    "verilator_params": {},
    "fuzzer_params": {
        "interactive_mode": 1,
        "timeout_ms": None,
        "memory_limit_mb": None,
        "num_instances": 1,
        "mode": "m",
        "duration_mins": 1440,
    },
}

# EXPERIMENT_BASE_NAMES = [
# "exp003-cpp-afl-lock-%dstates-%dwidth-full-instr-%d",
# "exp004-cpp-afl-lock-%dstates-%dwidth-duttb-instr-%d",
# "exp005-cpp-afl-lock-%dstates-%dwidth-dut-instr-%d"
# ]
# NUM_STATES = [8, 16, 32, 64, 128]
EXPERIMENT_BASE_NAMES = [
    "exp004-cpp-afl-lock-%dstates-%dwidth-duttb-instr-%d",
]
NUM_STATES = [8]
COMP_WIDTHS = [4]
RUNS = range(0, 1)

LINE_SEP = "*******************************************************************"


def _run_cmd(cmd, error_str):
  try:
    print("Running command:")
    print(yellow(subprocess.list2cmdline(cmd)))
    subprocess.check_call(cmd)
  except subprocess.CalledProcessError:
    print(red(error_str))
    sys.exit(1)


def _main():
  num_experiments = len(NUM_STATES) * len(COMP_WIDTHS) * len(RUNS)
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(green("LAUNCHING %d EXPERIMENTS ..." % num_experiments))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)

  # create a temp dir to store config files
  tmp_dir = os.path.join(os.getcwd(), "tmp%d")
  i = 0
  while os.path.isdir(tmp_dir % i):
    i += 1
  tmp_dir = tmp_dir % i
  os.mkdir(tmp_dir)

  # create config files on the fly and launch experiments
  for run in RUNS:
    for experiment_name in EXPERIMENT_BASE_NAMES:
      for states in NUM_STATES:
        for width in COMP_WIDTHS:
          # craft config dictionary
          cdict = copy.deepcopy(BASE_CONFIG_DICT)

          # Set experiment name
          experiment_name = experiment_name % (states, width, run)
          cdict["experiment_name"] = experiment_name

          # Set instrumentation amount
          if "full-instr" in experiment_name:
            cdict["instrument_dut"] = 1
            cdict["instrument_tb"] = 1
            cdict["instrument_vltrt"] = 1
          elif "duttb-instr" in experiment_name:
            cdict["instrument_dut"] = 1
            cdict["instrument_tb"] = 1
            cdict["instrument_vltrt"] = 0
          elif "dut" in experiment_name:
            cdict["instrument_dut"] = 1
            cdict["instrument_tb"] = 0
            cdict["instrument_vltrt"] = 0
          else:
            print(red("ERROR: invalid instrumentation config. ABORTING!"))
            sys.exit(1)

          # Set lock size
          cdict["hdl_gen_params"]["num_lock_states"] = states
          cdict["hdl_gen_params"]["lock_comp_width"] = width

          # write to HJSON file
          hjson_filename = experiment_name + ".hjson"
          hjson_file_path = os.path.join(tmp_dir, hjson_filename)
          with open(hjson_file_path, "w") as fp:
            hjson.dump(cdict, fp)

          # launch fuzz the DUT
          fuzz([hjson_file_path])

          # cleanup config file
          os.remove(hjson_file_path)

  # remove temp dir
  os.rmdir(tmp_dir)

  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(green("DONE!"))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)


if __name__ == "__main__":
  _main()

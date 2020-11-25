#!/usr/bin/env python3
# Copyright 2020 Timothy Trippel
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

import copy
import glob
import os
import shutil
import sys

import hjson
from hwfp.fuzz import fuzz
from hwfutils.string_color import color_str_green as green
from hwfutils.string_color import color_str_red as red

from lock_config_dict import CONFIG_DICT

EXPERIMENT_BASE_NAMES = [
    "exp002-cpp-afl-lock-%dstates-%dwidth-full-instr-%d",
    "exp003-cpp-afl-lock-%dstates-%dwidth-duttb-instr-%d",
    "exp004-cpp-afl-lock-%dstates-%dwidth-dut-instr-%d",
    "exp005-cpp-afl-lock-%dstates-%dwidth-full-instr-wopt-%d",
    "exp006-cpp-afl-lock-%dstates-%dwidth-duttb-instr-wopt-%d",
    "exp007-cpp-afl-lock-%dstates-%dwidth-dut-instr-wopt-%d",
]
NUM_STATES = [8]
# NUM_STATES = [16, 32, 64]
COMP_WIDTHS = [4]
RUNS = range(0, 50)

LINE_SEP = "*******************************************************************"


def _main():
  num_experiments = len(NUM_STATES) * len(COMP_WIDTHS) * len(RUNS) * len(
      EXPERIMENT_BASE_NAMES)
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(green("LAUNCHING %d EXPERIMENTS ..." % num_experiments))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)

  # create a temp dir to store config files
  try:
    tmp_dir = os.path.join(os.getcwd(), "tmp%d")
    i = 0
    while os.path.isdir(tmp_dir % i):
      i += 1
    tmp_dir = tmp_dir % i
    os.mkdir(tmp_dir)

    # create config files on the fly and launch experiments
    for experiment_base_name in EXPERIMENT_BASE_NAMES:
      for states in NUM_STATES:
        for width in COMP_WIDTHS:
          for run in RUNS:
            # craft config dictionary
            cdict = copy.deepcopy(CONFIG_DICT)

            # Set experiment name
            experiment_name = experiment_base_name % (states, width, run)
            cdict["experiment_name"] = experiment_name

            # Set test bench
            if "wopt" in experiment_name:
              cdict["tb"] = "afl_opt"
            else:
              cdict["tb"] = "afl"

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
            fuzz(["--fail-silently", hjson_file_path])

            # cleanup config file
            os.remove(hjson_file_path)

  finally:
    # remove temp dir
    for tmp_dir in glob.glob("tmp*"):
      shutil.rmtree(tmp_dir, ignore_errors=True)

  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)
  print(green("DONE!"))
  print(LINE_SEP)
  print(LINE_SEP)
  print(LINE_SEP)


if __name__ == "__main__":
  _main()

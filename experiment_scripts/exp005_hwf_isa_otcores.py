#!/usr/bin/python3
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
import itertools
import os
import shutil

import hjson
from hwfp.fuzz import fuzz
from hwfutils.string_color import color_str_green as green

from ot_config_dict import CONFIG_DICT

# ------------------------------------------------------------------------------
# Experiment Parameters
# ------------------------------------------------------------------------------
EXPERIMENT_BASE_NAME = "exp009-cpp-afl-%s-%s-%s-%s-%d"
DURATION_MINS = 60
# DURATION_MINS = 1440  # 24 hours
# TOPLEVELS = ["aes", "hmac", "kmac", "rv_timer"]
TOPLEVELS = ["rv_timer"]
# OPCODE_TYPES = ["constant"]
# INSTR_TYPES = ["fixed"]
# TERMINATE_TYPES = ["invalidop"]
OPCODE_TYPES = ["constant", "mapped"]
INSTR_TYPES = ["variable", "fixed"]
TERMINATE_TYPES = ["invalidop", "never"]
# RUNS = range(0, 20)
# RUNS = range(0, 2)
RUNS = range(0, 5)
# ------------------------------------------------------------------------------

TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)


def _main():
  isas = list(
      itertools.product(TOPLEVELS, OPCODE_TYPES, INSTR_TYPES, TERMINATE_TYPES))
  print(LINE_SEP)
  print(green("Launching %d experiments ..." % (len(isas) * len(RUNS))))
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
    for toplevel, opcode_type, instr_type, terminate_type in isas:
      for run in RUNS:
        # craft config dictionary
        cdict = copy.deepcopy(CONFIG_DICT)

        # Set experiment name
        experiment_name = EXPERIMENT_BASE_NAME % (
            toplevel, opcode_type, instr_type, terminate_type, run)
        experiment_name = experiment_name.replace("_", "-")
        # print(experiment_name)
        # continue
        cdict["experiment_name"] = experiment_name
        cdict["toplevel"] = toplevel

        # Set configurations
        cdict["fuzzer_params"]["duration_mins"] = DURATION_MINS
        cdict["model_params"]["opcode_type"] = opcode_type
        cdict["model_params"]["instr_type"] = instr_type
        if terminate_type == "invalidop":
          cdict["model_params"]["terminate_on_invalid_opcode"] = 1
        else:
          cdict["model_params"]["terminate_on_invalid_opcode"] = 0

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
    for directory in glob.glob("tmp*"):
      shutil.rmtree(directory)

  print(LINE_SEP)
  print(green("DONE!"))
  print(LINE_SEP)


if __name__ == "__main__":
  _main()

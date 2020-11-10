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
import os

import hjson
from hwfp.fuzz import fuzz
from hwfutils.string_color import color_str_green as green

from ot_config_dict import CONFIG_DICT

EXPERIMENT_BASE_NAME = "exp008-cpp-afl-aes-%s-%s-%s-%d"
TOPLEVEL = "aes"
OPCODE_TYPES = ["constant", "mapped"]
INSTR_TYPES = ["variable", "fixed"]
TERMINATE_TYPES = ["invalidop", "never"]
# RUNS = range(0, 20)
RUNS = range(1, 2)

LINE_SEP = "*******************************************************************"


def _main():
  num_experiments = len(OPCODE_TYPES) * len(INSTR_TYPES) * len(TERMINATE_TYPES)
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
    for run in RUNS:
      for opcode_type in OPCODE_TYPES:
        for instr_type in INSTR_TYPES:
          for term_type in TERMINATE_TYPES:
            # craft config dictionary
            cdict = copy.deepcopy(CONFIG_DICT)

            # Set experiment name
            experiment_name = EXPERIMENT_BASE_NAME % (opcode_type, instr_type,
                                                      term_type, run)
            print(experiment_name)
            cdict["experiment_name"] = experiment_name
            cdict["toplevel"] = TOPLEVEL

            # Set configurations
            cdict["model_params"]["opcode_type"] = opcode_type
            cdict["model_params"]["instr_type"] = instr_type
            if term_type == "invalidop":
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

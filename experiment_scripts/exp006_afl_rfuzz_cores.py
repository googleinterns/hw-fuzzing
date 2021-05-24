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
import tempfile

import hjson
from hwfp.fuzz import fuzz
from hwfutils.string_color import color_str_green as green
from rfuzz_config_dict import CONFIG_DICT

# ------------------------------------------------------------------------------
# Experiment Parameters
# ------------------------------------------------------------------------------
EXPERIMENT_BASE_NAME = "exp016-rfuzz-afl-%s-%sm-%d"
DURATION_MINS = 1440
TOPLEVELS = ["Sodor3Stage", "FFTSmall", "TLI2C", "TLPWM", "TLSPI", "TLUART"]
RUNS = range(0, 2)
# ------------------------------------------------------------------------------

TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)


def _main():
  print(LINE_SEP)
  print(green("Launching %d experiments ..." % (len(TOPLEVELS) * len(RUNS))))
  print(LINE_SEP)

  # create a temp dir to store config files
  with tempfile.TemporaryDirectory() as tmp_dir:
    # create config files on the fly and launch experiments
    for toplevel in TOPLEVELS:
      for run in RUNS:
        # craft config dictionary
        cdict = copy.deepcopy(CONFIG_DICT)

        # Set experiment name
        experiment_name = EXPERIMENT_BASE_NAME % (toplevel, DURATION_MINS, run)
        experiment_name = experiment_name.replace("_", "-").lower()
        cdict["experiment_name"] = experiment_name
        cdict["toplevel"] = toplevel

        # Set configurations
        cdict["fuzzer_params"]["duration_mins"] = DURATION_MINS

        # write to HJSON file
        hjson_filename = experiment_name + ".hjson"
        hjson_file_path = os.path.join(tmp_dir, hjson_filename)
        with open(hjson_file_path, "w") as fp:
          hjson.dump(cdict, fp)

        # launch fuzz the DUT
        fuzz(["--fail-silently", hjson_file_path])
        # fuzz([
        # "-y", "--gcp-config-filename", "gcp_config.east1b.hjson",
        # hjson_file_path
        # ])

        # cleanup config file
        os.remove(hjson_file_path)

  print(LINE_SEP)
  print(green("DONE!"))
  print(LINE_SEP)


if __name__ == "__main__":
  _main()

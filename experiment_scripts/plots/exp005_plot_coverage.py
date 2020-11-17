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

import argparse
import glob
import itertools
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from hwfutils.string_color import color_str_green as green
from hwfutils.string_color import color_str_red as red
from hwfutils.string_color import color_str_yellow as yellow
from scipy import stats

# ------------------------------------------------------------------------------
# Plot parameters
# ------------------------------------------------------------------------------
MARKER_SIZE = 5
ZSCORE_THRESHOLD = 3

# ------------------------------------------------------------------------------
# Plot labels
# ------------------------------------------------------------------------------
TIME_LABEL = "Time (s)"
TOPLEVEL_LABEL = "IP Block"
ISA_LABEL = "Grammar"
AFL_TEST_ID_LABEL = "Test ID"
COVERAGE_TYPE_LABEL = "Coverage Type"
COVERAGE_LABEL = "Coverage (%)"

# LINES_COVERED_LABEL = "Lines Covered"
# TOTAL_LINES_LABEL = "Total Lines"
# LINE_COVERAGE_LABEL = "Line Coverage"
# REGIONS_COVERED_LABEL = "Regions Covered"
# TOTAL_REGIONS_LABEL = "Total Regions"
# REGION_COVERAGE_LABEL = "Region Coverage"

# ------------------------------------------------------------------------------
# Experiment Status Labels
# ------------------------------------------------------------------------------

NUM_TRIALS_COMPLETED_LABEL = "# Trials Completed"
TRIALS_MISSING_LABEL = "Trials Missing"

# ------------------------------------------------------------------------------
# Experiment Parameters
# ------------------------------------------------------------------------------
EXPERIMENT_BASE_NAME = "exp009-cpp-afl-%s-%s-%s-%s"
# TOPLEVELS = ["aes", "hmac", "kmac", "rv_timer"]
TOPLEVELS = ["aes", "hmac", "rv_timer"]
OPCODE_TYPES = ["constant", "mapped"]
INSTR_TYPES = ["variable", "fixed"]
TERMINATE_TYPES = ["invalidop", "never"]
TRIALS = range(0, 5)

# ------------------------------------------------------------------------------
# Other defines
# ------------------------------------------------------------------------------
TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)


def build_coverage_df(kcov_dfs, vlt_cov_dfs, llvm_cov_dfs):
  print(yellow("Building coverage dataframe ..."))
  all_cov_data = {
      "kcov": kcov_dfs,
      "Verilator": vlt_cov_dfs,
      "LLVM": llvm_cov_dfs,
  }
  # Create empty dataframe
  column_names = [
      TOPLEVEL_LABEL,
      ISA_LABEL,
      COVERAGE_TYPE_LABEL,
      AFL_TEST_ID_LABEL,
      COVERAGE_LABEL,
  ]
  coverage_df = pd.DataFrame(columns=column_names)
  # Add rows to the dataframe
  for cov_type, cov_dfs in all_cov_data.items():
    for exp_name, cov_df in cov_dfs.items():
      # Extract experiment details from name
      exp_name_list = exp_name.split("-")
      toplevel = exp_name_list[3]
      if toplevel == "rv":
        toplevel += "_%s" % exp_name_list[4]
        opcode_type = exp_name_list[5]
        instr_type = exp_name_list[6]
        terminate_type = exp_name_list[7]
      else:
        opcode_type = exp_name_list[4]
        instr_type = exp_name_list[5]
        terminate_type = exp_name_list[6]
      isa = "%s-%s-%s" % (opcode_type, instr_type, terminate_type)
      for _, row in cov_df.iterrows():
        test_id = int(row["Test-ID"].lstrip("id:"))
        if cov_type == "Verilator":
          line_coverage = float(row["Lines-Covered"]) / float(
              row["Total-Lines"])
        else:
          line_coverage = row["Line-Coverage-(%)"]
        # Update dataframe
        coverage_df = coverage_df.append(
            {
                TOPLEVEL_LABEL: toplevel,
                ISA_LABEL: isa,
                COVERAGE_TYPE_LABEL: cov_type,
                AFL_TEST_ID_LABEL: test_id,
                COVERAGE_LABEL: line_coverage,
            },
            ignore_index=True)
  print(green("Done."))
  print(LINE_SEP)
  return coverage_df


def load_all_afl_data(data_root):
  print(yellow("Loading all AFL plot data into dataframes ..."))
  # create dictionary for tracking missing experiment data
  exp_status_dict = defaultdict(int)
  exps_missing = defaultdict(list)

  # create dictionary to hold AFL plot dataframes
  afl_plot_dfs = {}

  # extract each data file into a Pandas dataframe
  isas = list(
      itertools.product(TOPLEVELS, OPCODE_TYPES, INSTR_TYPES, TERMINATE_TYPES))
  for toplevel, opcode_type, instr_type, terminate_type in isas:
    for trial in TRIALS:
      # Build complete path of AFL plot data file
      exp_name_wo_trialnum = EXPERIMENT_BASE_NAME % (
          toplevel, opcode_type, instr_type, terminate_type)
      exp_name_wo_trialnum = exp_name_wo_trialnum.replace("_", "-")
      exp_name = "%s-%d" % (exp_name_wo_trialnum, trial)
      afl_plot_data_files = glob.glob(
          os.path.join(data_root, exp_name, "out", "afl_*_interactive",
                       "plot_data"))
      if len(afl_plot_data_files) > 1:
        print(
            red("ERROR: more than one possible AFL plot data file for: %s" %
                exp_name))
        sys.exit(1)

      # Check if experiment data exists locally
      if afl_plot_data_files:
        exp_status_dict[exp_name_wo_trialnum] += 1
        # parse AFL plot data file
        afl_plot_dfs[exp_name] = pd.read_csv(afl_plot_data_files[0],
                                             delimiter=',',
                                             index_col=None,
                                             engine='python')
      else:
        exps_missing[exp_name_wo_trialnum].append(trial)

  # report missing experiment data and return data we found
  # report_missing_exp_data(exp_status_dict, exps_missing)
  print(green("Done."))
  print(LINE_SEP)
  return afl_plot_dfs


def load_all_coverage_data(data_root, csv_filename):
  print(yellow("Loading all %s data into dataframes ..." % csv_filename))
  # create dictionary to hold coverage dataframes
  cov_dfs = {}

  # extract each data file into a Pandas dataframe
  isas = list(
      itertools.product(TOPLEVELS, OPCODE_TYPES, INSTR_TYPES, TERMINATE_TYPES))
  for toplevel, opcode_type, instr_type, terminate_type in isas:
    for trial in TRIALS:
      # Build complete path of AFL plot data file
      exp_name_wo_trialnum = EXPERIMENT_BASE_NAME % (
          toplevel, opcode_type, instr_type, terminate_type)
      exp_name_wo_trialnum = exp_name_wo_trialnum.replace("_", "-")
      exp_name = "%s-%d" % (exp_name_wo_trialnum, trial)
      data_file = os.path.join(data_root, exp_name, "logs", csv_filename)
      if not os.path.exists(data_file):
        print(red("ERROR: coverage data file (%s) does not exist." %
                  data_file))
        sys.exit(1)

      # load coverage data file
      cov_dfs[exp_name] = pd.read_csv(data_file,
                                      delimiter=',',
                                      index_col=None,
                                      engine='python')

  # report missing experiment data and return data we found
  # report_missing_exp_data(exp_status_dict, exps_missing)
  print(green("Done."))
  print(LINE_SEP)
  return cov_dfs


def main(argv):
  parser = argparse.ArgumentParser(description="Plotting script for exp. 004.")
  parser.add_argument("data_root")
  args = parser.parse_args()

  # Load runtime data
  # afl_plot_dfs = load_all_afl_data(args.data_root)
  kcov_dfs = load_all_coverage_data(args.data_root, "kcov_cum.csv")
  vlt_cov_dfs = load_all_coverage_data(args.data_root, "vlt_cov_cum.csv")
  llvm_cov_dfs = load_all_coverage_data(args.data_root, "llvm_cov_cum.csv")
  coverage_df = build_coverage_df(kcov_dfs, vlt_cov_dfs, llvm_cov_dfs)
  print(coverage_df.head(10))
  # runtimes_df.to_csv("temp.csv", index=False)
  # runtimes_df = pd.read_csv("temp.csv",
  # delimiter=',',
  # index_col=None,
  # engine='python')

  # Condition the data

  # Compute stats

  # # Plot the instrumentation complexity data
  # sns.set()
  # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 4))
  # sns.stripplot(x=NUM_STATES_LABEL,
  # y=RUN_TIME_LABEL,
  # hue=INSTR_TYPE_LABEL,
  # data=instr_type_runtimes_df,
  # dodge=True,
  # size=MARKER_SIZE,
  # ax=ax1)
  # sns.stripplot(x=NUM_STATES_LABEL,
  # y=RUN_TIME_LABEL,
  # hue=OPT_TYPE_LABEL,
  # data=fs_opt_runtimes_df,
  # dodge=True,
  # size=MARKER_SIZE,
  # ax=ax2)
  # plt.show()


if __name__ == "__main__":
  main(sys.argv[1:])

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

# Plot parameters
MARKER_SIZE = 5
ZSCORE_THRESHOLD = 3

# Plot labels
RUN_TIME_LABEL = "Time to Full FSM Coverage (Relative)"
NUM_STATES_LABEL = "# FSM states"
WIDTH_LABEL = "width"
INSTR_TYPE_LABEL = "Components Instrumented"
OPT_TYPE_LABEL = "Fork Server Init."
INSTR_TYPE_MAPPINGS = {
    # "full": "All",
    # "duttb": "DUT & TB",
    # "dut": "DUT only",
    "full": "full",
    "duttb": "duttb",
    "dut": "dut",
}
OPT_TYPE_MAPPINGS = {
    False: "TB Startup",
    True: "After DUT Reset",
}

# Experiment Status Labels
NUM_TRIALS_COMPLETED_LABEL = "# Trials Completed"
TRIALS_MISSING_LABEL = "Trials Missing"

# Experiment selection
EXP_BASE_NAMES = [
    "exp002-cpp-afl-lock-%dstates-%dwidth-full-instr",
    "exp003-cpp-afl-lock-%dstates-%dwidth-duttb-instr",
    "exp004-cpp-afl-lock-%dstates-%dwidth-dut-instr",
    "exp005-cpp-afl-lock-%dstates-%dwidth-full-instr-wopt",
    "exp006-cpp-afl-lock-%dstates-%dwidth-duttb-instr-wopt",
    "exp007-cpp-afl-lock-%dstates-%dwidth-dut-instr-wopt",
]
STATES = [16, 32, 64]
# STATES = [16, 32, 64, 128]
WIDTHS = [4]
TRIALS = range(50)

# Other defines
TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)


def build_runtime_df(afl_plot_dfs):
  # Create empty dataframe
  column_names = [
      NUM_STATES_LABEL,
      WIDTH_LABEL,
      INSTR_TYPE_LABEL,
      OPT_TYPE_LABEL,
      RUN_TIME_LABEL,
  ]
  runtimes_df = pd.DataFrame(columns=column_names)
  # Add rows to the dataframe
  for exp_name, exp_df in afl_plot_dfs.items():
    # Extract experiment details from name
    exp_name_list = exp_name.split("-")
    num_states = int(exp_name_list[4].rstrip("states"))
    width = int(exp_name_list[5].rstrip("width"))
    instr_type = exp_name_list[6]
    if len(exp_name_list) > 9:
      fs_opt = True
    else:
      fs_opt = False
    # Compute fuzzing runtime
    start_time = exp_df["# unix_time"].iloc[0]
    stop_time = exp_df["# unix_time"].iloc[-1]
    runtime = stop_time - start_time
    # Update dataframe
    runtimes_df = runtimes_df.append(
        {
            NUM_STATES_LABEL: num_states,
            WIDTH_LABEL: width,
            INSTR_TYPE_LABEL: INSTR_TYPE_MAPPINGS[instr_type],
            OPT_TYPE_LABEL: OPT_TYPE_MAPPINGS[fs_opt],
            RUN_TIME_LABEL: runtime,
        },
        ignore_index=True)
  return runtimes_df


def report_missing_exp_data(exp_status_dict, exps_missing):
  # Format status tracking dict to create dataframe to print to console
  status_dict = {
      NUM_STATES_LABEL: [],
      WIDTH_LABEL: [],
      INSTR_TYPE_LABEL: [],
      OPT_TYPE_LABEL: [],
      NUM_TRIALS_COMPLETED_LABEL: [],
      TRIALS_MISSING_LABEL: [],
  }
  for width in WIDTHS:
    for state in STATES:
      for exp_base_name in EXP_BASE_NAMES:
        exp_name_wo_trialnum = exp_base_name % (state, width)
        exp_name_list = exp_name_wo_trialnum.split("-")
        status_dict[NUM_STATES_LABEL].append(state)
        status_dict[WIDTH_LABEL].append(width)
        status_dict[INSTR_TYPE_LABEL].append(exp_name_list[6])
        if len(exp_name_list) > 8:
          status_dict[OPT_TYPE_LABEL].append(True)
        else:
          status_dict[OPT_TYPE_LABEL].append(False)
        status_dict[NUM_TRIALS_COMPLETED_LABEL].append(
            exp_status_dict[exp_name_wo_trialnum])
        status_dict[TRIALS_MISSING_LABEL].append(
            exps_missing[exp_name_wo_trialnum])
  status_df = pd.DataFrame.from_dict(status_dict)
  print(status_df)


def load_all_afl_data(data_root):
  print(yellow("Loading all AFL plot data into dataframes ..."))
  # create dictionary for tracking missing experiment data
  exp_status_dict = defaultdict(int)
  exps_missing = defaultdict(list)

  # create dictionary to hold AFL plot dataframes
  afl_plot_dfs = {}

  # extract each data file into a Pandas dataframe
  for width in WIDTHS:
    for num_states in STATES:
      for exp_base_name in EXP_BASE_NAMES:
        for trial in TRIALS:
          # Build complete path of AFL plot data file
          exp_name_wo_trialnum = exp_base_name % (num_states, width)
          exp_name = "%s-%d" % (exp_name_wo_trialnum, trial)
          afl_plot_data_files = glob.glob(
              os.path.join(data_root, exp_name, "out", "afl_*_interactive",
                           "plot_data"))
          if len(afl_plot_data_files) > 1:
            print(
                red("ERROR: more than one possible AFL plot data file for: %s"
                    % exp_name))
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
  report_missing_exp_data(exp_status_dict, exps_missing)
  print(green("Done."))
  print(LINE_SEP)
  return afl_plot_dfs


def normalize_instr_type_runtimes(runtimes_df, zscore_threshold=3):
  print(yellow("Normalizing instrumentation complexity data ..."))
  # Parameters
  INSTR_TYPE_BASELINE = INSTR_TYPE_MAPPINGS["full"]
  FS_OPT_BASELINE = OPT_TYPE_MAPPINGS[False]
  # extract only instrumentation only data from dataframe
  runtimes_df = runtimes_df.loc[runtimes_df[OPT_TYPE_LABEL] ==
                                FS_OPT_BASELINE, :]
  # print(runtimes_df.head(10))
  normalized_df = pd.DataFrame(columns=runtimes_df.columns)
  for num_states in STATES:
    sub_rt_df = runtimes_df[runtimes_df[NUM_STATES_LABEL] == num_states].copy()
    for instr_type in INSTR_TYPE_MAPPINGS.values():
      sub_sub_rt_df = sub_rt_df[sub_rt_df[INSTR_TYPE_LABEL] ==
                                instr_type].copy()
      # drop outliers
      sub_sub_rt_df = sub_sub_rt_df[
          np.abs(stats.zscore(sub_sub_rt_df[RUN_TIME_LABEL].astype(
              float))) < zscore_threshold]
      # compute mean
      if instr_type == INSTR_TYPE_BASELINE:
        mean = sub_sub_rt_df[RUN_TIME_LABEL].mean()
      # normalize to mean of full instrumentation
      sub_sub_rt_df.loc[:, RUN_TIME_LABEL] /= float(mean)
      normalized_df = normalized_df.append(sub_sub_rt_df, ignore_index=True)
  print(green("Done."))
  # print(normalized_df.head(10))
  print(LINE_SEP)
  return normalized_df


def normalize_fsopt_runtimes(runtimes_df, zscore_threshold=3):
  print(yellow("Normalizing fork server optimization data ..."))
  # Parameters
  FS_OPT_BASELINE = OPT_TYPE_MAPPINGS[False]
  # extract only instrumentation only data from dataframe
  runtimes_df = runtimes_df.loc[runtimes_df[INSTR_TYPE_LABEL] ==
                                INSTR_TYPE_MAPPINGS["dut"], :]
  # print(runtimes_df.head(10))
  normalized_df = pd.DataFrame(columns=runtimes_df.columns)
  for num_states in STATES:
    sub_rt_df = runtimes_df[runtimes_df[NUM_STATES_LABEL] == num_states].copy()
    for fs_opt in OPT_TYPE_MAPPINGS.values():
      sub_sub_rt_df = sub_rt_df[sub_rt_df[OPT_TYPE_LABEL] == fs_opt].copy()
      # drop outliers
      sub_sub_rt_df = sub_sub_rt_df[
          np.abs(stats.zscore(sub_sub_rt_df[RUN_TIME_LABEL].astype(
              float))) < zscore_threshold]
      # compute mean
      if fs_opt == FS_OPT_BASELINE:
        mean = sub_sub_rt_df[RUN_TIME_LABEL].mean()
      # normalize to mean of full instrumentation
      sub_sub_rt_df.loc[:, RUN_TIME_LABEL] /= float(mean)
      normalized_df = normalized_df.append(sub_sub_rt_df, ignore_index=True)
  print(green("Done."))
  # print(normalized_df.head(10))
  print(LINE_SEP)
  return normalized_df


def compute_instr_type_mann_whitney(runtimes_df, zscore_threshold=3):
  print(
      yellow(
          "Computing Mann-Whitney U-test on instrumentation complexity data ..."
      ))
  # Parameters
  FS_OPT_BASELINE = OPT_TYPE_MAPPINGS[False]
  # extract only instrumentation only data from dataframe
  runtimes_df = runtimes_df.loc[runtimes_df[OPT_TYPE_LABEL] ==
                                FS_OPT_BASELINE, :]
  # drop outliers
  cleaned_df = pd.DataFrame(columns=runtimes_df.columns)
  for num_states in STATES:
    sub_rt_df = runtimes_df[runtimes_df[NUM_STATES_LABEL] == num_states].copy()
    for instr_type in INSTR_TYPE_MAPPINGS.values():
      sub_sub_rt_df = sub_rt_df[sub_rt_df[INSTR_TYPE_LABEL] ==
                                instr_type].copy()
      sub_sub_rt_df = sub_sub_rt_df[
          np.abs(stats.zscore(sub_sub_rt_df[RUN_TIME_LABEL].astype(
              float))) < zscore_threshold]
      cleaned_df = cleaned_df.append(sub_sub_rt_df, ignore_index=True)
  # Compute Mann-Whitney U-test
  for num_states in STATES:
    sub_rt_df = cleaned_df[cleaned_df[NUM_STATES_LABEL] == num_states]
    full_instr_data = sub_rt_df[sub_rt_df[INSTR_TYPE_LABEL] ==
                                INSTR_TYPE_MAPPINGS["full"]][RUN_TIME_LABEL]
    duttb_instr_data = sub_rt_df[sub_rt_df[INSTR_TYPE_LABEL] ==
                                 INSTR_TYPE_MAPPINGS["duttb"]][RUN_TIME_LABEL]
    dut_instr_data = sub_rt_df[sub_rt_df[INSTR_TYPE_LABEL] ==
                               INSTR_TYPE_MAPPINGS["dut"]][RUN_TIME_LABEL]
    mw_full_duttb = stats.mannwhitneyu(full_instr_data, duttb_instr_data)
    mw_full_dut = stats.mannwhitneyu(full_instr_data, dut_instr_data)
    mw_duttb_dut = stats.mannwhitneyu(duttb_instr_data, dut_instr_data)
    print("%d States - Mann-Whitney:" % num_states)
    print(
        "\t%s vs. %s:" %
        (INSTR_TYPE_MAPPINGS["full"], INSTR_TYPE_MAPPINGS["duttb"]),
        mw_full_duttb)
    print(
        "\t%s vs. %s:" %
        (INSTR_TYPE_MAPPINGS["full"], INSTR_TYPE_MAPPINGS["dut"]), mw_full_dut)
    print(
        "\t%s vs. %s:" %
        (INSTR_TYPE_MAPPINGS["duttb"], INSTR_TYPE_MAPPINGS["dut"]),
        mw_duttb_dut)
  print(green("Done."))
  print(LINE_SEP)


def main(argv):
  parser = argparse.ArgumentParser(description="Plotting script for exp. 004.")
  parser.add_argument("data_root")
  args = parser.parse_args()

  # Load runtime data
  afl_plot_dfs = load_all_afl_data(args.data_root)
  runtimes_df = build_runtime_df(afl_plot_dfs)
  # runtimes_df.to_csv("temp.csv", index=False)
  # runtimes_df = pd.read_csv("temp.csv",
  # delimiter=',',
  # index_col=None,
  # engine='python')

  # Condition the data
  instr_type_runtimes_df = normalize_instr_type_runtimes(
      runtimes_df, zscore_threshold=ZSCORE_THRESHOLD)
  fs_opt_runtimes_df = normalize_fsopt_runtimes(
      runtimes_df, zscore_threshold=ZSCORE_THRESHOLD)

  # Compute stats
  compute_instr_type_mann_whitney(runtimes_df,
                                  zscore_threshold=ZSCORE_THRESHOLD)

  # Plot the instrumentation complexity data
  sns.set()
  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 4))
  sns.stripplot(x=NUM_STATES_LABEL,
                y=RUN_TIME_LABEL,
                hue=INSTR_TYPE_LABEL,
                data=instr_type_runtimes_df,
                dodge=True,
                size=MARKER_SIZE,
                ax=ax1)
  sns.stripplot(x=NUM_STATES_LABEL,
                y=RUN_TIME_LABEL,
                hue=OPT_TYPE_LABEL,
                data=fs_opt_runtimes_df,
                dodge=True,
                size=MARKER_SIZE,
                ax=ax2)
  plt.show()


if __name__ == "__main__":
  main(sys.argv[1:])

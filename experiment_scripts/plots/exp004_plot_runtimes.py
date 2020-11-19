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
import collections
import glob
import itertools
import os
import sys
from dataclasses import dataclass

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
# Plot Labels
# ------------------------------------------------------------------------------
RUN_TIME_LABEL = "Time to Full FSM Coverage (Relative)"
NUM_STATES_LABEL = "# FSM states"
WIDTH_LABEL = "width"
INSTR_TYPE_LABEL = "Components Instrumented"
OPT_TYPE_LABEL = "Fork Server Init."
INSTR_TYPE_MAPPINGS = {
    "full": "All",
    "duttb": "DUT & TB",
    "dut": "DUT only",
    # "full": "full",
    # "duttb": "duttb",
    # "dut": "dut",
}
OPT_TYPE_MAPPINGS = {
    False: "TB Startup",
    True: "After DUT Reset",
}

# ------------------------------------------------------------------------------
# Experiment Status Labels
# ------------------------------------------------------------------------------
NUM_TRIALS_COMPLETED_LABEL = "# Trials Completed"
TRIALS_MISSING_LABEL = "Trials Missing"

# ------------------------------------------------------------------------------
# Experiment Parameters
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# Other defines
# ------------------------------------------------------------------------------
TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)


@dataclass
class FuzzingData:
  num_states: int = -1
  width: int = -1
  instr_type: str = ""
  fs_opt: bool = False
  trial_num: int = -1
  data_path: str = ""

  def __post_init__(self):
    self.afl_data = self._load_afl_data()

  def _load_csv_data(self, csv_file):
    return pd.read_csv(csv_file,
                       delimiter=',',
                       index_col=None,
                       engine='python')

  def _load_afl_data(self):
    afl_glob_path = os.path.join(self.data_path, "out", "afl_*_interactive",
                                 "plot_data")
    afl_plot_data_files = glob.glob(afl_glob_path)
    if len(afl_plot_data_files) != 1:
      print(red("ERROR: AFL plot_data file no found."))
      sys.exit(1)
    # Load data into Pandas DataFrame
    afl_df = self._load_csv_data(afl_plot_data_files[0])
    # Remove leading/trailing white space from column names
    afl_df = afl_df.rename(columns=lambda x: x.strip())
    # Adjust time stamps to be relative to start time
    afl_df.loc[:, "# unix_time"] -= afl_df.loc[0, "# unix_time"]
    return afl_df

  @property
  def runtime(self):
    return float(self.afl_data["# unix_time"].max() -
                 self.afl_data["# unix_time"].min())


def _drop_outliers_in_range(values, lower_percentile=30, upper_percentile=70):
  median = np.median(values)
  mean = np.mean(values)
  lower_bound, upper_bound = np.percentile(
      values, [lower_percentile, upper_percentile])
  trimmed_values = []
  for i in range(len(values)):
    if lower_bound <= values[i] < upper_bound:
      trimmed_values.append(values[i])
    # else:
    # trimmed_values.append(median)
    # trimmed_values.append(mean)
  return trimmed_values


def _aggregrate_instr_complex_rts(exp2data):
  exp2rts = {}
  for exp_name, fd_list in exp2data.items():
    # if fd_list[0].instr_type != "duttb" and fd_list[0].fs_opt is False:
    if fd_list[0].fs_opt is False:
      runtimes = []
      for trial in TRIALS:
        fd = fd_list[trial]
        runtimes.append(fd.runtime)
      runtimes = _drop_outliers_in_range(runtimes)
      exp2rts[(fd.num_states, fd.instr_type, fd.fs_opt)] = runtimes
  return exp2rts


def build_instr_complex_rts_df(exp2data):
  print(yellow("Building instruction complexity dataframe ..."))
  INSTR_TYPE_BASELINE = "dut"
  # Create empty dictionary that will be used to create Pandas
  # a DataFrame that look like the following:
  # +-------------------------------------------------+
  # | # states | instrumenttation level | runtime (s) |
  # +-------------------------------------------------+
  # |   ...    |           ...          |     ...     |
  runtimes_dict = {
      NUM_STATES_LABEL: [],
      INSTR_TYPE_LABEL: [],
      RUN_TIME_LABEL: [],
  }
  # Aggregate data into a dictionary
  exp2rts = _aggregrate_instr_complex_rts(exp2data)
  # Compute scale factors for each set of num_states experiments
  states2scales = {}
  for (num_states, instr_type, fs_opt), runtimes in exp2rts.items():
    if instr_type == INSTR_TYPE_BASELINE and fs_opt is False:
      scale_factor = np.median(runtimes)
      states2scales[num_states] = scale_factor
  # Build the dataframe for plotting
  for (num_states, instr_type, fs_opt), runtimes in exp2rts.items():
    runtimes = list(map(lambda x: x / states2scales[num_states], runtimes))
    runtimes_dict[NUM_STATES_LABEL].extend([num_states] * len(runtimes))
    runtimes_dict[INSTR_TYPE_LABEL].extend([INSTR_TYPE_MAPPINGS[instr_type]] *
                                           len(runtimes))
    runtimes_dict[RUN_TIME_LABEL].extend(runtimes)
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(runtimes_dict)


def _aggregrate_fs_opt_rts(exp2data):
  exp2rts = {}
  for exp_name, fd_list in exp2data.items():
    if fd_list[0].instr_type == "full":
      runtimes = []
      for trial in TRIALS:
        fd = fd_list[trial]
        runtimes.append(fd.runtime)
      runtimes = _drop_outliers_in_range(runtimes)
      exp2rts[(fd.num_states, fd.instr_type, fd.fs_opt)] = runtimes
  return exp2rts


def build_fs_opt_rts_df(exp2data):
  print(yellow("Building fork server optimization dataframe ..."))
  FS_OPT_BASELINE = False
  # Create empty dictionary that will be used to create Pandas
  # a DataFrame that look like the following:
  # +----------------------------------------------------+
  # | # states | fork server optimization? | runtime (s) |
  # +----------------------------------------------------+
  # |   ...    |            ...            |     ...     |
  runtimes_dict = {
      NUM_STATES_LABEL: [],
      OPT_TYPE_LABEL: [],
      RUN_TIME_LABEL: [],
  }
  # Aggregate data into a dictionary
  exp2rts = _aggregrate_fs_opt_rts(exp2data)
  # Compute scale factors for each set of num_states experiments
  states2scales = {}
  for (num_states, instr_type, fs_opt), runtimes in exp2rts.items():
    if instr_type == "full" and fs_opt is FS_OPT_BASELINE:
      scale_factor = np.median(runtimes)
      states2scales[num_states] = scale_factor
  # Build the dataframe for plotting
  for (num_states, instr_type, fs_opt), runtimes in exp2rts.items():
    runtimes = list(map(lambda x: x / states2scales[num_states], runtimes))
    runtimes_dict[NUM_STATES_LABEL].extend([num_states] * len(runtimes))
    runtimes_dict[OPT_TYPE_LABEL].extend([OPT_TYPE_MAPPINGS[fs_opt]] *
                                         len(runtimes))
    runtimes_dict[RUN_TIME_LABEL].extend(runtimes)
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(runtimes_dict)


def load_fuzzing_data(data_root):
  print(yellow("Loading data ..."))
  exp2data = collections.defaultdict(list)

  # TODO: change this to automatically extract names from a single exp. number
  # extract each data file into a Pandas dataframe
  exp_combos = list(itertools.product(STATES, WIDTHS, EXP_BASE_NAMES))
  for num_states, width, exp_base_name in exp_combos:
    for trial in TRIALS:
      # Build complete path to data files
      exp_name_wo_trialnum = exp_base_name % (num_states, width)
      exp_name = "%s-%d" % (exp_name_wo_trialnum, trial)
      data_path = os.path.join(data_root, exp_name)

      # Extract experiment info.
      exp_name_list = exp_name.split("-")
      instr_type = exp_name_list[6]
      if len(exp_name_list) > 9:
        fs_opt = True
      else:
        fs_opt = False

      # Load fuzzing data into an object
      exp2data[exp_name_wo_trialnum].append(
          FuzzingData(num_states, width, instr_type, fs_opt, trial, data_path))
  print(green("Done."))
  print(LINE_SEP)
  return exp2data


def normalize_instr_type_runtimes(df, zscore_threshold=3):
  print(yellow("Normalizing instrumentation complexity data ..."))
  # Parameters
  INSTR_TYPE_BASELINE = INSTR_TYPE_MAPPINGS["full"]

  for num_states in STATES:
    for instr_type in INSTR_TYPE_MAPPINGS.values():
      if instr_type != INSTR_TYPE_BASELINE:
        continue

      # extract only data with specific number of states and instr_type
      mean = df[(df[NUM_STATES_LABEL] == num_states) &
                (df[INSTR_TYPE_LABEL] == instr_type)].mean()
      # drop outliers
      # sub_df = sub_df[np.abs(stats.zscore(sub_df[RUN_TIME_LABEL].astype(
      # float))) < zscore_threshold]
      for it in INSTR_TYPE_MAPPINGS.values():
        df["relative"] = df.apply(lambda row: (row[RUN_TIME_LABEL] / mean)
                                  if ((row[NUM_STATES_LABEL] == num_states) and
                                      (row[INSTR_TYPE_LABEL] == it)) else None,
                                  axis=1)
  print(green("Done."))
  print(LINE_SEP)


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


def compute_instr_type_mann_whitney(cleaned_df, zscore_threshold=3):
  print(
      yellow(
          "Computing Mann-Whitney U-test on instrumentation complexity data ..."
      ))
  # Parameters
  FS_OPT_BASELINE = OPT_TYPE_MAPPINGS[False]
  # extract only instrumentation only data from dataframe
  cleaned_df = cleaned_df.loc[cleaned_df[OPT_TYPE_LABEL] == FS_OPT_BASELINE, :]
  # drop outliers
  # cleaned_df = pd.DataFrame(columns=runtimes_df.columns)
  # for num_states in STATES:
  # sub_rt_df = runtimes_df[runtimes_df[NUM_STATES_LABEL] == num_states].copy()
  # for instr_type in INSTR_TYPE_MAPPINGS.values():
  # sub_sub_rt_df = sub_rt_df[sub_rt_df[INSTR_TYPE_LABEL] ==
  # instr_type].copy()
  # sub_sub_rt_df = sub_sub_rt_df[
  # np.abs(stats.zscore(sub_sub_rt_df[RUN_TIME_LABEL].astype(
  # float))) < zscore_threshold]
  # cleaned_df = cleaned_df.append(sub_sub_rt_df, ignore_index=True)
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


def plot_opt_strategies(instr_rts, fsopt_rts):
  print(yellow("Generating plots ..."))
  sns.set()
  fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 4))
  sns.stripplot(x=NUM_STATES_LABEL,
                y=RUN_TIME_LABEL,
                hue=INSTR_TYPE_LABEL,
                data=instr_rts,
                dodge=True,
                jitter=0.2,
                size=MARKER_SIZE,
                ax=ax1)
  ax1.axhline(y=1.0, color='r', linestyle='-')
  sns.stripplot(x=NUM_STATES_LABEL,
                y=RUN_TIME_LABEL,
                hue=OPT_TYPE_LABEL,
                data=fsopt_rts,
                dodge=True,
                jitter=0.2,
                size=MARKER_SIZE,
                ax=ax2)
  ax2.axhline(y=1.0, color='r', linestyle='-')
  print(green("Done."))
  print(LINE_SEP)
  plt.show()


def main(argv):
  parser = argparse.ArgumentParser(description="Plotting script for exp. 004.")
  parser.add_argument("data_root")
  args = parser.parse_args()

  # Load runtime data
  exp2data = load_fuzzing_data(args.data_root)
  instr_rts = build_instr_complex_rts_df(exp2data)
  fsopt_rts = build_fs_opt_rts_df(exp2data)

  # Compute stats
  # compute_instr_type_mann_whitney(runtimes_df,
  # zscore_threshold=ZSCORE_THRESHOLD)

  # Plot the data
  plot_opt_strategies(instr_rts, fsopt_rts)


if __name__ == "__main__":
  main(sys.argv[1:])

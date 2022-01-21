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

import matplotlib as mpl
import matplotlib.pyplot as plt

import pandas as pd
import seaborn as sns
from hwfutils.string_color import color_str_green as green
from hwfutils.string_color import color_str_red as red
from hwfutils.string_color import color_str_yellow as yellow

# from scipy import stats

# ------------------------------------------------------------------------------
# Plot parameters
# ------------------------------------------------------------------------------
LABEL_FONT_SIZE = 8
TICK_FONT_SIZE = 8
LEGEND_FONT_SIZE = 8
LEGEND_TITLE_FONT_SIZE = 8
TIME_SCALE = "m"
SCALED_MAX_PLOT_TIME = 60
PLOT_FILE_NAME = "hwf_no_seeds_with_alert_handler.pdf"
PLOT_FORMAT = "PDF"

# ------------------------------------------------------------------------------
# Plot labels
# ------------------------------------------------------------------------------
TIME_LABEL = "Time"
TOPLEVEL_LABEL = "Core"
GRAMMAR_LABEL = "Grammar"
COVERAGE_TYPE_LABEL = "Coverage"
COVERAGE_LABEL = "Cov. (%)"
HW_LINE_COVERAGE_LABEL = "HW Line (VLT)"
SW_LINE_COVERAGE_LABEL = "SW Line (kcov)"
SW_REGION_COVERAGE_LABEL = "SW Basic Block (LLVM)"

# ------------------------------------------------------------------------------
# Other Labels
# ------------------------------------------------------------------------------
AFL_TEST_ID_LABEL = "Test-ID"

# ------------------------------------------------------------------------------
# Experiment Parameters
# ------------------------------------------------------------------------------
EXPERIMENT_BASE_NAME = "exp014-cpp-afl-%s-%s-%s-%s"
TOPLEVELS = ["aes", "alert_handler", "hmac", "kmac", "rv_timer"]
OPCODE_TYPES = ["mapped"]
INSTR_TYPES = ["variable"]
TERMINATE_TYPES = ["never"]
TRIALS = range(0, 5)

# ------------------------------------------------------------------------------
# Other defines
# ------------------------------------------------------------------------------
TERMINAL_ROWS, TERMINAL_COLS = os.popen('stty size', 'r').read().split()
LINE_SEP = "=" * int(TERMINAL_COLS)

COUNT = 0


@dataclass
class SubplotAxisLimits:
  x_lower: int = None
  x_upper: int = None
  y_lower: int = None
  y_upper: int = None


@dataclass
class FigureAxisLimits:
  kcov_limits: SubplotAxisLimits
  llvm_cov_limits: SubplotAxisLimits
  vlt_cov_limits: SubplotAxisLimits


@dataclass
class FuzzingData:
  toplevel: str = ""
  opcode_type: str = ""
  instr_type: str = ""
  terminate_type: str = ""
  trial_num: int = -1
  afl_data_path: str = ""
  cov_data_path: str = ""

  def __post_init__(self):
    self.afl_data = self._load_afl_data()
    self.kcov_data = self._load_cov_data("kcov")
    self.llvm_cov_data = self._load_cov_data("llvm_cov")
    self.vlt_cov_data = self._load_cov_data("vlt_cov")

  def _load_afl_data(self):
    afl_glob_path = os.path.join(self.afl_data_path, "out",
                                 "afl_*_interactive", "plot_data")
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
    # Set time as index
    afl_df = afl_df.set_index("# unix_time")
    return afl_df

  @staticmethod
  def _id_str_to_int(id_str):
    return int(id_str.lstrip("id:"))

  def _load_cov_data(self, cov_type):
    cov_data_path = "%s/logs/%s_cum.csv" % (self.cov_data_path, cov_type)
    if not os.path.exists(cov_data_path):
      print(red("ERROR: coverage data (%s) does not exist." % cov_data_path))
      sys.exit(1)
    # Load data into Pandas DataFrame
    cov_df = self._load_csv_data(cov_data_path)
    if cov_df.shape[0] < int(self.afl_data.iloc[-1, 2]):
      print(red("ERROR: coverage data is missing (%s). Aborting!" % cov_type))
      sys.exit(1)
    # TODO(ttrippel): remove this hack after fixing run_cov_local.sh
    if cov_type == "vlt_cov":
      cov_df.drop(AFL_TEST_ID_LABEL, axis=1, inplace=True)
      cov_df.insert(0, AFL_TEST_ID_LABEL, list(range(cov_df.shape[0])))
    else:
      # Convert Test-ID labels to ints
      cov_df.loc[:,
                 AFL_TEST_ID_LABEL] = cov_df.loc[:, AFL_TEST_ID_LABEL].apply(
                     FuzzingData._id_str_to_int)
    # Set ID column as the row indicies
    cov_df = cov_df.set_index(AFL_TEST_ID_LABEL)
    return cov_df

  def _load_csv_data(self, csv_file):
    return pd.read_csv(csv_file,
                       delimiter=',',
                       index_col=None,
                       engine='python')

  @property
  def grammar(self):
    return "%s-%s-%s" % (self.opcode_type, self.instr_type,
                         self.terminate_type)


def get_paths_total_at_time(time, afl_data):
  while time not in afl_data.index:
    time -= 1
  return afl_data.loc[time, "paths_total"]


def get_cov_at_time(paths_total, cov_data, cov_data_key):
  return cov_data.loc[paths_total, cov_data_key] * 100.0


def get_vlt_cov_at_time(paths_total, vlt_cov_data):
  vlt_cov = (float(vlt_cov_data.loc[paths_total, "Lines-Covered"]) /
             float(vlt_cov_data.loc[paths_total, "Total-Lines"])) * 100.0
  return vlt_cov


def build_avg_coverage_df(exp2data,
                          time_units="m",
                          normalize_to_start=False,
                          consolidation="max"):
  print(yellow("Building average coverage dataframe ..."))
  # Create empty dictionary that will be used to create a Pandas DataFrame that
  # looks like the following:
  # +--------------------------------------------------------------------+
  # | toplevel | isa (grammar) | coverage type | time (s) | coverage (%) |
  # +--------------------------------------------------------------------+
  # |   ...    |        ...    |      ...      |   ...    |      ...     |
  coverage_dict = {
      TOPLEVEL_LABEL: [],
      GRAMMAR_LABEL: [],
      COVERAGE_TYPE_LABEL: [],
      TIME_LABEL: [],
      COVERAGE_LABEL: [],
  }
  for exp_name, fd_list in exp2data.items():
    anchor_fd = fd_list[0]
    for time, row in anchor_fd.afl_data.iterrows():
      # scale time
      if time_units == "h":
        scaled_time = float(time) / float(3600)
      elif time_units == "m":
        scaled_time = float(time) / float(60)
      else:
        scaled_time = time
      # add circuit, grammar, and time values to dataframe row
      for _ in range(3):
        coverage_dict[TOPLEVEL_LABEL].append(anchor_fd.toplevel)
        coverage_dict[GRAMMAR_LABEL].append(anchor_fd.grammar)
        coverage_dict[TIME_LABEL].append(scaled_time)
      # compute average coverage at all points in time
      kcov_avg = 0
      llvm_cov_avg = 0
      vlt_cov_avg = 0
      kcov_max = 0
      llvm_cov_max = 0
      vlt_cov_max = 0
      i = 0
      for fd in fd_list:
        # get the paths_total at the current time
        paths_total = get_paths_total_at_time(time, fd.afl_data) - 1
        # get coverage data
        # print(exp_name, i)
        kcov = get_cov_at_time(paths_total, fd.kcov_data, "Line-Coverage-(%)")
        kcov_avg += kcov
        kcov_max = max(kcov_max, kcov)
        llvm_cov = get_cov_at_time(paths_total, fd.llvm_cov_data,
                                   "Region-Coverage-(%)")
        llvm_cov_avg += llvm_cov
        llvm_cov_max = max(llvm_cov_max, llvm_cov)
        vlt_cov = get_vlt_cov_at_time(paths_total, fd.vlt_cov_data)
        vlt_cov_avg += vlt_cov
        vlt_cov_max = max(vlt_cov_max, vlt_cov)
        i += 1
      kcov_avg /= float(len(fd_list))
      llvm_cov_avg /= float(len(fd_list))
      vlt_cov_avg /= float(len(fd_list))
      # save time 0 coverage to normalize
      if time == 0:
        kcov_avg_t0 = kcov_avg
        llvm_cov_avg_t0 = llvm_cov_avg
        vlt_cov_avg_t0 = vlt_cov_avg
      if normalize_to_start:
        kcov_avg /= kcov_avg_t0
        llvm_cov_avg /= llvm_cov_avg_t0
        vlt_cov_avg /= vlt_cov_avg_t0
      coverage_dict[COVERAGE_TYPE_LABEL].append(SW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_TYPE_LABEL].append(SW_REGION_COVERAGE_LABEL)
      coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
      if consolidation == "avg":
        coverage_dict[COVERAGE_LABEL].append(kcov_avg)
        coverage_dict[COVERAGE_LABEL].append(llvm_cov_avg)
        coverage_dict[COVERAGE_LABEL].append(vlt_cov_avg)
      else:
        coverage_dict[COVERAGE_LABEL].append(kcov_max)
        coverage_dict[COVERAGE_LABEL].append(llvm_cov_max)
        coverage_dict[COVERAGE_LABEL].append(vlt_cov_max)
    # extend lines to max time value
    if coverage_dict[TIME_LABEL][-1] != SCALED_MAX_PLOT_TIME:
      for _ in range(3):
        coverage_dict[TOPLEVEL_LABEL].append(anchor_fd.toplevel)
        coverage_dict[GRAMMAR_LABEL].append(anchor_fd.grammar)
        coverage_dict[TIME_LABEL].append(SCALED_MAX_PLOT_TIME)
    coverage_dict[COVERAGE_TYPE_LABEL].append(SW_LINE_COVERAGE_LABEL)
    coverage_dict[COVERAGE_TYPE_LABEL].append(SW_REGION_COVERAGE_LABEL)
    coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
    coverage_dict[COVERAGE_LABEL].extend(coverage_dict[COVERAGE_LABEL][-3:])
    # print("Max SW Line coverage:       ", coverage_dict[COVERAGE_LABEL][-3])
    # print("Max SW Basic Block coverage:", coverage_dict[COVERAGE_LABEL][-2])
    print("Max HW Line coverage:       ", coverage_dict[COVERAGE_LABEL][-1])
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(coverage_dict)


def load_fuzzing_data(afl_data_root, cov_data_root):
  print(yellow("Loading data ..."))
  exp2data = collections.defaultdict(list)
  # TODO: change this to automatically extract names from a single exp. number
  # extract each data file into a Pandas dataframe
  isas = list(
      itertools.product(TOPLEVELS, OPCODE_TYPES, INSTR_TYPES, TERMINATE_TYPES))
  for toplevel, opcode_type, instr_type, terminate_type in isas:
    # TODO: remove this special case for the alert handler since it only seems
    # to run locally right now and not on GCP.
    if toplevel == "alert_handler":
      # Build complete path to data files
      exp_name = "exp014-cpp-afl-alert-handler-constant-variable-never-0"
      afl_data_path = os.path.join(afl_data_root, exp_name)
      cov_data_path = os.path.join(cov_data_root, exp_name)
      # Load fuzzing data into an object
      exp2data[exp_name].append(
          FuzzingData(toplevel, "constant", "variable", "never", 0,
                      afl_data_path, cov_data_path))
    else:
      for trial in TRIALS:
        # Build complete path to data files
        exp_name_wo_trialnum = EXPERIMENT_BASE_NAME % (
            toplevel, opcode_type, instr_type, terminate_type)
        exp_name_wo_trialnum = exp_name_wo_trialnum.replace("_", "-")
        exp_name = "%s-%d" % (exp_name_wo_trialnum, trial)
        afl_data_path = os.path.join(afl_data_root, exp_name)
        cov_data_path = os.path.join(cov_data_root, exp_name)
        # Load fuzzing data into an object
        exp2data[exp_name_wo_trialnum].append(
            FuzzingData(toplevel, opcode_type, instr_type, terminate_type,
                        trial, afl_data_path, cov_data_path))
  return exp2data


def plot_avg_coverage_vs_time(cov_df, time_units="m"):
  print(yellow("Generating plot ..."))

  # Set plot style and extract only HDL line coverage
  sns.set_theme(context="notebook", style="darkgrid")
  hdl_cov_df = cov_df[cov_df[COVERAGE_TYPE_LABEL] == HW_LINE_COVERAGE_LABEL]

  # create figure and plot the data
  fig, ax = plt.subplots(1, 1, figsize=(4, 2))
  sns.lineplot(data=hdl_cov_df,
               x=TIME_LABEL,
               y=COVERAGE_LABEL,
               hue=TOPLEVEL_LABEL,
               ax=ax,
               markers="x")

  # format the plot
  if time_units == "m":
    time_units_label = "min."
  elif time_units == "h":
    time_units_label = "hours"
  else:
    time_units_label = "s"
  ax.set_xlabel(TIME_LABEL + " (%s)" % time_units_label,
                fontsize=LABEL_FONT_SIZE)
  ax.set_ylabel("HDL Line " + COVERAGE_LABEL, fontsize=LABEL_FONT_SIZE)
  ax.tick_params("x", labelsize=TICK_FONT_SIZE)
  ax.tick_params("y", labelsize=TICK_FONT_SIZE)
  plt.legend(title="Core",
             fontsize=LEGEND_FONT_SIZE,
             title_fontsize=LEGEND_TITLE_FONT_SIZE,
             ncol=2)
  plt.tight_layout()

  # save the plot
  plt.savefig(PLOT_FILE_NAME, format=PLOT_FORMAT)
  print(green("Done."))
  print(LINE_SEP)


def main(argv):
  parser = argparse.ArgumentParser(description="Plotting script for exp. 004.")
  parser.add_argument("afl_data_root")
  parser.add_argument("cov_data_root")
  args = parser.parse_args()

  # Load runtime data
  exp2data = load_fuzzing_data(args.afl_data_root, args.cov_data_root)
  avg_cov_df = build_avg_coverage_df(exp2data,
                                     time_units=TIME_SCALE,
                                     normalize_to_start=False)

  # Plot data
  plot_avg_coverage_vs_time(avg_cov_df, time_units=TIME_SCALE)


if __name__ == "__main__":
  main(sys.argv[1:])

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
# TIME_SCALE = "m"
TIME_SCALE = "h"
# SCALED_MAX_PLOT_TIME = 60
SCALED_MAX_PLOT_TIME = 24
# PLOT_FILE_NAME = "hwf_grammar_cov_1hour_10trials_avg.pdf"
PLOT_FILE_NAME = "hwf_grammar_cov_24hours_10trials_avg_wline.pdf"
PLOT_FORMAT = "pdf"

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
# EXPERIMENT_BASE_NAME = "exp010-cpp-afl-%s-%s-%s-%s"
# EXPERIMENT_BASE_NAME = "exp011-cpp-afl-%s-%s-%s-%s"
# EXPERIMENT_BASE_NAME = "exp012-cpp-afl-%s-%s-%s-%s"
EXPERIMENT_BASE_NAME = "exp013-cpp-afl-%s-%s-%s-%s"
TOPLEVELS = ["aes", "hmac", "kmac", "rv_timer"]
OPCODE_TYPES = ["constant", "mapped"]
INSTR_TYPES = ["variable", "fixed"]
# TERMINATE_TYPES = ["invalidop", "never"]
TERMINATE_TYPES = ["never"]
TRIALS = range(0, 10)

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
      # return None
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
                          consolidation="avg"):
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
      for fd in fd_list:
        # get the paths_total at the current time
        paths_total = get_paths_total_at_time(time, fd.afl_data) - 1
        # get coverage data
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
      kcov_avg /= float(len(fd_list))
      llvm_cov_avg /= float(len(fd_list))
      vlt_cov_avg /= float(len(fd_list))
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
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(coverage_dict)


def build_coverage_df(exp2data, trial):
  print(yellow("Building coverage dataframe ..."))
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

  # Add rows to the dataframe
  for exp_name, fd_list in exp2data.items():
    fd = fd_list[trial]
    for time, row in fd.afl_data.iterrows():
      cov_df_idx = row["paths_total"] - 1
      for _ in range(3):
        coverage_dict[TOPLEVEL_LABEL].append(fd.toplevel)
        coverage_dict[GRAMMAR_LABEL].append(fd.grammar)
        coverage_dict[TIME_LABEL].append(time)

      # Add kcov coverage
      kcov = fd.kcov_data.loc[cov_df_idx, "Line-Coverage-(%)"]
      coverage_dict[COVERAGE_TYPE_LABEL].append(SW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(kcov * 100.0)

      # Add LLVM coverage
      llvm_cov = fd.llvm_cov_data.loc[cov_df_idx, "Region-Coverage-(%)"]
      coverage_dict[COVERAGE_TYPE_LABEL].append(SW_REGION_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(llvm_cov * 100.0)

      # Add Verilator coverage
      vlt_cov = (float(fd.vlt_cov_data.loc[cov_df_idx, "Lines-Covered"]) /
                 float(fd.vlt_cov_data.loc[cov_df_idx, "Total-Lines"]))
      coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(vlt_cov * 100.0)

  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(coverage_dict)


def build_coverage_dfs(exp2data):
  coverage_dfs = []
  for trial in TRIALS:
    coverage_dfs.append(build_coverage_df(exp2data, trial))
  return coverage_dfs


def load_fuzzing_data(afl_data_root, cov_data_root):
  print(yellow("Loading data ..."))
  exp2data = collections.defaultdict(list)
  # TODO: change this to automatically extract names from a single exp. number
  # extract each data file into a Pandas dataframe
  isas = list(
      itertools.product(TOPLEVELS, OPCODE_TYPES, INSTR_TYPES, TERMINATE_TYPES))
  for toplevel, opcode_type, instr_type, terminate_type in isas:
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
          FuzzingData(toplevel, opcode_type, instr_type, terminate_type, trial,
                      afl_data_path, cov_data_path))
  return exp2data


def plot_coverage_vs_time(coverage_dfs):
  print(yellow("Generating plots ..."))
  cov_metrics = [
      SW_LINE_COVERAGE_LABEL, SW_REGION_COVERAGE_LABEL, HW_LINE_COVERAGE_LABEL
  ]
  num_cores = len(TOPLEVELS)
  num_cov_metrics = len(cov_metrics)
  sns.set_theme(context="notebook", style="darkgrid")
  fig, axes = plt.subplots(num_cov_metrics,
                           num_cores,
                           sharex=True,
                           sharey=True)
  for trial in range(len(coverage_dfs)):
    # Select experiment trial number
    cov_df = coverage_dfs[trial]
    for row in range(len(axes)):
      # select portion of data corresponding to current COVERAGE METRIC
      sub_cov_df = cov_df[cov_df[COVERAGE_TYPE_LABEL] == cov_metrics[row]]
      for col in range(len(axes[row])):
        # select portion of data corresponding to current core
        plt_df = sub_cov_df[sub_cov_df[TOPLEVEL_LABEL] == TOPLEVELS[col]]
        # sns.set_context("paper")
        curr_ax = sns.lineplot(data=plt_df,
                               x=TIME_LABEL,
                               y=COVERAGE_LABEL,
                               hue=GRAMMAR_LABEL,
                               ax=axes[row][col],
                               legend=False)
        if row == 0 and col == 0 and trial == 0:
          lines = curr_ax.get_lines()
        axes[row][col].set_title("Coverage = %s | Core = %s" %
                                 (cov_metrics[row], TOPLEVELS[col]))
  fig.legend(
      lines,
      [
          "Const. Opcode & Variable Frame",
          "Const. Opcode & Fixed Frame",
          "Mapped Opcode & Variable Frame",
          "Mapped Opcode & Fixed Frame",
      ],
      loc="lower center",
      ncol=4,
  )
  print(green("Done."))
  print(LINE_SEP)
  plt.show()


def _format_plot(ax, axis_limits, time_units, subplot_title):
  if axis_limits.x_lower is not None and axis_limits.x_upper is not None:
    ax.set_xlim(axis_limits.x_lower, axis_limits.x_upper)
  if axis_limits.y_lower is not None and axis_limits.y_upper is not None:
    ax.set_ylim(axis_limits.y_lower, axis_limits.y_upper)
  ax.set_title(subplot_title)
  ax.set_title(subplot_title, fontsize=LABEL_FONT_SIZE)
  if time_units == "m":
    time_units_label = "min."
  elif time_units == "h":
    time_units_label = "hours"
  else:
    time_units_label = "s"
  ax.set_xlabel(TIME_LABEL + " (%s)" % time_units_label,
                fontsize=LABEL_FONT_SIZE)
  ax.set_ylabel(COVERAGE_LABEL, fontsize=LABEL_FONT_SIZE)
  ax.tick_params("x", labelsize=TICK_FONT_SIZE)
  ax.tick_params("y", labelsize=TICK_FONT_SIZE)


def _get_legend_labels(ax):
  legend = [c for c in ax.get_children()
            if isinstance(c, mpl.legend.Legend)][0]
  labels = []
  for text in legend.get_texts():
    labels.append(text.get_text())
  ax.get_legend().remove()
  return labels


def _get_axis_limits():
  axis_limits = {}
  for toplevel in TOPLEVELS:
    axis_limits[toplevel] = FigureAxisLimits(SubplotAxisLimits(),
                                             SubplotAxisLimits(),
                                             SubplotAxisLimits())

  MIN_TIME = -2
  MAX_TIME = SCALED_MAX_PLOT_TIME

  # ------------------------------------------------
  # AES axis limits
  # ------------------------------------------------
  # axis_limits["aes"].kcov_limits = SubplotAxisLimits(MIN_TIME, MAX_TIME, 89,
  # 91)
  # axis_limits["aes"].llvm_cov_limits = SubplotAxisLimits(
  # MIN_TIME, MAX_TIME, 58, 63)
  # axis_limits["aes"].vlt_cov_limits = SubplotAxisLimits(
  # MIN_TIME, MAX_TIME, 80, 90)
  # ------------------------------------------------
  axis_limits["aes"].kcov_limits = SubplotAxisLimits(MIN_TIME, MAX_TIME, 89,
                                                     91)
  axis_limits["aes"].llvm_cov_limits = SubplotAxisLimits(
      MIN_TIME, MAX_TIME, 58, 63)
  axis_limits["aes"].vlt_cov_limits = SubplotAxisLimits(
      MIN_TIME, MAX_TIME, 81, 91)
  # ------------------------------------------------

  # ------------------------------------------------
  # HMAC axis limits
  # ------------------------------------------------
  # axis_limits["hmac"].kcov_limits = SubplotAxisLimits(MIN_TIME, MAX_TIME, 85,
  # 89)
  # axis_limits["hmac"].llvm_cov_limits = SubplotAxisLimits(
  # MIN_TIME, MAX_TIME, 63, 68)
  # axis_limits["hmac"].vlt_cov_limits = SubplotAxisLimits(
  # MIN_TIME, MAX_TIME, 61, 95)
  # ------------------------------------------------
  axis_limits["hmac"].kcov_limits = SubplotAxisLimits(MIN_TIME, MAX_TIME, 85,
                                                      89)
  axis_limits["hmac"].llvm_cov_limits = SubplotAxisLimits(
      MIN_TIME, MAX_TIME, 63, 68)
  axis_limits["hmac"].vlt_cov_limits = SubplotAxisLimits(
      MIN_TIME, MAX_TIME, 60, 95)
  # ------------------------------------------------

  # ------------------------------------------------
  # KMAC axis limits
  # ------------------------------------------------
  # axis_limits["kmac"].kcov_limits = SubplotAxisLimits(MIN_TIME, MAX_TIME, 94,
  # 96)
  # axis_limits["kmac"].llvm_cov_limits = SubplotAxisLimits(
  # MIN_TIME, MAX_TIME, 67, 70)
  # axis_limits["kmac"].vlt_cov_limits = SubplotAxisLimits(
  # MIN_TIME, MAX_TIME, 50, 85)
  # ------------------------------------------------
  axis_limits["kmac"].kcov_limits = SubplotAxisLimits(MIN_TIME, MAX_TIME, 94,
                                                      96)
  # ------------------------------------------------

  # ------------------------------------------------
  # RV-Timer axis limits
  # ------------------------------------------------
  # RV_TIMER_START_TIME = -0.1
  # RV_TIMER_END_TIME = 3
  # axis_limits["rv_timer"].kcov_limits = SubplotAxisLimits(RV_TIMER_START_TIME, RV_TIMER_END_TIME, 80, 90)
  # axis_limits["rv_timer"].llvm_cov_limits = SubplotAxisLimits(RV_TIMER_START_TIME, RV_TIMER_END_TIME, 63, 73)
  # axis_limits["rv_timer"].vlt_cov_limits = SubplotAxisLimits(RV_TIMER_START_TIME, RV_TIMER_END_TIME, 10, 88)
  # ------------------------------------------------
  RV_TIMER_START_TIME = -0.01
  RV_TIMER_END_TIME = 0.1
  axis_limits["rv_timer"].kcov_limits = SubplotAxisLimits(
      RV_TIMER_START_TIME, RV_TIMER_END_TIME, 81, 90)
  axis_limits["rv_timer"].llvm_cov_limits = SubplotAxisLimits(
      RV_TIMER_START_TIME, RV_TIMER_END_TIME, 63, 74)
  axis_limits["rv_timer"].vlt_cov_limits = SubplotAxisLimits(
      RV_TIMER_START_TIME, RV_TIMER_END_TIME, 10, 95)
  # ------------------------------------------------
  return axis_limits


def plot_avg_coverage_vs_time(cov_df, time_units="m"):
  print(yellow("Generating plots ..."))
  cov_metrics = [
      SW_LINE_COVERAGE_LABEL, SW_REGION_COVERAGE_LABEL, HW_LINE_COVERAGE_LABEL
  ]
  axis_limits = _get_axis_limits()
  sns.set_theme(context="notebook", style="darkgrid")

  # create figure and subplot axes
  fig, axes = plt.subplots(len(cov_metrics),
                           len(TOPLEVELS),
                           sharex="col",
                           figsize=(10, 4))

  # plot coverage traces
  for row in range(len(axes)):
    # select portion of data corresponding to current COVERAGE METRIC
    sub_cov_df = cov_df[cov_df[COVERAGE_TYPE_LABEL] == cov_metrics[row]]
    for col in range(len(axes[row])):
      # select portion of data corresponding to current core
      plt_df = sub_cov_df[sub_cov_df[TOPLEVEL_LABEL] == TOPLEVELS[col]]
      # TODO(ttrippel): there has to be a better way to do the following:
      # plot legend only for the first subplot so we can extract the labels
      if row == 0 and col == 0:
        plot_legend = True
      else:
        plot_legend = False
      ax = sns.lineplot(data=plt_df,
                        x=TIME_LABEL,
                        y=COVERAGE_LABEL,
                        hue=GRAMMAR_LABEL,
                        ax=axes[row][col],
                        legend=plot_legend)
      ax.axhline(y=1.0, color='r', linestyle='-')
      # get legend info if we are plotting the first plot
      if plot_legend:
        lines = ax.get_lines()
        labels = _get_legend_labels(ax)

  # format each figure
  for row in range(len(axes)):
    for col in range(len(axes[row])):
      # get corresponding axis_limits
      if cov_metrics[row] == SW_LINE_COVERAGE_LABEL:
        ax_lims = axis_limits[TOPLEVELS[col]].kcov_limits
      elif cov_metrics[row] == SW_REGION_COVERAGE_LABEL:
        ax_lims = axis_limits[TOPLEVELS[col]].llvm_cov_limits
      else:
        ax_lims = axis_limits[TOPLEVELS[col]].vlt_cov_limits
      # format plot labels and axes
      subplot_title = "%s | %s" % (TOPLEVELS[col], cov_metrics[row])
      _format_plot(axes[row][col], ax_lims, time_units, subplot_title)
  plt.tight_layout()

  # set legend
  # isa_label_mapping = {
  # "constant-variable-never": "Const. Opcode | Variable Frame",
  # "constant-fixed-never": "Const. Opcode | Fixed Frame",
  # "mapped-variable-never": "Mapped Opcode | Variable Frame",
  # "mapped-fixed-never": "Mapped Opcode | Fixed Frame",
  # }
  isa_label_mapping = {
      "constant-variable-never": "Constant | Variable",
      "constant-fixed-never": "Constant | Fixed",
      "mapped-variable-never": "Mapped | Variable",
      "mapped-fixed-never": "Mapped | Fixed",
  }
  clean_labels = [isa_label_mapping[isa_label] for isa_label in labels]
  fig.legend(lines,
             clean_labels,
             fontsize=LEGEND_FONT_SIZE,
             title_fontsize=LEGEND_TITLE_FONT_SIZE,
             loc="upper center",
             ncol=4,
             borderaxespad=0.05,
             bbox_to_anchor=(0.5, 0.12),
             title=GRAMMAR_LABEL + " (Opcode Format | Frame Format)")
  plt.subplots_adjust(bottom=0.23, wspace=0.25, hspace=0.25)

  # adjust figure layout and save to file
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
  # coverage_dfs = build_coverage_dfs(exp2data)
  # print("Dumping to CSV ...")
  # avg_cov_df.to_csv("temp.csv", index=False)
  # print("Reading from CSV ...")
  # avg_cov_df = pd.read_csv("temp.csv",
  # delimiter=',',
  # index_col=None,
  # engine='python')

  # Plot data
  plot_avg_coverage_vs_time(avg_cov_df, time_units=TIME_SCALE)
  # plot_coverage_vs_time(coverage_dfs)


if __name__ == "__main__":
  main(sys.argv[1:])

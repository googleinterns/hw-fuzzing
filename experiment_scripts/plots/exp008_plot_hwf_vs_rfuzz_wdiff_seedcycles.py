#!/usr/bin/env python3
# Copyright 2021 Timothy Trippel
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
import json
import os
import sys
from dataclasses import dataclass

import matplotlib
import matplotlib.pyplot as plt

import pandas as pd
import seaborn as sns
from hwfutils.string_color import color_str_green as green
from hwfutils.string_color import color_str_red as red
from hwfutils.string_color import color_str_yellow as yellow
from scipy import stats

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

# ------------------------------------------------------------------------------
# Experiment Parameters
# ------------------------------------------------------------------------------
EXPERIMENT_SUFFIX = "%s-%sm-%dseedcycles"
DURATION_MINS = 1440
# DURATION_MINS = 60
# TOPLEVELS = ["Sodor1Stage", "Sodor5Stage"]
TOPLEVELS = [
    "FFTSmall", "Sodor1Stage", "Sodor3Stage", "Sodor5Stage", "TLI2C", "TLPWM",
    "TLSPI", "TLUART"
]
# NUM_SEED_CYCLES = range(1, 6)
NUM_SEED_CYCLES = [1, 3, 5]
# TRIALS = range(0, 4)
TRIALS = [0, 2, 3]
# TRIALS = range(0, 10)

# ------------------------------------------------------------------------------
# Plot parameters
# ------------------------------------------------------------------------------
LABEL_FONT_SIZE = 8
TICK_FONT_SIZE = 8
LEGEND_FONT_SIZE = 8
LEGEND_TITLE_FONT_SIZE = 8
TIME_SCALE = "h"
SCALED_MAX_PLOT_TIME = 24
PLOT_FORMAT = "PDF"
PLOT_FILE_NAME = "hwf_vs_rfuzz_wdiff_seeds_%dmin.%s" % (DURATION_MINS,
                                                        PLOT_FORMAT.lower())

# ------------------------------------------------------------------------------
# Plot labels
# ------------------------------------------------------------------------------
TIME_LABEL = "Time"
TOPLEVEL_LABEL = "Core"
SEED_CYCLES_LABEL = "Seed Cycles"
FUZZER_LABEL = "Fuzzer"
COVERAGE_TYPE_LABEL = "Coverage"
COVERAGE_LABEL = "HDL Line Cov. (%)"
HW_LINE_COVERAGE_LABEL = "HW Line (VLT)"

# ------------------------------------------------------------------------------
# Other Labels
# ------------------------------------------------------------------------------
TEST_ID_LABEL = "Test-ID"

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
  duration_mins: int = -1
  seed_cycles: int = -1
  trial_num: int = -1
  hwf_data_path: str = ""
  rfuzz_data_path: str = ""

  def __post_init__(self):
    self.hwf_afl_data = self._load_afl_data(self.hwf_data_path)
    self.rfuzz_data = self._load_rfuzz_data(self.rfuzz_data_path)
    self.hwf_cov_data = self._load_hwf_vlt_cov_data("%s/logs/vlt_cov_cum.csv" %
                                                    self.hwf_data_path)
    self.rfuzz_cov_data = self._load_rfuzz_vlt_cov_data("%s/vlt_cum_cov.csv" %
                                                        self.rfuzz_data_path)

  def _load_afl_data(self, data_path):
    afl_glob_path = os.path.join(data_path, "out", "afl_*_interactive",
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
    # Set time as index
    afl_df = afl_df.set_index("# unix_time")
    return afl_df

  def _load_rfuzz_data(self, data_path):
    rfuzz_entries = sorted(glob.glob("%s/entry_*.json" % data_path))
    rfuzz_data_dict = collections.defaultdict(list)
    # encountered_issues = False
    for entry in rfuzz_entries:
      with open(entry, "r") as ef:
        try:
          entry_dict = json.load(ef)
        except json.JSONDecodeError:
          print(red("ERROR: RFUZZ coverage data (%s) does not exist." % entry))
          sys.exit(1)
          # encountered_issues = True
          # continue
      entry_id = entry_dict["entry"]["id"]
      discovery_time = entry_dict["entry"]["discovered_after"]
      rfuzz_data_dict[TEST_ID_LABEL].append(entry_id)
      rfuzz_data_dict["Time (s)"].append(
          FuzzingData._disco_time_dict_to_secs(discovery_time))
    # if encountered_issues:
    # print(rfuzz_data_dict)
    # exit()
    rfuzz_df = pd.DataFrame.from_dict(rfuzz_data_dict)
    rfuzz_df = rfuzz_df.set_index(TEST_ID_LABEL)
    return rfuzz_df

  @staticmethod
  def _disco_time_dict_to_secs(disco_time_dict):
    seconds = disco_time_dict["secs"]
    nanoseconds = disco_time_dict["nanos"]
    seconds += float(nanoseconds) / float(1e9)
    return seconds

  @staticmethod
  def _id_str_to_int(id_str):
    return int(id_str.lstrip("id:"))

  def _load_hwf_vlt_cov_data(self, cov_data_path):
    if not os.path.exists(cov_data_path):
      print(red("ERROR: coverage data (%s) does not exist." % cov_data_path))
      sys.exit(1)
    # Load data into Pandas DataFrame
    cov_df = self._load_csv_data(cov_data_path)
    if cov_df.shape[0] < int(self.hwf_afl_data.iloc[-1, 2]):
      # print(cov_df.shape[0], int(self.hwf_afl_data.iloc[-1, 2]))
      print(
          red("WARNING: some coverage data is missing for %s" % cov_data_path))
    # Convert Test-ID labels to ints
    cov_df.loc[:, TEST_ID_LABEL] = cov_df.loc[:, TEST_ID_LABEL].apply(
        FuzzingData._id_str_to_int)
    # Set ID column as the row indicies
    cov_df = cov_df.set_index(TEST_ID_LABEL)
    return cov_df

  def _load_rfuzz_vlt_cov_data(self, cov_data_path):
    if not os.path.exists(cov_data_path):
      print(red("ERROR: coverage data (%s) does not exist." % cov_data_path))
      sys.exit(1)
    # Load data into Pandas DataFrame
    cov_df = self._load_csv_data(cov_data_path)
    # Check dimensions match, i.e., no data is missing
    if cov_df.shape[0] != self.rfuzz_data.shape[0]:
      print(red("ERROR: coverage data is missing. Aborting!"))
      sys.exit(1)
    # Set ID column as the row indicies
    cov_df = cov_df.set_index(TEST_ID_LABEL)
    return cov_df

  def _load_csv_data(self, csv_file):
    return pd.read_csv(csv_file,
                       delimiter=',',
                       index_col=None,
                       engine='python')


def get_paths_total_at_time(time, afl_data):
  while time not in afl_data.index:
    time -= 1
  return afl_data.loc[time, "paths_total"]


def get_cov_at_time(paths_total, cov_data, cov_data_key):
  return cov_data.loc[paths_total, cov_data_key] * 100.0


def get_vlt_cov_at_time(test_id, vlt_cov_data):
  if test_id >= vlt_cov_data.shape[0]:
    last_test_id = vlt_cov_data.shape[0] - 1
    vlt_cov = (float(vlt_cov_data.loc[last_test_id, "Lines-Covered"]) /
               float(vlt_cov_data.loc[last_test_id, "Total-Lines"])) * 100.0
  else:
    vlt_cov = (float(vlt_cov_data.loc[test_id, "Lines-Covered"]) /
               float(vlt_cov_data.loc[test_id, "Total-Lines"])) * 100.0
  return vlt_cov


def get_max_vlt_cov(vlt_cov_data):
  last_test_id = vlt_cov_data.shape[0] - 1
  vlt_cov = (float(vlt_cov_data.loc[last_test_id, "Lines-Covered"]) /
             float(vlt_cov_data.loc[last_test_id, "Total-Lines"])) * 100.0
  return vlt_cov


def scale_time(time_seconds, time_units):
  if time_units == "h":
    return float(time_seconds) / float(3600)
  elif time_units == "m":
    return float(time_seconds) / float(60)
  else:
    return time_seconds


def load_fuzzing_data(hwf_exp_prefix, rfuzz_exp_prefix):
  print(yellow("Loading data ..."))
  exp2data = collections.defaultdict(list)
  for toplevel in TOPLEVELS:
    for seed_cycles in NUM_SEED_CYCLES:
      for trial in TRIALS:
        # Build complete path to data files
        exp_suffix = EXPERIMENT_SUFFIX % (toplevel.lower(), DURATION_MINS,
                                          seed_cycles)
        hwf_data_path = f"{hwf_exp_prefix}-{exp_suffix}-{trial}"
        rfuzz_data_path = f"{rfuzz_exp_prefix}/rfuzz-{exp_suffix}-{trial}"
        # Load fuzzing data into an object
        exp2data[exp_suffix].append(
            FuzzingData(toplevel, DURATION_MINS, seed_cycles, trial,
                        hwf_data_path, rfuzz_data_path))
  return exp2data


def build_max_rfuzz_coverage_df(exp2data,
                                time_units="m",
                                normalize_to_start=False,
                                consolidation="max"):
  print(yellow("Building RFUZZ coverage dataframe ..."))
  # Create empty dictionary that will be used to create a Pandas DataFrame that
  # looks like the following:
  # +-----------------------------------------------------------+
  # |toplevel|seed cycles|fuzzer|coverage type|time|coverage (%)|
  # +-----------------------------------------------------------+
  # |  ...   |    ...    | ...  |    ...      | ...|    ...      |
  coverage_dict = {
      TOPLEVEL_LABEL: [],
      SEED_CYCLES_LABEL: [],
      FUZZER_LABEL: [],
      COVERAGE_TYPE_LABEL: [],
      TIME_LABEL: [],
      COVERAGE_LABEL: [],
  }
  cov_dict = {}
  # maps {toplevel --> {seed_cycles --> [coverage list]}}
  for exp_name, fd_list in exp2data.items():
    # get max coverage experiment
    max_cov = get_max_vlt_cov(fd_list[0].rfuzz_cov_data)
    max_cov_fd = fd_list[0]
    for fd in fd_list:
      cov = get_max_vlt_cov(fd.rfuzz_cov_data)
      if fd.toplevel not in cov_dict:
        cov_dict[fd.toplevel] = {}
      if fd.seed_cycles not in cov_dict[fd.toplevel]:
        cov_dict[fd.toplevel][fd.seed_cycles] = []
      cov_dict[fd.toplevel][fd.seed_cycles].append(cov)
      if cov > max_cov:
        max_cov = cov
        max_cov_fd = fd
    for test_id, row in max_cov_fd.rfuzz_data.iterrows():
      # scale time
      scaled_time = scale_time(row["Time (s)"], time_units)
      # add circuit, fuzzer, and time values to dataframe row
      coverage_dict[TOPLEVEL_LABEL].append(max_cov_fd.toplevel)
      coverage_dict[SEED_CYCLES_LABEL].append(max_cov_fd.seed_cycles)
      coverage_dict[TIME_LABEL].append(scaled_time)
      # compute average coverage at all points in time
      rfuzz_vlt_cov = get_vlt_cov_at_time(test_id, max_cov_fd.rfuzz_cov_data)
      # save time 0 coverage to normalize if requested
      if test_id == 0:
        rfuzz_vlt_cov_t0 = rfuzz_vlt_cov
      if normalize_to_start:
        rfuzz_vlt_cov /= rfuzz_vlt_cov_t0
      # add coverage to dataframe row
      coverage_dict[FUZZER_LABEL].append("RFUZZ")
      coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(rfuzz_vlt_cov)
    # extend lines to max time value
    if coverage_dict[TIME_LABEL][-1] != SCALED_MAX_PLOT_TIME:
      coverage_dict[TOPLEVEL_LABEL].append(max_cov_fd.toplevel)
      coverage_dict[SEED_CYCLES_LABEL].append(max_cov_fd.seed_cycles)
      coverage_dict[TIME_LABEL].append(SCALED_MAX_PLOT_TIME)
      coverage_dict[FUZZER_LABEL].append("RFUZZ")
      coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(coverage_dict[COVERAGE_LABEL][-1])
    print("Max HW Line coverage (%15s): %.3f%%" %
          (max_cov_fd.toplevel, coverage_dict[COVERAGE_LABEL][-1]))
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(coverage_dict), cov_dict


def build_min_hwf_coverage_df(exp2data,
                              time_units="m",
                              normalize_to_start=False,
                              consolidation="max"):
  print(yellow("Building HWF coverage dataframe ..."))
  # Create empty dictionary that will be used to create a Pandas DataFrame that
  # looks like the following:
  # +-----------------------------------------------------------+
  # |toplevel|seed cycles|fuzzer|coverage type|time|coverage (%)|
  # +-----------------------------------------------------------+
  # |  ...   |    ...    | ...  |    ...      | ...|    ...      |
  coverage_dict = {
      TOPLEVEL_LABEL: [],
      SEED_CYCLES_LABEL: [],
      FUZZER_LABEL: [],
      COVERAGE_TYPE_LABEL: [],
      TIME_LABEL: [],
      COVERAGE_LABEL: [],
  }
  cov_dict = {}  # maps {toplevel --> {seed_cycles --> [coverage list]}}
  for exp_name, fd_list in exp2data.items():
    # get min coverage experiment
    min_cov = get_max_vlt_cov(fd_list[0].hwf_cov_data)
    min_cov_fd = fd_list[0]
    for fd in fd_list:
      cov = get_max_vlt_cov(fd.hwf_cov_data)
      if fd.toplevel not in cov_dict:
        cov_dict[fd.toplevel] = {}
      if fd.seed_cycles not in cov_dict[fd.toplevel]:
        cov_dict[fd.toplevel][fd.seed_cycles] = []
      cov_dict[fd.toplevel][fd.seed_cycles].append(cov)
      if cov < min_cov:
        min_cov = cov
        min_cov_fd = fd
    # build data frame for plotting
    for time, row in min_cov_fd.hwf_afl_data.iterrows():
      # scale time
      scaled_time = scale_time(time, time_units)
      # add circuit, fuzzer, and time values to dataframe row
      coverage_dict[TOPLEVEL_LABEL].append(min_cov_fd.toplevel)
      coverage_dict[SEED_CYCLES_LABEL].append(min_cov_fd.seed_cycles)
      coverage_dict[TIME_LABEL].append(scaled_time)
      # get the AFL paths_total at the current time
      paths_total = get_paths_total_at_time(time, min_cov_fd.hwf_afl_data) - 1
      # get HWF coverage data
      hwf_vlt_cov = get_vlt_cov_at_time(paths_total, min_cov_fd.hwf_cov_data)
      # normalize to start time if requested
      if time == 0:
        hwf_vlt_cov_t0 = hwf_vlt_cov
      if normalize_to_start:
        hwf_vlt_cov /= hwf_vlt_cov_t0
      # add to data frame
      coverage_dict[FUZZER_LABEL].append("HWF")
      coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(hwf_vlt_cov)
    # extend lines to max time value
    if coverage_dict[TIME_LABEL][-1] != SCALED_MAX_PLOT_TIME:
      coverage_dict[TOPLEVEL_LABEL].append(min_cov_fd.toplevel)
      coverage_dict[SEED_CYCLES_LABEL].append(min_cov_fd.seed_cycles)
      coverage_dict[TIME_LABEL].append(SCALED_MAX_PLOT_TIME)
      coverage_dict[FUZZER_LABEL].append("HWF")
      coverage_dict[COVERAGE_TYPE_LABEL].append(HW_LINE_COVERAGE_LABEL)
      coverage_dict[COVERAGE_LABEL].append(coverage_dict[COVERAGE_LABEL][-1])
    print("Min. HW Line coverage (%15s): %.3f%%" %
          (min_cov_fd.toplevel, coverage_dict[COVERAGE_LABEL][-1]))
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(coverage_dict), cov_dict


def plot_avg_coverage_vs_time(hwf_cov_df, rfuzz_cov_df, time_units="m"):
  print(yellow("Generating plot ..."))

  sns.set_theme(context="notebook", style="darkgrid")
  hdl_cov_df = pd.concat([hwf_cov_df, rfuzz_cov_df])

  grid = sns.FacetGrid(hdl_cov_df,
                       row=SEED_CYCLES_LABEL,
                       height=3,
                       aspect=1.5,
                       legend_out=True)
  grid.map_dataframe(sns.lineplot,
                     x=TIME_LABEL,
                     y=COVERAGE_LABEL,
                     hue=TOPLEVEL_LABEL,
                     style=FUZZER_LABEL)

  # format the plot
  grid.add_legend()
  if time_units == "m":
    time_units_label = "min."
    upper_xlim = max(DURATION_MINS / 60, 1500)
  elif time_units == "h":
    time_units_label = "hours"
    upper_xlim = max(DURATION_MINS / 60, 25)
  else:
    time_units_label = "s"
    upper_xlim = (DURATION_MINS * 60, 90000)
  grid.set_axis_labels(f"{TIME_LABEL} ({time_units_label})",
                       f"{COVERAGE_LABEL}")
  grid.set(xlim=(-1, upper_xlim), ylim=(30, 100))
  plt.subplots_adjust(bottom=0.08)

  # save the plot
  plt.savefig(PLOT_FILE_NAME, format=PLOT_FORMAT)
  print(green("Done."))
  print(LINE_SEP)


def compute_stats(hwf_cov_dict, rfuzz_cov_dict):
  print(yellow("Computing stats ..."))
  # Compute HDL coverage % differences
  cov_diffs_sum = 0
  num_exps = 0
  max_diff_percent = 0
  min_diff_percent = 100
  for toplevel, seed_cycles_dict in hwf_cov_dict.items():
    for seed_cycles, hwf_cov in seed_cycles_dict.items():
      min_hwf_cov = min(hwf_cov)
      max_rfuzz_cov = max(rfuzz_cov_dict[toplevel][seed_cycles])
      cov_diff = min_hwf_cov - max_rfuzz_cov
      min_diff_percent = min(min_diff_percent, cov_diff)
      max_diff_percent = max(max_diff_percent, cov_diff)
      cov_diffs_sum += cov_diff
      num_exps += 1
      print("HWF vs. RFUZZ coverage (%15s -- %d seed cycles): %.3f%%" %
            (toplevel, seed_cycles, cov_diff))
  cov_diffs_avg = float(cov_diffs_sum) / float(num_exps)
  print("Avg. coverage difference: %.3f%%" % (cov_diffs_avg))
  print("Min. coverage difference: %.3f%%" % (min_diff_percent))
  print("Max. coverage difference: %.3f%%" % (max_diff_percent))
  print('-' * len(LINE_SEP))
  for toplevel, seed_cycles_dict in hwf_cov_dict.items():
    for seed_cycles, hwf_cov in seed_cycles_dict.items():
      rfuzz_cov = rfuzz_cov_dict[toplevel][seed_cycles]
      myu = stats.mannwhitneyu(hwf_cov, rfuzz_cov)
      # print("HWF vs. RFUZZ Mann-Whitney (%15s -- %d seed cycles): %s" %
      # (toplevel, seed_cycles, myu))
  print(green("Done."))
  print(LINE_SEP)


def main(argv):
  parser = argparse.ArgumentParser(
      description="Plotting script RFUZZ vs HWF experiments.")
  parser.add_argument("hwf_exp_prefix")
  parser.add_argument("rfuzz_exp_prefix")
  args = parser.parse_args()

  # Load runtime data
  exp2data = load_fuzzing_data(args.hwf_exp_prefix, args.rfuzz_exp_prefix)
  hwf_cov_df, hwf_cov_dict = build_min_hwf_coverage_df(
      exp2data, time_units=TIME_SCALE, normalize_to_start=False)
  rfuzz_cov_df, rfuzz_cov_dict = build_max_rfuzz_coverage_df(
      exp2data, time_units=TIME_SCALE, normalize_to_start=False)

  # Compute Stats
  compute_stats(hwf_cov_dict, rfuzz_cov_dict)

  # Plot data
  plot_avg_coverage_vs_time(hwf_cov_df, rfuzz_cov_df, time_units=TIME_SCALE)


if __name__ == "__main__":
  main(sys.argv[1:])

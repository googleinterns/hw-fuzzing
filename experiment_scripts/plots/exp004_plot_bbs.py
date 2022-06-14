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
import itertools
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

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

# ------------------------------------------------------------------------------
# Plot parameters
# ------------------------------------------------------------------------------
MARKER_SIZE = 5

# ------------------------------------------------------------------------------
# Plot Labels
# ------------------------------------------------------------------------------
NUM_BB_LABEL = "# basic blocks"
NUM_STATES_LABEL = "# states"
WIDTH_LABEL = "width"
INSTR_TYPE_LABEL = "Simulation Binary Components"
OPT_TYPE_LABEL = "Fork Server Init."
INSTR_TYPE_MAPPINGS = {
    "full": "All",
    "duttb": "DUT & TB",
    "dut": "DUT only",
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
STATES = [8, 16, 32, 64]
# STATES = [16, 32, 64, 128]
WIDTHS = [4]
TRIALS = range(1)

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
    self.bb_data = self._load_bb_data()

  def _load_csv_data(self, csv_file):
    return pd.read_csv(csv_file,
                       delimiter=',',
                       index_col=None,
                       engine='python')

  def _load_bb_data(self):
    bb_csv_file = os.path.join(self.data_path, "logs/bb_complexity.csv")
    if not os.path.exists(bb_csv_file):
      print(red("ERROR: BB CSV file (%s) not found." % bb_csv_file))
      sys.exit(1)
    # Load data into Pandas DataFrame
    df = self._load_csv_data(bb_csv_file)
    # Remove leading/trailing white space from column names
    df = df.rename(columns=lambda x: x.strip())
    return df

  @property
  def dut_bbs(self):
    return int(self.bb_data[self.bb_data["Design-Portion"] == "DUT"]["#-BBs"])

  @property
  def tb_bbs(self):
    return int(self.bb_data[self.bb_data["Design-Portion"] == "TB"]["#-BBs"])

  @property
  def vltrt_bbs(self):
    return int(
        self.bb_data[self.bb_data["Design-Portion"] == "VLTRT"]["#-BBs"])

  @property
  def full_bbs(self):
    return int(self.bb_data[self.bb_data["Design-Portion"] == "ALL"]["#-BBs"])

  @property
  def duttb_bbs(self):
    return (self.dut_bbs + self.tb_bbs)


def build_bbs_df(exp2data):
  print(yellow("Building basic block stats dataframe ..."))
  # Create empty dictionary that will be used to create Pandas
  # a DataFrame that look like the following:
  # +---------------------------------------------------+
  # | # states | instrumentation level | # basic blocks |
  # +---------------------------------------------------+
  # |   ...    |          ...          |       ...      |
  bbs_dict = {
      NUM_STATES_LABEL: [],
      INSTR_TYPE_LABEL: [],
      NUM_BB_LABEL: [],
  }
  for exp_name, fd in exp2data.items():
    bbs_dict[NUM_STATES_LABEL].extend([fd.num_states] * 2)
    # bbs_dict[INSTR_TYPE_LABEL].extend(["Simulation Engine", "TB", "DUT"])
    bbs_dict[INSTR_TYPE_LABEL].extend(["Simulation Engine + TB", "DUT"])
    # bbs_dict[NUM_BB_LABEL].append(fd.vltrt_bbs)
    # bbs_dict[NUM_BB_LABEL].append(fd.tb_bbs)
    bbs_dict[NUM_BB_LABEL].append(fd.vltrt_bbs + fd.tb_bbs)
    bbs_dict[NUM_BB_LABEL].append(fd.dut_bbs)
    # bbs_dict[NUM_STATES_LABEL].append(fd.num_states)
    # bbs_dict[INSTR_TYPE_LABEL].append(INSTR_TYPE_MAPPINGS[fd.instr_type])
    # if fd.instr_type == "full":
    # bbs_dict[NUM_BB_LABEL].append(fd.full_bbs)
    # elif fd.instr_type == "duttb":
    # bbs_dict[NUM_BB_LABEL].append(fd.duttb_bbs)
    # elif fd.instr_type == "dut":
    # bbs_dict[NUM_BB_LABEL].append(fd.dut_bbs)
    # else:
    # print(red("ERROR: unknown instrumentation type."))
    # sys.exit(1)
  print(green("Done."))
  print(LINE_SEP)
  return pd.DataFrame.from_dict(bbs_dict)


def load_bb_data(data_root):
  print(yellow("Loading data ..."))
  exp2data = {}

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
      exp2data[exp_name_wo_trialnum] = FuzzingData(num_states, width,
                                                   instr_type, fs_opt, trial,
                                                   data_path)
  print(green("Done."))
  print(LINE_SEP)
  return exp2data


def plot_bbs(instr_bbs, orientation="h"):
  print(yellow("Generating plots ..."))
  LABEL_FONT_SIZE = 14
  sns.set()
  if orientation == "h":
    ax = sns.barplot(y=NUM_STATES_LABEL,
                     x=NUM_BB_LABEL,
                     hue=INSTR_TYPE_LABEL,
                     data=instr_bbs,
                     orient="h",
                     ci=None)
    ax.set_ylabel(NUM_STATES_LABEL, fontsize=LABEL_FONT_SIZE)
    ax.set_xlabel(NUM_BB_LABEL, fontsize=LABEL_FONT_SIZE)
    ax.tick_params("y", labelsize=LABEL_FONT_SIZE)
    ax.tick_params("x", labelsize=LABEL_FONT_SIZE)
    ax.set_xlim(10, 10000)
    plt.xscale("log")
  else:
    ax = sns.barplot(x=NUM_STATES_LABEL,
                     y=NUM_BB_LABEL,
                     hue=INSTR_TYPE_LABEL,
                     data=instr_bbs,
                     ci=None)
    ax.set_xlabel(NUM_STATES_LABEL, fontsize=LABEL_FONT_SIZE)
    ax.set_ylabel(NUM_BB_LABEL, fontsize=LABEL_FONT_SIZE)
    ax.tick_params("x", labelsize=LABEL_FONT_SIZE)
    ax.tick_params("y", labelsize=LABEL_FONT_SIZE)
    ax.set_ylim(10, 10000)
    plt.yscale("log")
  plt.legend(title=INSTR_TYPE_LABEL,
             fontsize=LABEL_FONT_SIZE,
             title_fontsize=LABEL_FONT_SIZE,
             ncol=3,
             loc="upper center",
             bbox_to_anchor=(0.5, 1.25))
  plt.tight_layout()
  plt.savefig("hwf_components_bbs.png", format="PNG")
  print(green("Done."))
  print(LINE_SEP)


def main(argv):
  parser = argparse.ArgumentParser(description="Plotting script for exp. 004.")
  parser.add_argument("data_root")
  args = parser.parse_args()

  # Load runtime data
  exp2data = load_bb_data(args.data_root)
  instr_bbs = build_bbs_df(exp2data)

  # Plot the data
  plot_bbs(instr_bbs)


if __name__ == "__main__":
  main(sys.argv[1:])

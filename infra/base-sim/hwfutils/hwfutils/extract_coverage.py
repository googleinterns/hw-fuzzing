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

import argparse
import csv
import glob
import json
import os
import sys

from hwfutils.string_color import color_str_red as red

TIME_LABEL = "Time (s)"
DESIGN_PORTION_LABEL = "Design Portion"
SW_LINE_COVERAGE_LABEL = "Line Coverage (%)"


class KcovFileStats:
  def __init__(self, stats_dict):
    self.filename = stats_dict["file"]
    self.percent_covered = float(stats_dict["percent_covered"])
    self.covered_lines = int(stats_dict["covered_lines"])
    self.total_lines = int(stats_dict["total_lines"])


class Coverage:
  def __init__(self, args):
    self.coverage_dict = {
        TIME_LABEL: [],
        DESIGN_PORTION_LABEL: [],
        SW_LINE_COVERAGE_LABEL: [],
    }
    self._extract_cumulative_kcov_data(args)

  def dump_to_csv(self, csv_file_name):
    """Dump coverage dictionary to a CSV file for future analysis."""
    # Check that all columns of dict are the same length
    num_rows = len(self.coverage_dict[TIME_LABEL])
    for value in self.coverage_dict.values():
      if num_rows != len(value):
        print(red("ERROR: table dimension mismatch. Aborting!"))
        # Fail silently, we don't want to throw away fuzzing results for a
        # post-processing error.
        sys.exit(1)

    with open(csv_file_name, "w", newline="") as csv_file:
      csv_writer = csv.writer(csv_file)
      # Write CSV column headers
      col_headers = [TIME_LABEL, DESIGN_PORTION_LABEL, SW_LINE_COVERAGE_LABEL]
      csv_writer.writerow(col_headers)
      for row_index in range(num_rows):
        # craft row list
        row_list = []
        for col in col_headers:
          row_list.append(self.coverage_dict[col][row_index])
        # write row list to file
        csv_writer.writerow(row_list)

    return

  def _extract_kcov_data_from_json(self, cov_data_file):
    cov_data_dict = {}
    with open(cov_data_file, "r") as jf:
      cov_data = json.load(jf)
      for stats_dict in cov_data["files"]:
        cov_data_dict[stats_dict["file"]] = KcovFileStats(stats_dict)
    return cov_data_dict

  def _extract_cumulative_kcov_data(self, args):
    print("Extracting kcov data into CSV format ...")
    sorted_cov_data = []
    # This is a hack, but essentially we need to sort the coverage data files
    # in ascending numerical order, as this corresponds to the temporal order
    # in which each AFL test case was generated.
    sorted_cov_data_files = sorted(
        glob.glob(os.path.join(args.kcov_dir, "*.json")),
        key=lambda x: int(x.rstrip(".json").split("_")[-1]))
    for cov_data_file in sorted_cov_data_files:
      print("    Extracting coverage data from: %s" % cov_data_file)

      # Extract per file stats for the current coverage trace
      cov_data_dict = self._extract_kcov_data_from_json(cov_data_file)

      # Sort and aggregrate per-file coverage stats
      curr_test_filenames = {
          "DUT": [],
          "TB": [],
          "VLTRT": [],
          "Other": [],
      }
      curr_test_cov = {
          "DUT": [0, 0],
          "TB": [0, 0],
          "VLTRT": [0, 0],
          "Other": [0, 0],
      }
      LINES_COVERED = 0
      TOTAL_LINES = 1
      for filename, kcov_stats in cov_data_dict.items():
        if filename.startswith("/src/hw/%s/model" % args.toplevel):
          curr_test_filenames["DUT"].append(filename)
          curr_test_cov["DUT"][LINES_COVERED] += kcov_stats.covered_lines
          curr_test_cov["DUT"][TOTAL_LINES] += kcov_stats.total_lines
        elif (filename.startswith("/src/hw/tb") or
              filename.startswith("/src/hw/%s/tb" % args.toplevel)):
          curr_test_filenames["TB"].append(filename)
          curr_test_cov["TB"][LINES_COVERED] += kcov_stats.covered_lines
          curr_test_cov["TB"][TOTAL_LINES] += kcov_stats.total_lines
        elif filename.startswith("/src/verilator"):
          curr_test_filenames["VLTRT"].append(filename)
          curr_test_cov["VLTRT"][LINES_COVERED] += kcov_stats.covered_lines
          curr_test_cov["VLTRT"][TOTAL_LINES] += kcov_stats.total_lines
        else:
          curr_test_filenames["Other"].append(filename)
          curr_test_cov["Other"][LINES_COVERED] += kcov_stats.covered_lines
          curr_test_cov["Other"][TOTAL_LINES] += kcov_stats.total_lines

      # Save coverage data to temporally ordered list
      sorted_cov_data.append(curr_test_cov)

    # The AFL plot data file is a CSV file
    print("Computing line coverage percentages over time ...")
    with open(glob.glob(args.afl_plot_data)[0], newline="") as csvfile:
      csv_reader = csv.reader(csvfile)
      row_num = 0
      for row in csv_reader:
        if row_num > 0:
          # Extract timestamp and number of test cases processed at that time
          unix_time = int(row[0])
          paths_total = int(row[3])
          index = paths_total - 1

          # Adjust time to be zero indexed
          if row_num == 1:
            start_time = unix_time
          unix_time -= start_time

          # Compute line coverage percentage and add data to dict
          for portion in ["DUT", "TB", "VLTRT", "Other"]:
            lines_covered = sorted_cov_data[index][portion][LINES_COVERED]
            total_lines = sorted_cov_data[index][portion][TOTAL_LINES]
            line_coverage = float(lines_covered) / float(total_lines)
            self.coverage_dict[TIME_LABEL].append(unix_time)
            self.coverage_dict[DESIGN_PORTION_LABEL].append(portion)
            self.coverage_dict[SW_LINE_COVERAGE_LABEL].append(line_coverage)
        row_num += 1
    print("Done.")


def _main(argv):
  module_description = "HW Fuzzing Coverage Extraction"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("toplevel")
  parser.add_argument("afl_plot_data")
  parser.add_argument("kcov_dir")
  parser.add_argument("output_file_name")
  args = parser.parse_args(argv)

  # Load cumulative coverage data and sort/match data by design component and
  # time it was achieved during fuzzing execution.
  cov = Coverage(args)

  # Export coverage data to a plotting friendly CSV file.
  cov.dump_to_csv(args.output_file_name)


if __name__ == "__main__":
  _main(sys.argv[1:])

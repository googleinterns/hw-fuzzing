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

import abc
import csv
import glob
import os
import sys

from hwfutils.string_color import color_str_red as red


class Coverage:
  __metaclass__ = abc.ABCMeta

  TEST_ID = "Test-ID"
  LINES_COVERED = "Lines-Covered"
  LINES_TOTAL = "Total-Lines"
  LINE_COVERAGE = "Line-Coverage-(%)"

  def __init__(self, toplevel, data_dir, glob_str, file_ext):
    self.toplevel = toplevel
    self.data_dir = data_dir
    self.glob_str = glob_str
    self.file_ext = file_ext
    self.coverage_dict = {
        Coverage.TEST_ID: [],
        Coverage.LINES_COVERED: [],
        Coverage.LINES_TOTAL: [],
        Coverage.LINE_COVERAGE: [],
    }

  def dump_to_csv(self, csv_file_name):
    """Dump coverage dictionary to a CSV file for future analysis."""
    # Check that all columns of dict are the same length
    col_headers = list(self.coverage_dict.keys())
    num_rows = len(self.coverage_dict[col_headers[0]])
    for col_header in col_headers:
      if num_rows != len(self.coverage_dict[col_header]):
        print(red("ERROR: table dimension mismatch. Aborting!"))
        # Fail silently, we don't want to throw away fuzzing results for a
        # post-processing error.
        sys.exit()

    with open(csv_file_name, "w", newline="") as csv_file:
      csv_writer = csv.writer(csv_file)
      # Write CSV column headers
      col_headers = self.coverage_dict.keys()
      csv_writer.writerow(col_headers)
      for row_index in range(num_rows):
        # craft row list
        row_list = []
        for col in col_headers:
          row_list.append(self.coverage_dict[col][row_index])
        # write row list to file
        csv_writer.writerow(row_list)

  def extract_all_cov_traces(self):
    print("Aggregating coverage traces into CSV file ...")
    sorted_cov_traces = self._sort_cov_traces()
    for trace in sorted_cov_traces:
      print("\tExtracting coverage trace from: %s" % trace)
      # Extract per file stats for the current coverage trace
      self._extract_single_cov_trace(trace)
    print("Done.")

  def _sort_cov_traces(self):
    # This is a hack, but essentially we need to sort the coverage trace files
    # in ascending numerical order, as this corresponds to the temporal order
    # in which each AFL test case was generated.
    # TODO(ttrippel): make fuzzer agnostic
    sorted_cov_trace_files = sorted(
        glob.glob(os.path.join(self.data_dir, self.glob_str + self.file_ext)),
        key=lambda x: int(x.rstrip(self.file_ext).split("_")[-1]))
    return sorted_cov_trace_files

  @abc.abstractmethod
  def _extract_single_cov_trace(self, cov_trace_file):
    pass

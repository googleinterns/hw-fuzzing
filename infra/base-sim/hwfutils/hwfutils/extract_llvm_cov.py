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
import re
import sys

from hwfutils.coverage import Coverage


class LLVMCov(Coverage):
  REGIONS_COVERED = "Regions-Covered"
  REGIONS_TOTAL = "Regions-Total"
  REGION_COVERAGE = "Region-Coverage-(%)"

  def __init__(self, toplevel, data_dir, glob_str, file_ext):
    super().__init__(toplevel, data_dir, glob_str, file_ext)
    self.coverage_dict[LLVMCov.REGIONS_COVERED] = []
    self.coverage_dict[LLVMCov.REGIONS_TOTAL] = []
    self.coverage_dict[LLVMCov.REGION_COVERAGE] = []
    self._ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    self.extract_all_cov_traces()

  def _extract_single_cov_trace(self, cov_trace_file):
    test_id = int(cov_trace_file.rstrip(".report.txt").split("_")[-1])
    test_id_str = "id:{:06d}".format(test_id)
    self.coverage_dict[Coverage.TEST_ID].append(test_id_str)
    self.coverage_dict[LLVMCov.REGIONS_COVERED].append(0)
    self.coverage_dict[LLVMCov.REGIONS_TOTAL].append(0)
    self.coverage_dict[Coverage.LINES_COVERED].append(0)
    self.coverage_dict[Coverage.LINES_TOTAL].append(0)

    # open file and iterate over lines
    with open(cov_trace_file, "r") as fp:
      line_num = 0
      for line in fp:
        line_num += 1

        # clean up the line string
        line = self._ansi_escape.sub('', line)
        line_list = line.rstrip().split()

        # check if we are at the beginning lines that we can skip
        if line_num < 3:
          continue

        # check if we are done parsing
        if len(line_list) < 2:
          # compute coverage percentages
          self.coverage_dict[LLVMCov.REGION_COVERAGE].append(
              float(self.coverage_dict[LLVMCov.REGIONS_COVERED][-1]) /
              float(self.coverage_dict[LLVMCov.REGIONS_TOTAL][-1]))
          self.coverage_dict[Coverage.LINE_COVERAGE].append(
              float(self.coverage_dict[Coverage.LINES_COVERED][-1]) /
              float(self.coverage_dict[Coverage.LINES_TOTAL][-1]))
          break

        # extract stats from each line
        filename = line_list[0]
        if filename.startswith("hw/%s/model" % self.toplevel):
          # parse region coverage
          regions_total = int(line_list[1])
          regions_missed = int(line_list[2])
          self.coverage_dict[LLVMCov.REGIONS_TOTAL][-1] += regions_total
          self.coverage_dict[LLVMCov.REGIONS_COVERED][-1] += regions_total
          self.coverage_dict[LLVMCov.REGIONS_COVERED][-1] -= regions_missed
          # parse line coverage
          lines_total = int(line_list[7])
          lines_missed = int(line_list[8])
          self.coverage_dict[Coverage.LINES_TOTAL][-1] += lines_total
          self.coverage_dict[Coverage.LINES_COVERED][-1] += lines_total
          self.coverage_dict[Coverage.LINES_COVERED][-1] -= lines_missed


def main(argv):
  module_description = "HW Fuzzing LLVM Coverage Extraction"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("toplevel")
  parser.add_argument("llvm_cov_dir")
  args = parser.parse_args(argv)

  # Load coverage data
  cov = LLVMCov(args.toplevel, args.llvm_cov_dir, "cov_*", ".report.txt")
  cum_cov = LLVMCov(args.toplevel, args.llvm_cov_dir, "cum_cov_*",
                    ".report.txt")

  # Export coverage data to a plotting friendly CSV file.
  cov.dump_to_csv("logs/llvm_cov.csv")
  cum_cov.dump_to_csv("logs/llvm_cov_cum.csv")


if __name__ == "__main__":
  main(sys.argv[1:])

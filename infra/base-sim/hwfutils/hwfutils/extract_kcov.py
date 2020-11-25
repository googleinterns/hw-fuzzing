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
import json
import sys

from hwfutils.coverage import Coverage


class KCov(Coverage):
  def __init__(self, toplevel, data_dir, glob_str, file_ext):
    super().__init__(toplevel, data_dir, glob_str, file_ext)
    self.extract_all_cov_traces()

  def _extract_single_cov_trace(self, cov_trace_file):
    # extract test id str and prep data dictionary
    test_id = int(cov_trace_file.rstrip(".json").split("_")[-1])
    test_id_str = "id:{:06d}".format(test_id)
    self.coverage_dict[Coverage.TEST_ID].append(test_id_str)
    self.coverage_dict[Coverage.LINES_COVERED].append(0)
    self.coverage_dict[Coverage.LINES_TOTAL].append(0)

    # open json file and extract coverage data for the DUT only
    with open(cov_trace_file, "r") as jf:
      cov_data = json.load(jf)
      for cov_dict in cov_data['files']:
        filename = cov_dict['file']
        if ("hw/%s/model" % self.toplevel) in filename:
          lines_covered = int(cov_dict['covered_lines'])
          lines_total = int(cov_dict['total_lines'])
          self.coverage_dict[Coverage.LINES_COVERED][-1] += lines_covered
          self.coverage_dict[Coverage.LINES_TOTAL][-1] += lines_total

    # compute line coverage percentage
    self.coverage_dict[Coverage.LINE_COVERAGE].append(
        float(self.coverage_dict[Coverage.LINES_COVERED][-1]) /
        float(self.coverage_dict[Coverage.LINES_TOTAL][-1]))


def main(argv):
  module_description = "HW Fuzzing LLVM Coverage Extraction"
  parser = argparse.ArgumentParser(description=module_description)
  parser.add_argument("--output-dir", default="logs")
  parser.add_argument("toplevel")
  parser.add_argument("kcov_dir")
  args = parser.parse_args(argv)

  # Load coverage data
  cov = KCov(args.toplevel, args.kcov_dir, "kcov_[0-9]*", ".json")
  cum_cov = KCov(args.toplevel, args.kcov_dir, "kcov_cum*", ".json")

  # Export coverage data to a plotting friendly CSV file.
  cov.dump_to_csv("%s/kcov.csv" % args.output_dir)
  cum_cov.dump_to_csv("%s/kcov_cum.csv" % args.output_dir)


if __name__ == "__main__":
  main(sys.argv[1:])

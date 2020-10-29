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

import sys

SVA_MACROS = [
    "ASSERT",
    "ASSERT_NEVER",
    "ASSERT_PULSE",
    "ASSERT_IF",
    # below probably won't help for fuzzing
    "ASSERT_KNOWN",
    "ASSERT_KNOWN_IF",
]

LINE_SEP = "-------------------------------------------------------------------"


def _write_sva_locations_to_csv(sva_locations, csv_file_name):
  with open(csv_file_name, "w") as csv_file:
    csv_file.write("Filename, Line-#, Line\n")
    for i in range(len(sva_locations["Filename"])):
      hdl_file_name = sva_locations["Filename"][i]
      line_num = sva_locations["Line-#"][i]
      line = sva_locations["Line"][i]
      csv_file.write("%s, %d, %s\n" % (hdl_file_name, line_num, line))


def _main(args):

  num_svas = {macro: 0 for macro in SVA_MACROS}
  sva_locations = {
      "Filename": [],
      "Line-#": [],
      "Line": [],
  }

  for hdl_file_name in args:
    if "prim_assert" not in hdl_file_name:
      line_num = 0
      with open(hdl_file_name, "r") as hdl_file:
        for line in hdl_file:
          line = line.lstrip().rstrip()
          for sva in SVA_MACROS:
            if "`%s(" % sva in line and not line.startswith(r"//"):
              sva_locations["Filename"].append(hdl_file_name)
              sva_locations["Line-#"].append(line_num)
              sva_locations["Line"].append(line.rstrip().lstrip())
              num_svas[sva] += 1
          line_num += 1

  _write_sva_locations_to_csv(sva_locations, "logs/svas.csv")

  print(LINE_SEP)
  print("# of SVAS embedded in HDL:")
  print(LINE_SEP)
  for sva in SVA_MACROS:
    print("%s: %d" % (sva, num_svas[sva]))
  print(LINE_SEP)


if __name__ == "__main__":
  _main(sys.argv[1:])

#!/usr/bin/python3
# Copyright 2020 Google LLC
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

def write_target(src_file, line_num, targets_f):
    targets_f.write("%s:%d\n" % (src_file, line_num))

def main(args):
    print("Defining AFLGo BB targets...")
    bb_targets_filename = args[0]
    with open(bb_targets_filename, "w") as targets_f:
        write_target("Vaes_128.cpp", 250, targets_f)
    print("Done!")

if __name__ == "__main__":
    main(sys.argv[1:])

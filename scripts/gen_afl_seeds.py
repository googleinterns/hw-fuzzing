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
import os

sys.path.append(os.getcwd())
from gen_random_test import gen_random_test

def gen_afl_seeds(test_file_basename, num_seeds, num_tests_per_seed):
    for seed_num in range(num_seeds):

        # Set test file name
        test_file_name_ext = "." + str(seed_num) + ".tf"
        test_file_name = test_file_basename + test_file_name_ext

        # Open Test File
        test_file = open(test_file_name, "w")

        # Write Tests
        for _ in range(num_tests_per_seed):
            test_file.write("%s\n" % gen_random_test())

        # Close Test File
        test_file.close()

if __name__ == '__main__':
    gen_afl_seeds(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))

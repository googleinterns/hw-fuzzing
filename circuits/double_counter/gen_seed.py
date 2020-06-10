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
import random
import string

SELECT_SIZE = 1

def generateRandomInput(select_size):
    select = ""
    for _ in range(select_size):
        select += random.choice(string.ascii_letters)

    return select

def genRandomTests(test_file_name='double_counter.tf', num_tests=1000):

    # Open Test File
    test_file = open(test_file_name, "w")

    # Write Tests
    for _ in range(num_tests):
        test_file.write("%s\n" % generateRandomInput(SELECT_SIZE))

    # Close Test File
    test_file.close()

if __name__ == '__main__':
    genRandomTests(test_file_name=sys.argv[1], num_tests=int(sys.argv[2]))

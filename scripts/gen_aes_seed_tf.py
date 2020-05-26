#! /usr/bin/python3
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

KEY_SIZE = 16
STATE_SIZE = 16

def generateRandomInput(key_size, state_size):
    key = ""
    state = ""
    for _ in range(key_size):
        key += random.choice(string.ascii_letters)
    for _ in range(state_size):
        state += random.choice(string.ascii_letters)

    return key + " " + state

def genRandomTests(test_file_name='aes.tf', num_tests=5):

    # Open Test File
    test_file = open(test_file_name, "w")

    # Write Tests
    for _ in range(num_tests):
        test_file.write("%s\n" % \
                generateRandomInput(KEY_SIZE, STATE_SIZE))

    # Close Test File
    test_file.close()

if __name__ == '__main__':
    genRandomTests(test_file_name=sys.argv[1], num_tests=int(sys.argv[2]))

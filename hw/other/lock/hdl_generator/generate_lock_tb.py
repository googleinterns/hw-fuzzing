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

import math
import os
import sys


def _main(args):
  code_msb = int(os.getenv("LOCK_COMP_WIDTH")) - 1
  state_msb = math.ceil(math.log2(int(os.getenv("NUM_LOCK_STATES")))) - 1

  vars = {"code_msb": code_msb, "state_msb": state_msb}

  with open(args[0]) as f:
    data = f.read()
    print(data % vars)


if __name__ == "__main__":
  _main(sys.argv[1:])

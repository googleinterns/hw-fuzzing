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
"""Helper module to run shell commands."""

import subprocess
import sys

from hwfutils.string_color import color_str_red as red
from hwfutils.string_color import color_str_yellow as yellow


# Run command as subprocess catching non-zero exit codes
def run_cmd(cmd, error_str, silent=False):
  """Runs the provided command (list of strings) in a separate process."""
  try:
    if not silent:
      print("Running command:")
      print(yellow(subprocess.list2cmdline(cmd)))
      subprocess.check_call(cmd)
    else:
      subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
  except subprocess.CalledProcessError:
    print(red(error_str), file=sys.stderr)
    sys.exit(1)

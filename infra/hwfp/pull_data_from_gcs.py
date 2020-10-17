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

"""This is a helper module to interact with GCS.

Description:
This module implements a method to pull all data from a GCS bucket.
"""

import glob
import os
import subprocess
import sys

from infra.config import color_str_red

# TODO(ttrippel): move this to a CMD line arg
GCS_BUCKET = "fuzzing-data"


def pull_data_from_gcs():
  """Pulls down fuzzer data from GCS to local machine."""
  ls_cmd = ["gsutil", "ls", "gs://%s" % GCS_BUCKET]
  proc = subprocess.Popen(ls_cmd, \
      stdin=subprocess.PIPE, \
      stdout=subprocess.PIPE, \
      stderr=subprocess.STDOUT, \
      close_fds=True)
  while True:
    line = proc.stdout.readline()
    if not line:
      break
    src = line.decode("utf-8").rstrip("/\n")
    dst = os.path.join(os.getenv("HW_FUZZING"), "experiments", "data")
    full_dst = os.path.join(dst, src.lstrip("gs://fuzzing-data"))
    if not data_exists_locally(full_dst):
      cp_cmd = ["gsutil", "cp", "-r", src, dst]
      print("Pulling down fuzzing data from %s ..." % src)
      p = subprocess.Popen(cp_cmd, \
          stdin=subprocess.PIPE, \
          stdout=subprocess.PIPE, \
          stderr=subprocess.STDOUT, \
          close_fds=True)
      if p.returncode:
        print(p.stdout.read())
        line = p.stdout.readline().decode("utf-8")
        while line:
          line = p.stdout.readline()
          print(line)
        print(color_str_red("ERROR: GCS data copy FAILED."))
        sys.exit(1)


def data_exists_locally(exp_data_path):
  """Checks if local experiment data already exists."""
  if glob.glob(exp_data_path):
    return True
  return False


if __name__ == "__main__":
  pull_data_from_gcs()
